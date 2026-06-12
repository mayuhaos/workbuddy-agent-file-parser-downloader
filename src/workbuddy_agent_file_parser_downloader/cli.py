from __future__ import annotations

from datetime import datetime
import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn

from .downloader import DEFAULT_BUNDLE_BASE_URL, download_many
from .excel_report import REPORT_FILENAME, write_report
from .manifest import DEFAULT_MANIFEST_URL, fetch_manifest, parse_experts


app = typer.Typer(help="Sync WorkBuddy expert and expert-team bundles.", no_args_is_help=True)
console = Console()


def _setup_logger(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("workbuddy_agent_file_parser_downloader")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


def _describe_entry(event: str, entry, url: str, target: Path, error: str = "") -> str:
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


@app.callback()
def main() -> None:
    """WorkBuddy expert marketplace bundle tools."""


@app.command()
def sync(
    out_dir: Annotated[Path, typer.Option(help="Output directory.")] = Path("outputs"),
    manifest_url: Annotated[str, typer.Option(help="expert_center.json URL.")] = DEFAULT_MANIFEST_URL,
    bundle_base_url: Annotated[str, typer.Option(help="Base URL for bundle .tar.gz files.")] = DEFAULT_BUNDLE_BASE_URL,
    concurrency: Annotated[
        int,
        typer.Option(help="Download concurrency. Default is 1 to keep requests gentle."),
    ] = 1,
    retries: Annotated[int, typer.Option(help="Retry count for failed downloads.")] = 3,
    delay_min: Annotated[float, typer.Option(help="Minimum delay in seconds before remote bundle requests.")] = 1.0,
    delay_max: Annotated[float, typer.Option(help="Maximum delay in seconds before remote bundle requests.")] = 2.0,
    verify_existing: Annotated[
        bool,
        typer.Option(help="Use HEAD to verify existing file size before skipping."),
    ] = False,
    xlsx_template: Annotated[Path | None, typer.Option(help="Optional existing xlsx template path.")] = None,
    limit: Annotated[int | None, typer.Option(help="Optional: process only the first N entries.")] = None,
    sample_agents: Annotated[int | None, typer.Option(help="Optional: process only the first N agent entries.")] = None,
    sample_teams: Annotated[int | None, typer.Option(help="Optional: process only the first N team entries.")] = None,
    log_file: Annotated[Path | None, typer.Option(help="Log file path. Defaults to <out-dir>/sync.log.")] = None,
) -> None:
    """Fetch manifest, download bundles, and generate an xlsx report."""
    out_dir = out_dir.resolve()
    log_path = (log_file or out_dir / "sync.log").resolve()
    logger = _setup_logger(log_path)
    manifest_path = out_dir / "expert_center.json"

    logger.info("sync_start | started_at=%s | out_dir=%s", datetime.now().isoformat(timespec="seconds"), out_dir)
    logger.info("manifest_fetch_start | url=%s | output=%s", manifest_url, manifest_path)
    console.print(f"[bold]Manifest:[/bold] {manifest_url}")
    manifest = fetch_manifest(manifest_url, manifest_path)
    logger.info("manifest_fetch_success | output=%s", manifest_path)

    entries = parse_experts(manifest)
    if sample_agents is not None or sample_teams is not None:
        agent_limit = sample_agents if sample_agents is not None else 0
        team_limit = sample_teams if sample_teams is not None else 0
        entries = [
            *[entry for entry in entries if entry.expert_type == "agent"][: max(agent_limit, 0)],
            *[entry for entry in entries if entry.expert_type == "team"][: max(team_limit, 0)],
        ]
    if limit is not None:
        entries = entries[: max(limit, 0)]

    console.print(f"[bold]Entries:[/bold] {len(entries)}")
    logger.info(
        "entries_loaded | count=%s | concurrency=%s | delay=%.2f-%.2fs | verify_existing=%s",
        len(entries),
        concurrency,
        delay_min,
        delay_max,
        verify_existing,
    )

    def log_event(event: str, entry, url: str, target: Path, error: str = "") -> None:
        message = _describe_entry(event, entry, url, target, error)
        logger.info(message)
        color = {
            "start": "cyan",
            "success": "green",
            "skipped": "yellow",
            "retry": "magenta",
            "failed": "red",
        }.get(event, "white")
        timestamp = datetime.now().isoformat(sep=" ", timespec="milliseconds")
        console.print(f"[{color}]{timestamp}[/] {message}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("Downloading bundles", total=len(entries))
        results = download_many(
            entries,
            out_dir=out_dir,
            bundle_base_url=bundle_base_url,
            concurrency=concurrency,
            retries=retries,
            delay_min=delay_min,
            delay_max=delay_max,
            verify_existing=verify_existing,
            log_callback=log_event,
            progress=progress,
            task_id=task_id,
        )

    report_path = out_dir / REPORT_FILENAME
    write_report(results, report_path, xlsx_template)

    success = sum(1 for item in results if item.success)
    failed = len(results) - success
    logger.info("sync_done | success_or_skipped=%s | failed=%s | report=%s", success, failed, report_path)
    console.print(f"[green]Done[/green] success/skipped={success}, failed={failed}")
    console.print(f"Report: {report_path}")
    console.print(f"Log: {log_path}")
    if failed:
        console.print("[yellow]Some bundles failed. See sheet: 澶辫触閲嶈窇闃熷垪[/yellow]")

