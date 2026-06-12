from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn

from .core import RunConfig, run_workflow
from .downloader import DEFAULT_BUNDLE_BASE_URL
from .manifest import DEFAULT_MANIFEST_URL


app = typer.Typer(help="Run WorkBuddy expert and expert-team bundle downloads.", no_args_is_help=True)
console = Console()


@app.callback()
def main() -> None:
    """WorkBuddy expert marketplace bundle tools."""


@app.command()
def run(
    out_dir: Annotated[
        Path | None,
        typer.Option(help="Output directory. Defaults to agent-outputs-YYYY-MM-DD-HHMMSS."),
    ] = None,
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
    log_file: Annotated[Path | None, typer.Option(help="Log file path. Defaults to <out-dir>/run.log.")] = None,
) -> None:
    """Fetch manifest, download bundles, and generate an xlsx report."""
    config = RunConfig(
        out_dir=out_dir,
        manifest_url=manifest_url,
        bundle_base_url=bundle_base_url,
        concurrency=concurrency,
        retries=retries,
        delay_min=delay_min,
        delay_max=delay_max,
        verify_existing=verify_existing,
        xlsx_template=xlsx_template,
        limit=limit,
        sample_agents=sample_agents,
        sample_teams=sample_teams,
        log_file=log_file,
    )

    color_by_event = {
        "manifest": "cyan",
        "info": "white",
        "start": "cyan",
        "success": "green",
        "skipped": "yellow",
        "retry": "magenta",
        "failed": "red",
        "done": "green",
    }
    task_id: object | None = None

    def on_event(event: str, message: str) -> None:
        color = color_by_event.get(event, "white")
        console.print(f"[{color}]{message}[/]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:

        def on_total(total: int) -> None:
            nonlocal task_id
            task_id = progress.add_task("Downloading bundles", total=total)

        def on_progress(done: int, total: int) -> None:
            if task_id is not None:
                progress.update(task_id, completed=done, total=total)

        summary = run_workflow(
            config,
            event_callback=on_event,
            total_callback=on_total,
            progress_callback=on_progress,
        )

    console.print(f"[green]Done[/green] success/skipped={summary.success}, failed={summary.failed}")
    console.print(f"Report: {summary.report_path}")
    console.print(f"Log: {summary.log_path}")
    if summary.failed:
        console.print("[yellow]Some bundles failed. See the failure retry queue sheet in the report.[/yellow]")


@app.command()
def gui() -> None:
    """Launch the CustomTkinter desktop app."""
    try:
        from .gui import run_gui
    except ModuleNotFoundError as exc:
        if exc.name == "customtkinter":
            raise typer.BadParameter('GUI dependency is missing. Install with: python -m pip install -e ".[gui]"') from exc
        raise
    run_gui()
