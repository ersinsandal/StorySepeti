"""
Download Queue Panel displaying active, pending, and completed tasks.
"""

import subprocess
import customtkinter as ctk
from typing import Dict, Any
from storysepeti.i18n import t, register_listener
from storysepeti.core.downloader import DownloadEngine, DownloadTask

STATUS_BADGES = {
    "pending": ("Bekliyor", "#F59E0B"),
    "running": ("İndiriliyor", "#6366F1"),
    "completed": ("Tamamlandı", "#10B981"),
    "failed": ("Hata", "#EF4444"),
    "cancelled": ("İptal Edildi", "#64748B")
}

class TaskCard(ctk.CTkFrame):
    def __init__(self, master, task: DownloadTask, on_cancel, on_retry, **kwargs):
        super().__init__(
            master,
            corner_radius=10,
            fg_color="#1E293B",
            border_width=1,
            border_color="#334155",
            **kwargs
        )
        self.task = task
        self.on_cancel = on_cancel
        self.on_retry = on_retry

        self.grid_columnconfigure(1, weight=1)

        # Icon
        self.lbl_icon = ctk.CTkLabel(
            self,
            text="📦" if "highlight" in task.title.lower() else "📱",
            font=ctk.CTkFont(size=22)
        )
        self.lbl_icon.grid(row=0, column=0, rowspan=2, padx=(12, 8), pady=8)

        # Title & Target
        self.lbl_title = ctk.CTkLabel(
            self,
            text=task.title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#F8FAFC",
            anchor="w"
        )
        self.lbl_title.grid(row=0, column=1, sticky="w", pady=(8, 0))

        # Status Badge
        text, color = STATUS_BADGES.get(task.status, (task.status, "#94A3B8"))
        self.badge = ctk.CTkLabel(
            self,
            text=f"  {text}  ",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#FFFFFF",
            fg_color=color,
            corner_radius=6,
            height=20
        )
        self.badge.grid(row=0, column=2, padx=12, pady=(8, 0), sticky="e")

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self,
            height=6,
            progress_color="#6366F1",
            fg_color="#0F172A"
        )
        self.progress_bar.grid(row=1, column=1, sticky="ew", pady=(4, 8), padx=(0, 10))
        self.progress_bar.set(task.progress / 100.0)

        # Action Button (Cancel or Open Folder)
        self.btn_action = ctk.CTkButton(
            self,
            text="İptal",
            width=65,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color="#374151",
            hover_color="#4B5563",
            command=self._handle_action
        )
        self.btn_action.grid(row=1, column=2, padx=12, pady=(0, 8), sticky="e")
        self._update_action_button()

    def update_task(self):
        text, color = STATUS_BADGES.get(self.task.status, (self.task.status, "#94A3B8"))
        if self.task.status == "running" and self.task.progress > 0:
            text = f"İndiriliyor %{self.task.progress:.0f}"
        self.badge.configure(text=f"  {text}  ", fg_color=color)
        self.progress_bar.set(self.task.progress / 100.0)
        self._update_action_button()

    def _update_action_button(self):
        if self.task.status in ("pending", "running"):
            self.btn_action.configure(text="İptal", fg_color="#374151", hover_color="#4B5563")
        elif self.task.status == "completed":
            self.btn_action.configure(text="Klasör", fg_color="#065F46", hover_color="#047857")
        elif self.task.status == "failed":
            self.btn_action.configure(text="Tekrar", fg_color="#991B1B", hover_color="#B91C1C")
        else:
            self.btn_action.grid_forget()

    def _handle_action(self):
        if self.task.status in ("pending", "running"):
            self.on_cancel(self.task.task_id)
        elif self.task.status == "completed":
            if self.task.output_dir.exists():
                try:
                    subprocess.Popen(["explorer", str(self.task.output_dir)])
                except Exception:
                    pass
        elif self.task.status == "failed":
            self.on_retry(self.task)


class QueuePanel(ctk.CTkFrame):
    def __init__(self, master, engine: DownloadEngine, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.engine = engine
        self._cards: Dict[str, TaskCard] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header with title and clear completed button
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.lbl_title = ctk.CTkLabel(
            self.header_frame,
            text=t("queue.title"),
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F8FAFC"
        )
        self.lbl_title.grid(row=0, column=0, sticky="w")

        self.btn_clear = ctk.CTkButton(
            self.header_frame,
            text=t("btn.clear_completed"),
            width=140,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="#334155",
            hover_color="#475569",
            command=self._clear_completed
        )
        self.btn_clear.grid(row=0, column=1, sticky="e")

        # Scrollable Task List
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        self.scroll_frame.grid(row=1, column=0, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self.lbl_empty = ctk.CTkLabel(
            self.scroll_frame,
            text=t("queue.empty"),
            font=ctk.CTkFont(size=13),
            text_color="#64748B"
        )
        self.lbl_empty.pack(pady=40)

        register_listener(self._on_language_change)

    def refresh(self):
        tasks = self.engine.tasks
        if not tasks:
            self.lbl_empty.pack(pady=40)
            return

        self.lbl_empty.pack_forget()

        for task_id, task in tasks.items():
            if task_id not in self._cards:
                card = TaskCard(
                    self.scroll_frame,
                    task=task,
                    on_cancel=self.engine.cancel_task,
                    on_retry=self._retry_task
                )
                card.pack(fill="x", pady=4, padx=2)
                self._cards[task_id] = card
            else:
                self._cards[task_id].update_task()

    def _retry_task(self, task: DownloadTask):
        self.engine.create_task(
            url_or_user=task.url,
            task_type=task.task_type,
            title_override=task.title
        )

    def _clear_completed(self):
        to_delete = [
            tid for tid, task in self.engine.tasks.items()
            if task.status in ("completed", "cancelled", "failed")
        ]
        for tid in to_delete:
            del self.engine.tasks[tid]
            if tid in self._cards:
                self._cards[tid].destroy()
                del self._cards[tid]
        if not self.engine.tasks:
            self.lbl_empty.pack(pady=40)

    def _on_language_change(self):
        self.lbl_title.configure(text=t("queue.title"))
        self.btn_clear.configure(text=t("btn.clear_completed"))
        self.lbl_empty.configure(text=t("queue.empty"))
