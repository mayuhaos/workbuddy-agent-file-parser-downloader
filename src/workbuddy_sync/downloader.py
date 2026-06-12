from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Callable, Iterable
import os
import random
import time

import httpx

from .models import DownloadResult, ExpertEntry


DEFAULT_BUNDLE_BASE_URL = (
    "https://acc-1258344699.cos.accelerate.myqcloud.com/"
    "workbuddy/expert-marketplace/bundles"
)


LogCallback = Callable[[str, ExpertEntry, str, Path, str], None]


@dataclass
class RequestThrottler:
    min_delay: float
    max_delay: float
    _lock: Lock
    _next_allowed_at: float = 0.0

    def wait(self) -> None:
        delay = max(0.0, random.uniform(self.min_delay, self.max_delay))
        with self._lock:
            now = time.monotonic()
            wait_seconds = max(self._next_allowed_at - now, 0.0)
            self._next_allowed_at = max(now, self._next_allowed_at) + delay
        if wait_seconds:
            time.sleep(wait_seconds)


def bundle_url(entry: ExpertEntry, bundle_base_url: str = DEFAULT_BUNDLE_BASE_URL) -> str:
    return f"{bundle_base_url.rstrip('/')}/{entry.plugin}.tar.gz"


def _remote_size(client: httpx.Client, url: str, throttler: RequestThrottler | None = None) -> int | None:
    try:
        if throttler is not None:
            throttler.wait()
        response = client.head(url)
        if response.status_code >= 400:
            return None
        content_length = response.headers.get("content-length")
        return int(content_length) if content_length else None
    except Exception:
        return None


def download_one(
    entry: ExpertEntry,
    out_dir: Path,
    bundle_base_url: str,
    retries: int,
    throttler: RequestThrottler | None = None,
    log_callback: LogCallback | None = None,
    verify_existing: bool = False,
    timeout: float = 90.0,
) -> DownloadResult:
    url = bundle_url(entry, bundle_base_url)
    target = entry.output_path(out_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    attempts = max(retries, 0) + 1

    with httpx.Client(timeout=timeout, follow_redirects=True, verify=False) as client:
        remote_size = _remote_size(client, url, throttler) if verify_existing else None
        if target.exists() and target.stat().st_size > 0 and not verify_existing:
            result = DownloadResult(
                entry=entry,
                url=url,
                path=target,
                status="skipped",
                file_size=target.stat().st_size,
            )
            if log_callback:
                log_callback("skipped", entry, url, target, "")
            return result
        if target.exists() and remote_size is not None and target.stat().st_size == remote_size:
            result = DownloadResult(
                entry=entry,
                url=url,
                path=target,
                status="skipped",
                file_size=target.stat().st_size,
            )
            if log_callback:
                log_callback("skipped", entry, url, target, "")
            return result

        last_error = ""
        for attempt in range(1, attempts + 1):
            tmp_path = target.with_suffix(target.suffix + ".part")
            try:
                if throttler is not None:
                    throttler.wait()
                if log_callback:
                    log_callback("start", entry, url, target, "")
                with client.stream("GET", url) as response:
                    response.raise_for_status()
                    content_length = response.headers.get("content-length")
                    expected_size = int(content_length) if content_length else remote_size
                    with tmp_path.open("wb") as handle:
                        for chunk in response.iter_bytes():
                            if chunk:
                                handle.write(chunk)
                actual_size = tmp_path.stat().st_size
                if expected_size is not None and actual_size != expected_size:
                    raise RuntimeError(f"size mismatch: expected {expected_size}, got {actual_size}")
                os.replace(tmp_path, target)
                result = DownloadResult(
                    entry=entry,
                    url=url,
                    path=target,
                    status="success",
                    file_size=target.stat().st_size,
                    retries=attempt - 1,
                )
                if log_callback:
                    log_callback("success", entry, url, target, "")
                return result
            except Exception as exc:
                last_error = str(exc)
                if tmp_path.exists():
                    tmp_path.unlink(missing_ok=True)
                if log_callback:
                    log_callback("retry" if attempt < attempts else "failed", entry, url, target, last_error)
                if attempt < attempts:
                    time.sleep(min(2**attempt, 8))

    return DownloadResult(
        entry=entry,
        url=url,
        path=target,
        status="failed",
        error=last_error,
        retries=attempts - 1,
    )


def download_many(
    entries: Iterable[ExpertEntry],
    out_dir: Path,
    bundle_base_url: str = DEFAULT_BUNDLE_BASE_URL,
    concurrency: int = 1,
    retries: int = 3,
    delay_min: float = 1.0,
    delay_max: float = 2.0,
    verify_existing: bool = False,
    log_callback: LogCallback | None = None,
    progress: object | None = None,
    task_id: object | None = None,
) -> list[DownloadResult]:
    items = list(entries)
    results: list[DownloadResult] = []
    workers = max(1, concurrency)
    throttler = RequestThrottler(
        min_delay=max(0.0, delay_min),
        max_delay=max(delay_min, delay_max),
        _lock=Lock(),
    )
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                download_one,
                entry,
                out_dir,
                bundle_base_url,
                retries,
                throttler,
                log_callback,
                verify_existing,
            ): entry
            for entry in items
        }
        for future in as_completed(futures):
            results.append(future.result())
            if progress is not None and task_id is not None:
                progress.advance(task_id)
    results.sort(key=lambda item: (item.entry.type_label, item.entry.category_name, item.entry.plugin))
    return results
