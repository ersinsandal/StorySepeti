"""
Settings Panel for StorySepeti.
Controls Instagram session, download quality, dependencies, output folder, and language.
"""

from tkinter import filedialog
import customtkinter as ctk
from typing import Callable

from storysepeti.i18n import t, get_language, set_language, register_listener
from storysepeti.config.settings import AppSettings
from storysepeti.cookies.manager import CookieManager
from storysepeti.utils.dep_checker import check_all_dependencies

class SettingsPanel(ctk.CTkScrollableFrame):
    def __init__(
        self,
        master,
        settings: AppSettings,
        cookie_manager: CookieManager,
        on_open_wizard: Callable[[], None],
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.settings = settings
        self.cookie_manager = cookie_manager
        self.on_open_wizard = on_open_wizard

        self.grid_columnconfigure(0, weight=1)

        # Title
        self.lbl_title = ctk.CTkLabel(
            self,
            text=t("settings.title"),
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F8FAFC"
        )
        self.lbl_title.pack(anchor="w", pady=(0, 16))

        # 1. Instagram Session Card
        self.card_session = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        self.card_session.pack(fill="x", pady=(0, 12), padx=2)

        lbl_s_title = ctk.CTkLabel(
            self.card_session,
            text=t("settings.session_title"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F8FAFC"
        )
        lbl_s_title.pack(anchor="w", padx=16, pady=(12, 6))

        self.lbl_session_status = ctk.CTkLabel(
            self.card_session,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="#10B981"
        )
        self.lbl_session_status.pack(anchor="w", padx=16, pady=(0, 10))

        btn_row = ctk.CTkFrame(self.card_session, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 12))

        self.btn_refresh = ctk.CTkButton(
            btn_row,
            text=t("settings.btn_refresh_cookie"),
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#6366F1",
            hover_color="#4F46E5",
            command=self.on_open_wizard
        )
        self.btn_refresh.pack(side="left", padx=(0, 8))

        self.btn_logout = ctk.CTkButton(
            btn_row,
            text=t("settings.btn_logout"),
            font=ctk.CTkFont(size=12),
            fg_color="#374151",
            hover_color="#4B5563",
            command=self._logout
        )
        self.btn_logout.pack(side="left")

        # 2. Quality & Download Card
        self.card_quality = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        self.card_quality.pack(fill="x", pady=(0, 12), padx=2)

        lbl_q_title = ctk.CTkLabel(
            self.card_quality,
            text=t("settings.download_prefs"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F8FAFC"
        )
        lbl_q_title.pack(anchor="w", padx=16, pady=(12, 8))

        self.lbl_quality_mode = ctk.CTkLabel(
            self.card_quality,
            text=t("settings.quality_mode"),
            font=ctk.CTkFont(size=12),
            text_color="#94A3B8"
        )
        self.lbl_quality_mode.pack(anchor="w", padx=16, pady=(0, 4))

        self.quality_combo = ctk.CTkComboBox(
            self.card_quality,
            values=[
                "Maksimum Kalite (1080p+, bestvideo+bestaudio)",
                "1080p Öncelikli",
                "Hızlı (720p)"
            ],
            command=self._on_quality_change,
            width=360,
            height=32
        )
        self.quality_combo.pack(anchor="w", padx=16, pady=(0, 12))
        self._set_quality_combo_value()

        # Checkbox: Open explorer on done
        self.chk_explorer = ctk.CTkCheckBox(
            self.card_quality,
            text=t("settings.open_explorer"),
            font=ctk.CTkFont(size=12),
            fg_color="#6366F1",
            command=self._save_checkboxes
        )
        if self.settings.open_explorer_on_done:
            self.chk_explorer.select()
        self.chk_explorer.pack(anchor="w", padx=16, pady=(0, 8))

        # Checkbox: Notification on done
        self.chk_notify = ctk.CTkCheckBox(
            self.card_quality,
            text=t("settings.notify_done"),
            font=ctk.CTkFont(size=12),
            fg_color="#6366F1",
            command=self._save_checkboxes
        )
        if self.settings.notify_on_done:
            self.chk_notify.select()
        self.chk_notify.pack(anchor="w", padx=16, pady=(0, 14))

        # 3. Output Directory Card
        self.card_dir = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        self.card_dir.pack(fill="x", pady=(0, 12), padx=2)

        lbl_dir_title = ctk.CTkLabel(
            self.card_dir,
            text="Kayıt Klasörü",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F8FAFC"
        )
        lbl_dir_title.pack(anchor="w", padx=16, pady=(12, 6))

        dir_row = ctk.CTkFrame(self.card_dir, fg_color="transparent")
        dir_row.pack(fill="x", padx=16, pady=(0, 14))

        self.lbl_current_dir = ctk.CTkLabel(
            dir_row,
            text=self.settings.output_dir,
            font=ctk.CTkFont(size=12),
            text_color="#CBD5E1"
        )
        self.lbl_current_dir.pack(side="left")

        btn_browse = ctk.CTkButton(
            dir_row,
            text="Gözat...",
            width=70,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#334155",
            command=self._browse_dir
        )
        btn_browse.pack(side="right")

        # 4. Dependencies Card
        self.card_deps = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        self.card_deps.pack(fill="x", pady=(0, 12), padx=2)

        lbl_deps_title = ctk.CTkLabel(
            self.card_deps,
            text=t("settings.deps_title"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F8FAFC"
        )
        lbl_deps_title.pack(anchor="w", padx=16, pady=(12, 6))

        self.deps_container = ctk.CTkFrame(self.card_deps, fg_color="transparent")
        self.deps_container.pack(fill="x", padx=16, pady=(0, 8))
        self._populate_dependencies()

        self.engine_update_frame = ctk.CTkFrame(self.card_deps, fg_color="transparent")
        self.engine_update_frame.pack(fill="x", padx=16, pady=(0, 14))

        self.btn_update_engine = ctk.CTkButton(
            self.engine_update_frame,
            text="⚡ İndirme Motorunu Güncelle (yt-dlp)",
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#6366F1",
            hover_color="#4F46E5",
            command=self._on_click_update_engine
        )
        self.btn_update_engine.pack(side="left", padx=(0, 10))

        self.lbl_update_status = ctk.CTkLabel(
            self.engine_update_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        )
        self.lbl_update_status.pack(side="left")

        # 5. Language Card
        self.card_lang = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=10, border_width=1, border_color="#334155")
        self.card_lang.pack(fill="x", pady=(0, 12), padx=2)

        lbl_lang_title = ctk.CTkLabel(
            self.card_lang,
            text=t("settings.language_title"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F8FAFC"
        )
        lbl_lang_title.pack(anchor="w", padx=16, pady=(12, 6))

        self.lang_seg = ctk.CTkSegmentedButton(
            self.card_lang,
            values=["Türkçe", "English"],
            command=self._on_lang_switch
        )
        self.lang_seg.set("Türkçe" if get_language() == "tr" else "English")
        self.lang_seg.pack(anchor="w", padx=16, pady=(0, 14))

        self.refresh_session_status()
        register_listener(self._on_language_change)

    def refresh_session_status(self):
        if self.cookie_manager.is_authenticated:
            u = self.cookie_manager.username or "instagram"
            days = self.cookie_manager.days_remaining
            days_str = f" (~{days} gün kaldı)" if days is not None else ""
            self.lbl_session_status.configure(
                text=f"🟢 Oturum Açık (@{u}){days_str}",
                text_color="#10B981"
            )
            self.btn_logout.configure(state="normal")
        else:
            self.lbl_session_status.configure(
                text="🔴 Oturum Açık Değil",
                text_color="#EF4444"
            )
            self.btn_logout.configure(state="disabled")

    def _logout(self):
        self.cookie_manager.logout()
        self.refresh_session_status()

    def _browse_dir(self):
        f = filedialog.askdirectory(initialdir=self.settings.output_dir)
        if f:
            self.settings.output_dir = f
            self.settings.save()
            self.lbl_current_dir.configure(text=f)

    def _set_quality_combo_value(self):
        m = self.settings.quality_mode
        if m == "fast":
            self.quality_combo.set("Hızlı (720p)")
        elif m == "1080p":
            self.quality_combo.set("1080p Öncelikli")
        else:
            self.quality_combo.set("Maksimum Kalite (1080p+, bestvideo+bestaudio)")

    def _on_quality_change(self, choice: str):
        if "Hızlı" in choice:
            self.settings.quality_mode = "fast"
        elif "1080p Öncelikli" in choice:
            self.settings.quality_mode = "1080p"
        else:
            self.settings.quality_mode = "max"
        self.settings.save()

    def _save_checkboxes(self):
        self.settings.open_explorer_on_done = (self.chk_explorer.get() == 1)
        self.settings.notify_on_done = (self.chk_notify.get() == 1)
        self.settings.save()

    def _populate_dependencies(self):
        for widget in self.deps_container.winfo_children():
            widget.destroy()

        deps = check_all_dependencies()
        for name, info in deps.items():
            row = ctk.CTkFrame(self.deps_container, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            icon = "🟢" if info.available else "🔴"
            ver_text = f"v{info.version}" if info.version else ("Hazır" if info.available else "Eksik")
            
            lbl = ctk.CTkLabel(
                row,
                text=f"{icon} {name.ljust(12)} : {ver_text}",
                font=ctk.CTkFont(family="Consolas", size=12),
                text_color="#F8FAFC" if info.available else "#EF4444"
            )
            lbl.pack(side="left")

    def _on_click_update_engine(self):
        import threading
        from storysepeti.core.engine_updater import check_ytdlp_update, download_and_install_engine

        self.btn_update_engine.configure(state="disabled", text="Kontrol Ediliyor...")
        self.lbl_update_status.configure(text="En güncel motor sürümü sorgulanıyor...", text_color="#60A5FA")

        def worker():
            chk = check_ytdlp_update()
            latest = chk.get("latest_version", "")
            cur = chk.get("current_version", "")

            if chk.get("update_available"):
                self.after(0, lambda: self.lbl_update_status.configure(text=f"v{latest} indiriliyor...", text_color="#F59E0B"))
                def on_progress(pct, msg):
                    self.after(0, lambda: self.lbl_update_status.configure(text=msg))
                success = download_and_install_engine(progress_cb=on_progress)
                if success:
                    self.after(0, lambda: self.lbl_update_status.configure(text=f"✅ Başarıyla v{latest} sürümüne güncellendi!", text_color="#10B981"))
                else:
                    self.after(0, lambda: self.lbl_update_status.configure(text="❌ Güncelleme indirilemedi.", text_color="#EF4444"))
            else:
                self.after(0, lambda: self.lbl_update_status.configure(text=f"✅ İndirme motoru en güncel sürümde (v{cur}).", text_color="#10B981"))

            self.after(0, lambda: self.btn_update_engine.configure(state="normal", text="⚡ İndirme Motorunu Güncelle (yt-dlp)"))
            self.after(0, self._populate_dependencies)

        threading.Thread(target=worker, daemon=True).start()

    def _on_lang_switch(self, choice: str):
        lang = "tr" if choice == "Türkçe" else "en"
        set_language(lang)
        self.settings.language = lang
        self.settings.save()

    def _on_language_change(self):
        self.lbl_title.configure(text=t("settings.title"))
        self.btn_refresh.configure(text=t("settings.btn_refresh_cookie"))
        self.btn_logout.configure(text=t("settings.btn_logout"))
        self.lbl_quality_mode.configure(text=t("settings.quality_mode"))
        self.chk_explorer.configure(text=t("settings.open_explorer"))
        self.chk_notify.configure(text=t("settings.notify_done"))
        self.refresh_session_status()
