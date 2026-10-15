"""
Mode Selector Dashboard displaying 4 cards for all download scenarios.
"""

import customtkinter as ctk
from typing import Callable
from storysepeti.i18n import t, register_listener
from storysepeti.utils.url_parser import URLType

class ModeCard(ctk.CTkFrame):
    def __init__(self, master, icon: str, title_key: str, desc_key: str, on_click: Callable[[], None], **kwargs):
        super().__init__(
            master,
            corner_radius=12,
            fg_color="#1E293B",
            border_width=1,
            border_color="#334155",
            **kwargs
        )
        self.on_click = on_click
        self.title_key = title_key
        self.desc_key = desc_key

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Icon
        self.lbl_icon = ctk.CTkLabel(
            self,
            text=icon,
            font=ctk.CTkFont(size=32)
        )
        self.lbl_icon.grid(row=0, column=0, pady=(16, 4))

        # Title
        self.lbl_title = ctk.CTkLabel(
            self,
            text=t(self.title_key),
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#F8FAFC"
        )
        self.lbl_title.grid(row=1, column=0, padx=12, pady=(0, 4))

        # Description
        self.lbl_desc = ctk.CTkLabel(
            self,
            text=t(self.desc_key),
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8",
            wraplength=220,
            justify="center"
        )
        self.lbl_desc.grid(row=2, column=0, padx=12, pady=(0, 16))

        # Action Button
        self.btn_select = ctk.CTkButton(
            self,
            text="Seç",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#6366F1",
            hover_color="#4F46E5",
            corner_radius=8,
            height=32,
            command=self.on_click
        )
        self.btn_select.grid(row=3, column=0, padx=20, pady=(0, 16), sticky="ew")

        # Mouse hover effects
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _):
        self.configure(border_color="#6366F1", fg_color="#243248")

    def _on_leave(self, _):
        self.configure(border_color="#334155", fg_color="#1E293B")

    def refresh_texts(self):
        self.lbl_title.configure(text=t(self.title_key))
        self.lbl_desc.configure(text=t(self.desc_key))


class ModeSelector(ctk.CTkFrame):
    def __init__(self, master, on_select_mode: Callable[[URLType], None], **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_select_mode = on_select_mode

        self.grid_columnconfigure((0, 1), weight=1, uniform="group")
        self.grid_rowconfigure((1, 2), weight=1, uniform="group")

        # Header Title
        self.lbl_header = ctk.CTkLabel(
            self,
            text="İndirmek İstediğiniz İçeriği Seçin",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F8FAFC"
        )
        self.lbl_header.grid(row=0, column=0, columnspan=2, pady=(8, 16))

        # 4 Cards
        self.card_single_hl = ModeCard(
            self,
            icon="📦",
            title_key="mode.single_hl.title",
            desc_key="mode.single_hl.desc",
            on_click=lambda: self.on_select_mode(URLType.SINGLE_HIGHLIGHT)
        )
        self.card_single_hl.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.card_profile_hl = ModeCard(
            self,
            icon="🗂️",
            title_key="mode.profile_hl.title",
            desc_key="mode.profile_hl.desc",
            on_click=lambda: self.on_select_mode(URLType.PROFILE_HIGHLIGHTS)
        )
        self.card_profile_hl.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        self.card_single_story = ModeCard(
            self,
            icon="📱",
            title_key="mode.single_story.title",
            desc_key="mode.single_story.desc",
            on_click=lambda: self.on_select_mode(URLType.SINGLE_STORY)
        )
        self.card_single_story.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        self.card_user_stories = ModeCard(
            self,
            icon="⚡",
            title_key="mode.user_stories.title",
            desc_key="mode.user_stories.desc",
            on_click=lambda: self.on_select_mode(URLType.USER_STORIES)
        )
        self.card_user_stories.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

        register_listener(self._on_language_change)

    def _on_language_change(self):
        self.card_single_hl.refresh_texts()
        self.card_profile_hl.refresh_texts()
        self.card_single_story.refresh_texts()
        self.card_user_stories.refresh_texts()
