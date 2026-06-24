from __future__ import annotations

from pathlib import Path
from queue import Empty, Queue
from threading import Event, Thread
import ctypes
from datetime import datetime
import os
import platform
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Any
import webbrowser

import customtkinter as ctk

from .core import RunConfig, RunSummary, WorkflowCancelledError, default_output_dir, run_workflow


REPOSITORY_URL = "https://github.com/mayuhaos/workbuddy-agent-file-parser-downloader"
APP_ICON_PATH = Path(__file__).resolve().parents[2] / "assets" / "workbuddy-agent-file-parser-downloader.ico"
APP_USER_MODEL_ID = "mayuhaos.workbuddy_agent_file_parser_downloader"
OUTPUT_DIR_PREFIX = "workbuddy-agent"
MODE_TEST = "测试模式"
MODE_FULL = "全量模式"
APP_ICON_PNG_BASE64 = (
    "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"
)
GITHUB_ICON_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAACXBIWXMAAAsTAAALEwEAmpwYAAADXklEQVR4"
    "nO2aS2xNQRjHf1WPtokiHtVQGolY0JVHiI0o8QptFxIW3QiVkIoNQTwrIkiVELpAxEKwZCdl6xGJXVVJSLw2"
    "bRCL3mqvK5N8TW5O7jnfue6Zc25lfskkTe/M/f9n7pxvZr454HA4HA6Hw+FwxEUZUAesARqkmL8XyWf/HROA"
    "JqAT6AHSQManpKXOdaARGM8opgboAPoDOqwV0/YiMJtRxCTgMjBYQMe9ZVAGopIiZx3wNcKOe8sXYC1FSAnQ"
    "pjzfURWjcUI0i4JS4FYMHfeWG6KdKCViJJNQuZP0TGhLsPMj5XiSAS+dw9BdoB44KGt6oR18AxyQ77znExPM"
    "RipWKgOi/YqsemZ6bgc+eur0Ad3Acynd8r/sOqbNNs8UX+mj+RmYGOcAXAr4xWblqF8O7AO2AlUB31sldVp9"
    "tsU1AbrtxESNssmZZlF7eoBuymfwY/31M8B8i9oLFO32OA42/YqJ9Rb1NyrafbYPUE2KgSFgiUX9paIR5GGL"
    "RX06FXFzYLFNh+Lhmk3xngDhtARI28xVzhxmSbVCuSLcRXw8DfAxLLEqcuqUqXeK+DiteFloQ7ReEd1JfLQo"
    "XlbZEG1QRJuJj+YkVoJNiuge4qNV8bLBhugyRfQs8XFO8WL2C5EzTxF9THx0KV5qbYhWyBLjJ2oOSFOwz1Tl"
    "MDYkS7YVXikjfwj7HFE8vLQp3q6IfwfmWNQ3U/uH4uGCRX02K+IZmSWTLWibx+t1CH2zWlljPPAthIm3wPII"
    "dU2arTfkxck4LHPSI9oiqawdnrzekKTMFxegZZazm0rwjT1DXO2JwuZgMkM+M3vwXzmMfQLuSwDTOAo8kDaZ"
    "PEpKyTdGyhmP+IesrKzZpv7xMbkrxHfvzrPjI8XcUcRGOfDeY+B81ud7c6zVqZDrc4XUzafzvUm8XFHvyQ+k"
    "ZLdI1uNgXnR4JNfl+ezPu/PovIkPq0mI/R4zDyO6q3uRxwCY+4ZEueIxdDuCW5qwA2Dyg4lTClz1GPsp93gm"
    "MB0Wo2b5jHIAzGM1hiKiRUlZP4toAIaLYdoHBcZ3PsbNJWihA9CbZMALS5lM94ECssZPPG0H5LWYUfUeYbVs"
    "Tc3V9W/JKYalUdqYtseAmYxixv5jhqZW2jocDofD4XA4HA4i5y9GNvqaZdriqQAAAABJRU5ErkJggg=="
)


class WorkBuddyApp(ctk.CTk):
    def __init__(self) -> None:
        self._set_windows_app_id()
        super().__init__()
        self.title("WorkBuddy Agent File Parser Downloader")
        self.geometry("980x680")
        self.minsize(920, 560)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.queue: Queue[tuple[str, Any]] = Queue()
        self.worker: Thread | None = None
        self.summary: RunSummary | None = None
        self.cancel_event = Event()
        self.github_icon_image: tk.PhotoImage | None = None
        self.window_icon_image: tk.PhotoImage | None = None

        self.output_dir_var = tk.StringVar(value="")
        self.mode_var = tk.StringVar(value=MODE_TEST)
        self.status_var = tk.StringVar(value="准备就绪")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_label_var = tk.StringVar(value="0 / 0")

        self._set_window_icon()
        self._build_ui()
        self.after(100, self._poll_queue)

    def _set_windows_app_id(self) -> None:
        if platform.system() != "Windows":
            return
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
        except (AttributeError, OSError):
            pass

    def _set_window_icon(self) -> None:
        if APP_ICON_PATH.exists():
            try:
                self.iconbitmap(default=str(APP_ICON_PATH))
            except tk.TclError:
                pass

        try:
            self.window_icon_image = tk.PhotoImage(data=APP_ICON_PNG_BASE64)
            self.iconphoto(True, self.window_icon_image)
        except tk.TclError:
            self.window_icon_image = None

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray95", "gray12"))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title_block = ctk.CTkFrame(header, fg_color="transparent")
        title_block.grid(row=0, column=0, sticky="ew", padx=(24, 12), pady=(18, 18))
        title_block.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            title_block,
            text="WorkBuddy Agent File Parser Downloader",
            font=ctk.CTkFont(size=26, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = ctk.CTkLabel(
            title_block,
            text="下载 WorkBuddy 专家与专家团文件，并生成本地 Excel 清单。",
            text_color=("gray35", "gray70"),
            font=ctk.CTkFont(size=13),
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(6, 0))

        header_actions = ctk.CTkFrame(header, fg_color="transparent")
        header_actions.grid(row=0, column=1, sticky="ne", padx=(8, 24), pady=(18, 18))

        self.github_icon_image = tk.PhotoImage(data=GITHUB_ICON_BASE64)
        self.github_button = ctk.CTkButton(
            header_actions,
            text="GitHub",
            image=self.github_icon_image,
            compound="left",
            command=self._open_repository,
            width=128,
            height=40,
            corner_radius=20,
            fg_color=("#FFFFFF", "#FFFFFF"),
            hover_color=("#F3F4F6", "#E5E7EB"),
            text_color=("#111111", "#111111"),
            border_width=1,
            border_color=("#111111", "#111111"),
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.github_button.grid(row=0, column=0, sticky="e")

        controls = ctk.CTkFrame(self)
        controls.grid(row=1, column=0, sticky="ew", padx=24, pady=(18, 10))
        controls.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(controls, text="输出目录").grid(row=0, column=0, sticky="w", padx=(16, 10), pady=(16, 8))
        self.output_entry = ctk.CTkEntry(
            controls,
            textvariable=self.output_dir_var,
            placeholder_text="默认：agent-outputs-YYYY-MM-DD-HHMMSS",
        )
        self.output_entry.grid(row=0, column=1, sticky="ew", pady=(16, 8))

        self.browse_button = ctk.CTkButton(
            controls,
            text="选择目录",
            command=self._choose_output_dir,
            width=130,
        )
        self.browse_button.grid(row=0, column=2, padx=12, pady=(16, 8))

        ctk.CTkLabel(controls, text="运行模式").grid(row=1, column=0, sticky="w", padx=(16, 10), pady=(8, 16))
        self.mode_segment = ctk.CTkSegmentedButton(
            controls,
            values=[MODE_TEST, MODE_FULL],
            variable=self.mode_var,
            width=220,
        )
        self.mode_segment.grid(row=1, column=1, sticky="w", pady=(8, 16))

        action_buttons = ctk.CTkFrame(controls, fg_color="transparent")
        action_buttons.grid(row=1, column=2, padx=12, pady=(8, 16), sticky="e")

        self.start_button = ctk.CTkButton(
            action_buttons,
            text="开始下载",
            command=self._start_download,
            width=118,
        )
        self.start_button.grid(row=0, column=0, padx=(0, 8))

        self.stop_button = ctk.CTkButton(
            action_buttons,
            text="停止",
            command=self._stop_download,
            width=88,
            fg_color=("#FEE2E2", "#7F1D1D"),
            hover_color=("#FECACA", "#991B1B"),
            text_color=("#991B1B", "#FEE2E2"),
            border_width=1,
            border_color=("#DC2626", "#FCA5A5"),
            state="disabled",
        )
        self.stop_button.grid(row=0, column=1)

        progress_frame = ctk.CTkFrame(self)
        progress_frame.grid(row=2, column=0, sticky="ew", padx=24, pady=10)
        progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, variable=self.progress_var)
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        self.progress_bar.set(0)

        progress_meta = ctk.CTkFrame(progress_frame, fg_color="transparent")
        progress_meta.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 16))
        progress_meta.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(progress_meta, textvariable=self.status_var)
        self.status_label.grid(row=0, column=0, sticky="w")
        self.progress_count_label = ctk.CTkLabel(progress_meta, textvariable=self.progress_label_var)
        self.progress_count_label.grid(row=0, column=1, sticky="e")

        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=3, column=0, sticky="nsew", padx=24, pady=10)
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(log_frame, text="实时日志", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0,
            column=0,
            sticky="w",
            padx=16,
            pady=(14, 8),
        )
        self.log_box = ctk.CTkTextbox(log_frame, wrap="none")
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.log_box.configure(state="disabled")

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=4, column=0, sticky="ew", padx=24, pady=(6, 20))
        footer.grid_columnconfigure(0, weight=1)

        self.result_label = ctk.CTkLabel(footer, text="", anchor="w")
        self.result_label.grid(row=0, column=0, sticky="ew")
        self.open_button = ctk.CTkButton(
            footer,
            text="打开输出目录",
            command=self._open_output_dir,
            state="disabled",
        )
        self.open_button.grid(row=0, column=1, sticky="e", padx=(12, 0))

    def _choose_output_dir(self) -> None:
        selected = filedialog.askdirectory(title="选择输出目录")
        if selected:
            self.output_dir_var.set(str(self._build_output_dir(Path(selected))))

    def _build_output_dir(self, base_dir: Path, now: datetime | None = None) -> Path:
        current = now or datetime.now()
        folder_name = f"{OUTPUT_DIR_PREFIX}-{current:%Y%m%d-%H%M%S}"
        return base_dir / folder_name

    def _open_repository(self) -> None:
        webbrowser.open_new_tab(REPOSITORY_URL)

    def _append_log(self, message: str) -> None:
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _set_running(self, running: bool) -> None:
        normal_or_disabled = "disabled" if running else "normal"
        self.start_button.configure(state=normal_or_disabled)
        self.browse_button.configure(state=normal_or_disabled)
        self.mode_segment.configure(state=normal_or_disabled)
        self.github_button.configure(state=normal_or_disabled)
        self.stop_button.configure(state="normal" if running else "disabled")

    def _start_download(self) -> None:
        if self.worker and self.worker.is_alive():
            return

        raw_out_dir = self.output_dir_var.get().strip()
        out_dir = Path(raw_out_dir) if raw_out_dir else self._build_output_dir(Path.cwd())
        mode = self.mode_var.get()
        sample_agents = 2 if mode == MODE_TEST else None
        sample_teams = 1 if mode == MODE_TEST else None

        self.cancel_event = Event()
        self.summary = None
        self.output_dir_var.set(str(out_dir))
        self.result_label.configure(text="")
        self.open_button.configure(state="disabled")
        self.progress_var.set(0)
        self.progress_label_var.set("0 / 0")
        self.status_var.set("运行中...")
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self._set_running(True)

        config = RunConfig(out_dir=out_dir, sample_agents=sample_agents, sample_teams=sample_teams)
        self.worker = Thread(target=self._worker_run, args=(config,), daemon=True)
        self.worker.start()

    def _stop_download(self) -> None:
        if not self.worker or not self.worker.is_alive():
            return
        self.cancel_event.set()
        self.status_var.set("正在停止...")
        self._append_log("INFO: 已请求停止，正在结束当前任务...")
        self.stop_button.configure(state="disabled")

    def _worker_run(self, config: RunConfig) -> None:
        try:
            summary = run_workflow(
                config,
                event_callback=lambda _event, message: self.queue.put(("log", message)),
                total_callback=lambda total: self.queue.put(("total", total)),
                progress_callback=lambda done, total: self.queue.put(("progress", done, total)),
                cancel_event=self.cancel_event,
            )
            self.queue.put(("done", summary))
        except WorkflowCancelledError:
            self.queue.put(("cancelled",))
        except Exception as exc:
            self.queue.put(("error", str(exc)))

    def _poll_queue(self) -> None:
        try:
            while True:
                item = self.queue.get_nowait()
                kind = item[0]
                if kind == "log":
                    self._append_log(item[1])
                elif kind == "total":
                    total = item[1]
                    self.progress_label_var.set(f"0 / {total}")
                    self.progress_var.set(0)
                elif kind == "progress":
                    done, total = item[1], item[2]
                    self.progress_label_var.set(f"{done} / {total}")
                    self.progress_var.set(done / total if total else 1)
                elif kind == "done":
                    self._finish_success(item[1])
                elif kind == "cancelled":
                    self._finish_cancelled()
                elif kind == "error":
                    self._finish_error(item[1])
        except Empty:
            pass
        self.after(100, self._poll_queue)

    def _finish_success(self, summary: RunSummary) -> None:
        self.summary = summary
        self.status_var.set(f"完成。成功/跳过={summary.success}，失败={summary.failed}")
        self.result_label.configure(text=f"输出目录：{summary.out_dir} | 清单：{summary.report_path}")
        self.open_button.configure(state="normal")
        self._set_running(False)
        messagebox.showinfo(
            "下载完成",
            f"已完成。\n\n输出目录：\n{summary.out_dir}\n\nExcel 清单：\n{summary.report_path}",
        )

    def _finish_cancelled(self) -> None:
        self.status_var.set("已停止")
        self.result_label.configure(text="本次下载已由用户停止。")
        self._set_running(False)
        self._append_log("INFO: 本次下载已停止。")

    def _finish_error(self, error: str) -> None:
        self.status_var.set("失败")
        self._append_log(f"ERROR: {error}")
        self._set_running(False)
        messagebox.showerror("下载失败", error)

    def _open_output_dir(self) -> None:
        target = self.summary.out_dir if self.summary else Path(self.output_dir_var.get().strip() or ".")
        if not target.exists():
            messagebox.showwarning("目录不存在", str(target))
            return
        system = platform.system()
        if system == "Windows":
            os.startfile(target)  # type: ignore[attr-defined]
        elif system == "Darwin":
            subprocess.Popen(["open", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])


def run_gui() -> None:
    app = WorkBuddyApp()
    app.mainloop()
