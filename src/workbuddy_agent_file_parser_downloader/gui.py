from __future__ import annotations

from pathlib import Path
from queue import Empty, Queue
from threading import Thread
import os
import platform
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk

from .core import RunConfig, RunSummary, default_output_dir, run_workflow


class WorkBuddyApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("WorkBuddy Agent File Parser Downloader")
        self.geometry("980x680")
        self.minsize(860, 560)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.queue: Queue[tuple[str, Any]] = Queue()
        self.worker: Thread | None = None
        self.summary: RunSummary | None = None

        self.output_dir_var = tk.StringVar(value="")
        self.mode_var = tk.StringVar(value="测试模式")
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_label_var = tk.StringVar(value="0 / 0")

        self._build_ui()
        self.after(100, self._poll_queue)

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="WorkBuddy Agent File Parser Downloader",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=24, pady=(18, 4))

        subtitle = ctk.CTkLabel(
            header,
            text="下载 WorkBuddy 专家/专家团智能体文件，并生成本地 Excel 清单。",
            text_color=("gray35", "gray70"),
        )
        subtitle.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 18))

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

        self.browse_button = ctk.CTkButton(controls, text="选择目录", command=self._choose_output_dir, width=130)
        self.browse_button.grid(row=0, column=2, padx=12, pady=(16, 8))

        ctk.CTkLabel(controls, text="运行模式").grid(row=1, column=0, sticky="w", padx=(16, 10), pady=(8, 16))
        self.mode_segment = ctk.CTkSegmentedButton(
            controls,
            values=["测试模式", "全量模式"],
            variable=self.mode_var,
            width=220,
        )
        self.mode_segment.grid(row=1, column=1, sticky="w", pady=(8, 16))

        self.start_button = ctk.CTkButton(controls, text="开始下载", command=self._start_download, width=130)
        self.start_button.grid(row=1, column=2, padx=12, pady=(8, 16))

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

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=4, column=0, sticky="ew", padx=24, pady=(6, 20))
        footer.grid_columnconfigure(0, weight=1)

        self.result_label = ctk.CTkLabel(footer, text="", anchor="w")
        self.result_label.grid(row=0, column=0, sticky="ew")
        self.open_button = ctk.CTkButton(footer, text="打开输出目录", command=self._open_output_dir, state="disabled")
        self.open_button.grid(row=0, column=1, sticky="e", padx=(12, 0))

    def _choose_output_dir(self) -> None:
        selected = filedialog.askdirectory(title="选择输出目录")
        if selected:
            self.output_dir_var.set(selected)

    def _append_log(self, message: str) -> None:
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _set_running(self, running: bool) -> None:
        state = "disabled" if running else "normal"
        self.start_button.configure(state=state)
        self.browse_button.configure(state=state)
        self.mode_segment.configure(state=state)

    def _start_download(self) -> None:
        if self.worker and self.worker.is_alive():
            return

        raw_out_dir = self.output_dir_var.get().strip()
        out_dir = Path(raw_out_dir) if raw_out_dir else default_output_dir()
        mode = self.mode_var.get()
        sample_agents = 2 if mode == "测试模式" else None
        sample_teams = 1 if mode == "测试模式" else None

        self.summary = None
        self.output_dir_var.set(str(out_dir))
        self.result_label.configure(text="")
        self.open_button.configure(state="disabled")
        self.progress_var.set(0)
        self.progress_label_var.set("0 / 0")
        self.status_var.set("运行中")
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self._set_running(True)

        config = RunConfig(out_dir=out_dir, sample_agents=sample_agents, sample_teams=sample_teams)
        self.worker = Thread(target=self._worker_run, args=(config,), daemon=True)
        self.worker.start()

    def _worker_run(self, config: RunConfig) -> None:
        try:
            summary = run_workflow(
                config,
                event_callback=lambda _event, message: self.queue.put(("log", message)),
                total_callback=lambda total: self.queue.put(("total", total)),
                progress_callback=lambda done, total: self.queue.put(("progress", done, total)),
            )
            self.queue.put(("done", summary))
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
        messagebox.showinfo("下载完成", f"已完成。\n\n输出目录：\n{summary.out_dir}\n\nExcel 清单：\n{summary.report_path}")

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
