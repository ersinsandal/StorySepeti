"""
Live Log Viewer Panel for StoryVault with color-coded severity levels.
"""

import datetime
import customtkinter as ctk
from typing import Optional

COLOR_MAP = {
    "info": "#D1D5DB",       # Light gray
    "success": "#10B981",    # Emerald green
    "warning": "#F59E0B",    # Amber
    "error": "#EF4444"       # Red
}

class LogPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header with title and clear button
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(4, 2))
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.lbl_title = ctk.CTkLabel(
            self.header_frame,
            text="Canlı İşlem Günlüğü",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#9CA3AF"
        )
        self.lbl_title.grid(row=0, column=0, sticky="w")

        self.btn_clear = ctk.CTkButton(
            self.header_frame,
            text="Temizle",
            width=60,
            height=22,
            font=ctk.CTkFont(size=11),
            fg_color="#374151",
            hover_color="#4B5563",
            command=self.clear_logs
        )
        self.btn_clear.grid(row=0, column=1, sticky="e")

        # Textbox for logs
        self.textbox = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
            fg_color="#0F172A",
            border_width=1,
            border_color="#1E293B"
        )
        self.textbox.grid(row=1, column=0, sticky="nsew", padx=8, pady=(2, 8))

        # Setup tags for colors
        for tag, color in COLOR_MAP.items():
            self.textbox.tag_config(tag, foreground=color)
        self.textbox.tag_config("time", foreground="#64748B")

        self.log("info", "StoryVault hazır. Bir link veya kullanıcı adı girerek başlayabilirsiniz.")

    def log(self, level: str, message: str) -> None:
        lvl = level.lower()
        if lvl not in COLOR_MAP:
            lvl = "info"

        now_str = datetime.datetime.now().strftime("[%H:%M:%S] ")
        icon = {
            "info": "ℹ️ ",
            "success": "✅ ",
            "warning": "⚠️ ",
            "error": "❌ "
        }.get(lvl, "")

        self.textbox.configure(state="normal")
        self.textbox.insert("end", now_str, "time")
        self.textbox.insert("end", f"{icon}{message}\n", lvl)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def clear_logs(self) -> None:
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")
