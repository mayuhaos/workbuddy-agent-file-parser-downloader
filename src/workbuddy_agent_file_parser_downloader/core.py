from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
from threading import Event
from typing import Callable

from .downloader import DEFAULT_BUNDLE_BASE_URL, download_many
from .excel_report import REPORT_FILENAME, write_report
from .manifest import DEFAULT_MANIFEST_URL, fetch_manifest, parse_experts
from .models import DownloadResult, ExpertEntry


RunEventCallback = Callable[[str, str], None]
TotalCallback = Callable[[int], None]
ProgressCallback = Callable[[int, int], None]


class WorkflowCancelledError(RuntimeError):
    """Raised when the running workflow is cancelled by the user."""


@dataclass(frozen=True)
class RunConfig:
    out_dir: Path | None = None
    manifest_url: str = DEFAULT_MANIFEST_URL
    bundle_base_url: str = DEFAULT_BUNDLE_BASE_URL
    concurrency: int = 1
    retries: int = 3
    delay_min: float = 1.0
    delay_max: float = 2.0
    verify_existing: bool = False
    xlsx_template: Path | None = None
    limit: int | None = None
    sample_agents: int | None = None
    sample_teams: int | None = None
    log_file: Path | None = None


@dataclass(frozen=True)
class RunSummary:
    out_dir: Path
    manifest_path: Path
    report_path: Path
    log_path: Path
    results: list[DownloadResult]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def success(self) -> int:
        return sum(1 for item in self.results if item.success)

    @property
    def failed(self) -> int:
        return self.total - self.success


def default_output_dir(now: datetime | None = None) -> Path:
    current = now or datetime.now()
    return Path(f"agent-outputs-{current:%Y-%m-%d-%H%M%S}")


def setup_logger(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("workbuddy_agent_file_parser_downloader")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


def describe_download_event(event: str, entry: ExpertEntry, url: str, target: Path, error: str = "") -> str:
    parts = [
        f"event={event}",
        f"type={entry.type_label}",
        f"category={entry.category_name}",
        f"plugin={entry.plugin}",
        f"display_zh={entry.display_name_zh}",
        f"display_en={entry.display_name_en or '-'}",
        f"profession_zh={entry.profession_zh or '-'}",
        f"profession_en={entry.profession_en or '-'}",
        f"file={target.name}",
        f"path={target}",
        f"url={url}",
    ]
    if error:
        parts.append(f"error={error}")
    return " | ".join(parts)


def _emit(callback: RunEventCallback | None, event: str, message: str) -> None:
    if callback is None:
        return
    timestamp = datetime.now().isoformat(sep=" ", timespec="milliseconds")
    callback(event, f"{timestamp} {message}")


def _ensure_not_cancelled(cancel_event: Event | None) -> None:
    if cancel_event is not None and cancel_event.is_set():
        raise WorkflowCancelledError("用户已停止本次下载。")


def _apply_entry_limits(
    entries: list[ExpertEntry],
    limit: int | None,
    sample_agents: int | None,
    sample_teams: int | None,
) -> list[ExpertEntry]:
    if sample_agents is not None or sample_teams is not None:
        agent_limit = sample_agents if sample_agents is not None else 0
        team_limit = sample_teams if sample_teams is not None else 0
        entries = [
            *[entry for entry in entries if entry.expert_type == "agent"][: max(agent_limit, 0)],
            *[entry for entry in entries if entry.expert_type == "team"][: max(team_limit, 0)],
        ]
    if limit is not None:
        entries = entries[: max(limit, 0)]
    return entries


def run_workflow(
    config: RunConfig,
    event_callback: RunEventCallback | None = None,
    total_callback: TotalCallback | None = None,
    progress_callback: ProgressCallback | None = None,
    cancel_event: Event | None = None,
) -> RunSummary:
    out_dir = (config.out_dir or default_output_dir()).resolve()
    log_path = (config.log_file or out_dir / "run.log").resolve()
    logger = setup_logger(log_path)
    manifest_path = out_dir / "expert_center.json"

    logger.info("run_start | started_at=%s | out_dir=%s", datetime.now().isoformat(timespec="seconds"), out_dir)
    _emit(event_callback, "info", f"run_start | out_dir={out_dir}")
    _ensure_not_cancelled(cancel_event)

    logger.info("manifest_fetch_start | url=%s | output=%s", config.manifest_url, manifest_path)
    _emit(event_callback, "manifest", f"manifest_fetch_start | url={config.manifest_url} | output={manifest_path}")
    manifest = fetch_manifest(config.manifest_url, manifest_path)
    logger.info("manifest_fetch_success | output=%s", manifest_path)
    _emit(event_callback, "manifest", f"manifest_fetch_success | output={manifest_path}")
    _ensure_not_cancelled(cancel_event)

    entries = parse_experts(manifest)
    entries = _apply_entry_limits(entries, config.limit, config.sample_agents, config.sample_teams)
    logger.info(
        "entries_loaded | count=%s | concurrency=%s | delay=%.2f-%.2fs | verify_existing=%s",
        len(entries),
        config.concurrency,
        config.delay_min,
        config.delay_max,
        config.verify_existing,
    )
    _emit(
        event_callback,
        "info",
        (
            "entries_loaded | "
            f"count={len(entries)} | concurrency={config.concurrency} | "
            f"delay={config.delay_min:.2f}-{config.delay_max:.2f}s"
        ),
    )
    if total_callback:
        total_callback(len(entries))
    _ensure_not_cancelled(cancel_event)

    def log_event(event: str, entry: ExpertEntry, url: str, target: Path, error: str = "") -> None:
        message = describe_download_event(event, entry, url, target, error)
        logger.info(message)
        _emit(event_callback, event, message)

    results = download_many(
        entries,
        out_dir=out_dir,
        bundle_base_url=config.bundle_base_url,
        concurrency=config.concurrency,
        retries=config.retries,
        delay_min=config.delay_min,
        delay_max=config.delay_max,
        verify_existing=config.verify_existing,
        log_callback=log_event,
        progress_callback=progress_callback,
        cancel_event=cancel_event,
    )
    _ensure_not_cancelled(cancel_event)

    report_path = out_dir / REPORT_FILENAME
    write_report(results, report_path, config.xlsx_template)

    summary = RunSummary(
        out_dir=out_dir,
        manifest_path=manifest_path,
        report_path=report_path,
        log_path=log_path,
        results=results,
    )
    logger.info("run_done | success_or_skipped=%s | failed=%s | report=%s", summary.success, summary.failed, report_path)
    _emit(
        event_callback,
        "done",
        f"run_done | success_or_skipped={summary.success} | failed={summary.failed} | report={report_path}",
    )
    return summary
