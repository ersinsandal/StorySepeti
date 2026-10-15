"""
Dynamic Download Panel for StorySepeti.
Supports URL/username entry, clipboard paste, profile highlight exploration,
folder selection, and live logging.
"""

import threading
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import customtkinter as ctk
from typing import Callable, Optional, List, Dict, Any

from storysepeti.i18n import t, register_listener
from storysepeti.utils.url_parser import parse_url, URLType
from storysepeti.core.downloader import DownloadEngine
from storysepeti.core.highlight import list_user_highlights
from storysepeti.config.settings import AppSettings
from .log_panel import LogPanel
from .progress_widget import ProgressWidget

class DownloadPanel(ctk.CTkFrame):
    def __init__(
        self,
        master,
        engine: DownloadEngine,
        settings: AppSettings,
        on_back: Callable[[], None],
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.engine = engine
        self.settings = settings
        self.on_back = on_back
        self.active_mode: URLType = URLType.SINGLE_HIGHLIGHT

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1) # Log panel expands

        # 1. Header Frame
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.btn_back = ctk.CTkButton(
            self.header_frame,
            text="← Geri",
            width=70,
            height=28,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            command=self.on_back
        )
        self.btn_back.grid(row=0, column=0, sticky="w")

        self.lbl_mode_title = ctk.CTkLabel(
            self.header_frame,
            text="Tek Highlight İndir",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#F8FAFC"
        )
        self.lbl_mode_title.grid(row=0, column=1, sticky="w", padx=12)

        # 2. Input Frame (URL / Username)
        self.input_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        self.input_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10), padx=2)
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.lbl_input_hint = ctk.CTkLabel(
            self.input_frame,
            text="Instagram highlight linkini veya /s/ kısa linkini girin:",
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8"
        )
        self.lbl_input_hint.grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(8, 2))

        self.entry_url = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="https://www.instagram.com/stories/highlights/...",
            height=38,
            font=ctk.CTkFont(size=13),
            fg_color="#0F172A",
            border_color="#475569"
        )
        self.entry_url.grid(row=1, column=0, sticky="ew", padx=(12, 6), pady=(0, 8))
        self.entry_url.bind("<KeyRelease>", self._on_url_typed)

        self.btn_paste = ctk.CTkButton(
            self.input_frame,
            text="Yapıştır",
            width=75,
            height=38,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#475569",
            hover_color="#64748B",
            command=self._paste_clipboard
        )
        self.btn_paste.grid(row=1, column=1, sticky="e", padx=(0, 6), pady=(0, 8))

        self.btn_fetch = ctk.CTkButton(
            self.input_frame,
            text="Listele",
            width=75,
            height=38,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#6366F1",
            hover_color="#4F46E5",
            command=self._fetch_profile_highlights
        )
        # Visible only in PROFILE_HIGHLIGHTS mode

        # Auto-detect status indicator
        self.lbl_detected = ctk.CTkLabel(
            self.input_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#10B981"
        )
        self.lbl_detected.grid(row=2, column=0, columnspan=3, sticky="w", padx=12, pady=(0, 6))

        # 3. Profile Highlights Selection Container (Scrollable Frame)
        self.highlights_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#1E293B",
            corner_radius=10,
            border_width=1,
            border_color="#334155",
            height=140
        )
        self.highlights_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self._highlight_checkboxes: List[ctk.CTkCheckBox] = []
        self._highlight_data: List[Dict[str, Any]] = []

        # 4. Action & Directory Row
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        self.action_frame.grid_columnconfigure(0, weight=1)

        # Output folder display
        self.folder_frame = ctk.CTkFrame(self.action_frame, fg_color="transparent")
        self.folder_frame.grid(row=0, column=0, sticky="w", pady=(0, 6))
        
        self.lbl_folder = ctk.CTkLabel(
            self.folder_frame,
            text=f"📁 {self.settings.output_dir}",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        )
        self.lbl_folder.grid(row=0, column=0, sticky="w")

        self.btn_change_folder = ctk.CTkButton(
            self.folder_frame,
            text="Değiştir",
            width=65,
            height=22,
            font=ctk.CTkFont(size=11),
            fg_color="#334155",
            hover_color="#475569",
            command=self._choose_output_dir
        )
        self.btn_change_folder.grid(row=0, column=1, sticky="w", padx=8)

        # Action Buttons (Start Download & Add to Queue)
        self.btn_start = ctk.CTkButton(
            self.action_frame,
            text="▶ İndirmeye Başla",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#6366F1",
            hover_color="#4F46E5",
            corner_radius=8,
            command=self._start_download
        )
        self.btn_start.grid(row=1, column=0, sticky="ew", pady=(0, 4))

        # 5. Progress Widget
        self.progress_widget = ProgressWidget(self)
        self.progress_widget.grid(row=4, column=0, sticky="ew", pady=(0, 8))

        # 6. Live Log Panel
        self.log_panel = LogPanel(self, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        self.log_panel.grid(row=5, column=0, sticky="nsew", pady=(0, 2))

        register_listener(self._on_language_change)

    def set_mode(self, mode: URLType) -> None:
        self.active_mode = mode
        self.entry_url.delete(0, "end")
        self.lbl_detected.configure(text="")
        self.progress_widget.reset()

        if mode == URLType.SINGLE_HIGHLIGHT:
            self.lbl_mode_title.configure(text=t("mode.single_hl.title"))
            self.lbl_input_hint.configure(text="Instagram highlight linkini veya /s/ kısa linkini girin:")
            self.entry_url.configure(placeholder_text="https://www.instagram.com/stories/highlights/...")
            self.btn_fetch.grid_forget()
            self.highlights_frame.grid_forget()

        elif mode == URLType.PROFILE_HIGHLIGHTS:
            self.lbl_mode_title.configure(text=t("mode.profile_hl.title"))
            self.lbl_input_hint.configure(text="Kullanıcı adını girin ve 'Listele' butonuna basın:")
            self.entry_url.configure(placeholder_text="Kullanıcı adı (örn: @johndoe)")
            self.btn_fetch.grid(row=1, column=2, sticky="e", padx=(0, 12), pady=(0, 8))
            self.highlights_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))

        elif mode == URLType.SINGLE_STORY:
            self.lbl_mode_title.configure(text=t("mode.single_story.title"))
            self.lbl_input_hint.configure(text="Tek bir aktif story bağlantısı girin:")
            self.entry_url.configure(placeholder_text="https://www.instagram.com/stories/username/1234567890...")
            self.btn_fetch.grid_forget()
            self.highlights_frame.grid_forget()

        elif mode == URLType.USER_STORIES:
            self.lbl_mode_title.configure(text=t("mode.user_stories.title"))
            self.lbl_input_hint.configure(text="Kullanıcı adını veya aktif story linkini girin:")
            self.entry_url.configure(placeholder_text="Kullanıcı adı veya https://www.instagram.com/stories/username/...")
            self.btn_fetch.grid_forget()
            self.highlights_frame.grid_forget()

    def _paste_clipboard(self) -> None:
        try:
            cb_text = self.clipboard_get().strip()
            if cb_text:
                self.entry_url.delete(0, "end")
                self.entry_url.insert(0, cb_text)
                self._on_url_typed()
        except Exception:
            pass

    def _on_url_typed(self, _=None) -> None:
        raw = self.entry_url.get().strip()
        if not raw:
            self.lbl_detected.configure(text="")
            return

        parsed = parse_url(raw)
        labels = {
            URLType.SINGLE_HIGHLIGHT: "✅ Algılandı: Tek Highlight",
            URLType.PROFILE_HIGHLIGHTS: "✅ Algılandı: Profil / Kullanıcı",
            URLType.SINGLE_STORY: "✅ Algılandı: Tek Aktif Story",
            URLType.USER_STORIES: "✅ Algılandı: Tüm Aktif Story'ler",
            URLType.UNKNOWN: "⚠️ Tanınmayan URL / Kullanıcı adı formatı"
        }
        self.lbl_detected.configure(
            text=labels.get(parsed.url_type, ""),
            text_color="#10B981" if parsed.url_type != URLType.UNKNOWN else "#F59E0B"
        )

    def _choose_output_dir(self) -> None:
        folder = filedialog.askdirectory(initialdir=self.settings.output_dir, title="Kayıt Klasörü Seç")
        if folder:
            self.settings.output_dir = folder
            self.settings.save()
            self.lbl_folder.configure(text=f"📁 {folder}")

    def _fetch_profile_highlights(self) -> None:
        raw = self.entry_url.get().strip().lstrip("@")
        if not raw:
            self.log_panel.log("error", "Lütfen bir kullanıcı adı girin.")
            return

        self.log_panel.log("info", f"@{raw} için highlight albümleri aranıyor...")
        self.btn_fetch.configure(state="disabled", text="Aranıyor...")

        def worker():
            try:
                with self.engine.cookie_manager.temp_netscape_file() as cookie_path:
                    highlights = list_user_highlights(raw, cookie_path, log_cb=self.log_panel.log)
            except Exception as e:
                highlights = []
                self.log_panel.log("error", f"Arama başarısız: {e}")

            self.after(0, lambda: self._display_highlight_list(highlights))

        threading.Thread(target=worker, daemon=True).start()

    def _display_highlight_list(self, highlights: List[Dict[str, Any]]) -> None:
        self.btn_fetch.configure(state="normal", text="Listele")
        for widget in self.highlights_frame.winfo_children():
            widget.destroy()

        self._highlight_checkboxes.clear()
        self._highlight_data = highlights

        if not highlights:
            lbl = ctk.CTkLabel(self.highlights_frame, text="Highlight albümü bulunamadı.", text_color="#94A3B8")
            lbl.pack(pady=10)
            return

        # Select all / Deselect all bar
        control_bar = ctk.CTkFrame(self.highlights_frame, fg_color="transparent")
        control_bar.pack(fill="x", padx=4, pady=(2, 6))

        btn_all = ctk.CTkButton(
            control_bar,
            text="Tümünü Seç",
            width=80,
            height=22,
            font=ctk.CTkFont(size=11),
            fg_color="#334155",
            command=self._select_all_highlights
        )
        btn_all.pack(side="left", padx=2)

        btn_none = ctk.CTkButton(
            control_bar,
            text="Seçimi Kaldır",
            width=80,
            height=22,
            font=ctk.CTkFont(size=11),
            fg_color="#334155",
            command=self._deselect_all_highlights
        )
        btn_none.pack(side="left", padx=2)

        for item in highlights:
            title = item.get("title") or "Highlight"
            count = item.get("count", 0)
            text_label = f"📁 {title}" + (f" ({count} öğe)" if count else "")
            cb = ctk.CTkCheckBox(
                self.highlights_frame,
                text=text_label,
                font=ctk.CTkFont(size=12),
                fg_color="#6366F1"
            )
            cb.select()
            cb.pack(anchor="w", padx=8, pady=4)
            self._highlight_checkboxes.append(cb)

    def _select_all_highlights(self) -> None:
        for cb in self._highlight_checkboxes:
            cb.select()

    def _deselect_all_highlights(self) -> None:
        for cb in self._highlight_checkboxes:
            cb.deselect()

    def _start_download(self) -> None:
        raw = self.entry_url.get().strip()
        if not raw:
            self.log_panel.log("error", "Lütfen geçerli bir URL veya kullanıcı adı girin.")
            return

        if not self.engine.cookie_manager.is_authenticated:
            self.log_panel.log("error", "Instagram oturumu açık değil! Lütfen Ayarlar veya Giriş Sihirbazından giriş yapın.")
            return

        if self.active_mode == URLType.PROFILE_HIGHLIGHTS and self._highlight_checkboxes:
            # Multi-highlight queue dispatch
            selected_items = [
                self._highlight_data[i]
                for i, cb in enumerate(self._highlight_checkboxes)
                if cb.get() == 1
            ]
            if not selected_items:
                self.log_panel.log("warning", "Lütfen en az bir highlight seçin.")
                return

            self.log_panel.log("info", f"{len(selected_items)} adet highlight kuyruğa ekleniyor...")
            for item in selected_items:
                self.engine.create_task(
                    url_or_user=item["url"],
                    task_type=URLType.SINGLE_HIGHLIGHT,
                    title_override=f"Highlight: {item['title']}"
                )
        else:
            self.log_panel.log("info", f"Görev oluşturuluyor: {raw}")
            parsed = parse_url(raw)
            if parsed.url_type in (URLType.SINGLE_STORY, URLType.SINGLE_HIGHLIGHT):
                target_mode = parsed.url_type
            else:
                target_mode = self.active_mode

            self.engine.create_task(
                url_or_user=raw,
                task_type=target_mode
            )

    def _on_language_change(self) -> None:
        self.set_mode(self.active_mode)
        self.btn_back.configure(text="← " + ("Geri" if t("app.title") == "StorySepeti" else "Back"))
        self.btn_paste.configure(text=t("input.paste"))
        self.btn_start.configure(text="▶ " + t("btn.download"))
        self.btn_change_folder.configure(text=t("input.change_folder"))
        self.lbl_folder.configure(text=f"📁 {self.settings.output_dir}")
