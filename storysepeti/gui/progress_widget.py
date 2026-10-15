"""
Custom Progress Bar Widget with speed, percentage, and stage info.
"""

import customtkinter as ctk

class ProgressWidget(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        # Header info (Stage & Percentage)
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        self.info_frame.grid_columnconfigure(0, weight=1)

        self.lbl_stage = ctk.CTkLabel(
            self.info_frame,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#E2E8F0"
        )
        self.lbl_stage.grid(row=0, column=0, sticky="w")

        self.lbl_percent = ctk.CTkLabel(
            self.info_frame,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#818CF8"
        )
        self.lbl_percent.grid(row=0, column=1, sticky="e")

        # Progress bar
        self.bar = ctk.CTkProgressBar(
            self,
            orientation="horizontal",
            mode="determinate",
            progress_color="#6366F1",
            fg_color="#1E293B",
            height=10
        )
        self.bar.grid(row=1, column=0, sticky="ew", pady=(2, 4))
        self.bar.set(0.0)

        # Bottom detail (speed, eta, etc.)
        self.lbl_detail = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        )
        self.lbl_detail.grid(row=2, column=0, sticky="w")

    def update_progress(self, percent: float, detail: str = "", stage: str = "") -> None:
        p = max(0.0, min(100.0, percent))
        self.bar.set(p / 100.0)
        self.lbl_percent.configure(text=f"%{p:.1f}" if p > 0 else "")
        if detail:
            self.lbl_detail.configure(text=detail)
        if stage:
            self.lbl_stage.configure(text=stage)

    def reset(self) -> None:
        self.bar.set(0.0)
        self.lbl_percent.configure(text="")
        self.lbl_detail.configure(text="")
        self.lbl_stage.configure(text="")
