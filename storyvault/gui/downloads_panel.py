"""
Downloads Manager Panel for StoryVault.
Scans and displays downloaded media files with playback, folder reveal, filtering, and deletion.
"""

import os
import datetime
import subprocess
from pathlib import Path
import customtkinter as ctk
from typing import List, Dict, Any, Optional

from storyvault.i18n import t, register_listener
from storyvault.config.settings import AppSettings

MEDIA_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov"}

def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

class MediaCard(ctk.CTkFrame):
    def __init__(self, master, file_path: Path, on_delete, **kwargs):
        super().__init__(
            master,
            corner_radius=10,
            fg_color="#1E293B",
            border_width=1,
            border_color="#334155",
            **kwargs
        )
        self.file_path = file_path
        self.on_delete = on_delete

        self.grid_columnconfigure(1, weight=1)

        is_video = file_path.suffix.lower() in VIDEO_EXTS
        icon_text = "🎬" if is_video else "🖼️"

        # Icon
        self.lbl_icon = ctk.CTkLabel(
            self,
            text=icon_text,
            font=ctk.CTkFont(size=24)
        )
        self.lbl_icon.grid(row=0, column=0, rowspan=2, padx=(12, 10), pady=10)

        # Title & Path Info
        self.lbl_title = ctk.CTkLabel(
            self,
            text=file_path.name,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#F8FAFC",
            anchor="w"
        )
        self.lbl_title.grid(row=0, column=1, sticky="w", pady=(8, 0))

        # Metadata (Size, Date, Tag)
        try:
            stat = file_path.stat()
            size_str = _format_size(stat.st_size)
            date_str = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M")
        except Exception:
            size_str = ""
            date_str = ""

        is_story = "stories" in str(file_path).lower() or "_st_" in file_path.name.lower()
        tag_str = "Story" if is_story else "Highlight"
        tag_color = "#3B82F6" if is_story else "#8B5CF6"

        self.meta_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.meta_frame.grid(row=1, column=1, sticky="w", pady=(2, 8))

        self.tag_badge = ctk.CTkLabel(
            self.meta_frame,
            text=f" {tag_str} ",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#FFFFFF",
            fg_color=tag_color,
            corner_radius=4,
            height=16
        )
        self.tag_badge.pack(side="left", padx=(0, 8))

        self.lbl_details = ctk.CTkLabel(
            self.meta_frame,
            text=f"{size_str}  •  {date_str}",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        )
        self.lbl_details.pack(side="left")

        # Action Buttons
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=0, column=2, rowspan=2, padx=12, pady=8, sticky="e")

        self.btn_open = ctk.CTkButton(
            self.btn_frame,
            text="Aç",
            width=50,
            height=26,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#6366F1",
            hover_color="#4F46E5",
            command=self._open_file
        )
        self.btn_open.pack(side="left", padx=2)

        self.btn_locate = ctk.CTkButton(
            self.btn_frame,
            text="Klasörde Göster",
            width=95,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#334155",
            hover_color="#475569",
            command=self._locate_file
        )
        self.btn_locate.pack(side="left", padx=2)

        self.btn_delete = ctk.CTkButton(
            self.btn_frame,
            text="🗑️",
            width=32,
            height=26,
            font=ctk.CTkFont(size=12),
            fg_color="#374151",
            hover_color="#DC2626",
            command=self._delete_file
        )
        self.btn_delete.pack(side="left", padx=2)

    def _open_file(self):
        try:
            os.startfile(str(self.file_path))
        except Exception:
            pass

    def _locate_file(self):
        try:
            subprocess.Popen(["explorer", f"/select,{str(self.file_path)}"])
        except Exception:
            pass

    def _delete_file(self):
        try:
            if self.file_path.exists():
                self.file_path.unlink()
        except Exception:
            pass
        self.on_delete(self)


class DownloadsPanel(ctk.CTkFrame):
    def __init__(self, master, settings: AppSettings, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.settings = settings
        self._cards: List[MediaCard] = []
        self._all_files: List[Path] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Header Frame
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.lbl_title = ctk.CTkLabel(
            self.header_frame,
            text="📁 İndirilenler",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F8FAFC"
        )
        self.lbl_title.grid(row=0, column=0, sticky="w")

        btn_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        btn_box.grid(row=0, column=1, sticky="e")

        self.btn_refresh = ctk.CTkButton(
            btn_box,
            text="🔄 Yenile",
            width=80,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="#334155",
            hover_color="#475569",
            command=self.refresh
        )
        self.btn_refresh.pack(side="left", padx=(0, 6))

        self.btn_open_root = ctk.CTkButton(
            btn_box,
            text="Klasörü Aç",
            width=100,
            height=30,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#6366F1",
            hover_color="#4F46E5",
            command=self._open_root_folder
        )
        self.btn_open_root.pack(side="left")

        # 2. Filter Bar
        self.filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_bar.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        self.filter_seg = ctk.CTkSegmentedButton(
            self.filter_bar,
            values=["Tümü", "Story'ler", "Highlight'lar", "Videolar", "Fotoğraflar"],
            command=self._apply_filter
        )
        self.filter_seg.set("Tümü")
        self.filter_seg.pack(side="left")

        self.lbl_count = ctk.CTkLabel(
            self.filter_bar,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8"
        )
        self.lbl_count.pack(side="right")

        # 3. Scrollable List Container
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=2, column=0, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self.lbl_empty = ctk.CTkLabel(
            self.scroll_frame,
            text="Henüz indirilmiş bir medya bulunmuyor.\nİndirdiğiniz story ve highlight'lar burada listelenecektir.",
            font=ctk.CTkFont(size=13),
            text_color="#64748B",
            justify="center"
        )
        self.lbl_empty.pack(pady=60)

        register_listener(self._on_language_change)

    def refresh(self):
        out_path = Path(self.settings.output_dir)
        self._all_files.clear()

        if out_path.exists():
            for root, _, files in os.walk(out_path):
                for f in files:
                    p = Path(root) / f
                    if p.suffix.lower() in MEDIA_EXTS:
                        self._all_files.append(p)

        # Sort newest first
        self._all_files.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
        self._apply_filter(self.filter_seg.get())

    def _apply_filter(self, filter_name: str):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        self._cards.clear()

        filtered = []
        for p in self._all_files:
            if not p.exists():
                continue
            is_video = p.suffix.lower() in VIDEO_EXTS
            is_story = "stories" in str(p).lower() or "_st_" in p.name.lower()

            if filter_name == "Story'ler" and not is_story:
                continue
            elif filter_name == "Highlight'lar" and is_story:
                continue
            elif filter_name == "Videolar" and not is_video:
                continue
            elif filter_name == "Fotoğraflar" and is_video:
                continue

            filtered.append(p)

        self.lbl_count.configure(text=f"{len(filtered)} dosya")

        if not filtered:
            self.lbl_empty = ctk.CTkLabel(
                self.scroll_frame,
                text="Bu filtreye uygun dosya bulunamadı.",
                font=ctk.CTkFont(size=13),
                text_color="#64748B"
            )
            self.lbl_empty.pack(pady=60)
            return

        for p in filtered:
            card = MediaCard(self.scroll_frame, file_path=p, on_delete=self._on_card_deleted)
            card.pack(fill="x", pady=4, padx=2)
            self._cards.append(card)

    def _on_card_deleted(self, card: MediaCard):
        if card in self._cards:
            self._cards.remove(card)
        if card.file_path in self._all_files:
            self._all_files.remove(card.file_path)
        card.destroy()
        self.lbl_count.configure(text=f"{len(self._cards)} dosya")
        if not self._cards:
            self.lbl_empty = ctk.CTkLabel(
                self.scroll_frame,
                text="Henüz indirilmiş bir medya bulunmuyor.",
                font=ctk.CTkFont(size=13),
                text_color="#64748B"
            )
            self.lbl_empty.pack(pady=60)

    def _open_root_folder(self):
        out_path = Path(self.settings.output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.Popen(["explorer", str(out_path)])
        except Exception:
            pass

    def _on_language_change(self):
        is_tr = (t("app.title") == "StoryVault")
        self.lbl_title.configure(text="📁 " + ("İndirilenler" if is_tr else "Downloads"))
        self.btn_refresh.configure(text="🔄 " + ("Yenile" if is_tr else "Refresh"))
        self.btn_open_root.configure(text="Klasörü Aç" if is_tr else "Open Folder")
