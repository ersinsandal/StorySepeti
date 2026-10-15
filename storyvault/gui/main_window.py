"""
Main Application Window for StoryVault.
Features a responsive sidebar, view router, live engine polling, and tray integration.
"""

import queue
import customtkinter as ctk
from typing import Optional

from storyvault.i18n import t, get_language, set_language, register_listener
from storyvault.config.settings import AppSettings
from storyvault.cookies.manager import CookieManager
from storyvault.core.downloader import DownloadEngine, EngineMessage
from storyvault.utils.url_parser import URLType

from .mode_selector import ModeSelector
from .download_panel import DownloadPanel
from .queue_panel import QueuePanel
from .settings_panel import SettingsPanel
from .login_wizard import LoginWizard
from .tray import SystemTrayApp
from .downloads_panel import DownloadsPanel

class MainWindow(ctk.CTk):
    def __init__(self, settings: AppSettings, cookie_manager: CookieManager):
        super().__init__()
        self.settings = settings
        self.cookie_manager = cookie_manager
        self.engine = DownloadEngine(cookie_manager, settings)

        # Window Setup
        self.title("StoryVault - Instagram Story & Highlight Downloader")
        self.geometry("980x660")
        self.minsize(860, 580)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color="#0B1120")

        # Root Grid Layout (Sidebar 220px | Main Content 1fr)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content_views()

        # System Tray setup
        self.tray = SystemTrayApp(
            on_show=self._show_from_tray,
            on_quit=self._quit_application
        )
        self.tray.start()

        # Window protocols
        self.protocol("WM_DELETE_WINDOW", self._on_close_requested)

        # Live engine message poll loop (runs every 100ms)
        self.after(100, self._poll_engine_messages)

        register_listener(self._on_language_change)

        # Initial view: Home Dashboard (Mode Selector)
        self._navigate_to("home")

        # Bring window to foreground
        self.lift()
        self.attributes("-topmost", True)
        self.after(300, lambda: self.attributes("-topmost", False))
        self.focus_force()

        # Check if first run and unauthenticated -> prompt wizard
        if not self.cookie_manager.is_authenticated:
            self.after(500, self.open_login_wizard)

        # Background engine update check
        self.after(2500, self._check_engine_updates_async)

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=220,
            corner_radius=0,
            fg_color="#0F172A",
            border_width=1,
            border_color="#1E293B"
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(7, weight=1) # Spacer

        # App Logo & Title
        self.lbl_logo = ctk.CTkLabel(
            self.sidebar,
            text="⚡ StoryVault",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F8FAFC"
        )
        self.lbl_logo.grid(row=0, column=0, padx=20, pady=(24, 2), sticky="w")

        self.lbl_version = ctk.CTkLabel(
            self.sidebar,
            text="v1.0.0 • Max Quality",
            font=ctk.CTkFont(size=11),
            text_color="#64748B"
        )
        self.lbl_version.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        # Navigation Buttons
        self.btn_nav_hl = ctk.CTkButton(
            self.sidebar,
            text="📦 " + t("nav.highlight"),
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            fg_color="#1E293B",
            hover_color="#334155",
            anchor="w",
            corner_radius=8,
            command=lambda: self._select_mode_and_navigate(URLType.SINGLE_HIGHLIGHT)
        )
        self.btn_nav_hl.grid(row=2, column=0, padx=12, pady=4, sticky="ew")

        self.btn_nav_story = ctk.CTkButton(
            self.sidebar,
            text="📱 " + t("nav.story"),
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            fg_color="#1E293B",
            hover_color="#334155",
            anchor="w",
            corner_radius=8,
            command=lambda: self._select_mode_and_navigate(URLType.USER_STORIES)
        )
        self.btn_nav_story.grid(row=3, column=0, padx=12, pady=4, sticky="ew")

        self.btn_nav_queue = ctk.CTkButton(
            self.sidebar,
            text="📋 " + t("nav.queue"),
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            fg_color="#1E293B",
            hover_color="#334155",
            anchor="w",
            corner_radius=8,
            command=lambda: self._navigate_to("queue")
        )
        self.btn_nav_queue.grid(row=4, column=0, padx=12, pady=4, sticky="ew")

        self.btn_nav_downloads = ctk.CTkButton(
            self.sidebar,
            text="📁 " + t("nav.downloads"),
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            fg_color="#1E293B",
            hover_color="#334155",
            anchor="w",
            corner_radius=8,
            command=lambda: self._navigate_to("downloads")
        )
        self.btn_nav_downloads.grid(row=5, column=0, padx=12, pady=4, sticky="ew")

        self.btn_nav_settings = ctk.CTkButton(
            self.sidebar,
            text="⚙️ " + t("nav.settings"),
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            fg_color="#1E293B",
            hover_color="#334155",
            anchor="w",
            corner_radius=8,
            command=lambda: self._navigate_to("settings")
        )
        self.btn_nav_settings.grid(row=6, column=0, padx=12, pady=4, sticky="ew")

        # Bottom Area in Sidebar: Session Status & Language Switcher
        self.bottom_sidebar = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.bottom_sidebar.grid(row=8, column=0, padx=12, pady=16, sticky="ew")
        self.bottom_sidebar.grid_columnconfigure(0, weight=1)

        # Session Status Pill Button (Click to open login wizard)
        self.btn_session_pill = ctk.CTkButton(
            self.bottom_sidebar,
            text="",
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#0F172A",
            border_width=1,
            border_color="#334155",
            hover_color="#1E293B",
            command=self.open_login_wizard
        )
        self.btn_session_pill.pack(fill="x", pady=(0, 10))
        self.refresh_session_pill()

        # Language Toggle [TR | EN]
        self.btn_lang_toggle = ctk.CTkButton(
            self.bottom_sidebar,
            text="🌐 " + ("English" if get_language() == "tr" else "Türkçe"),
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#1E293B",
            hover_color="#334155",
            command=self._toggle_language
        )
        self.btn_lang_toggle.pack(fill="x")

    def _build_content_views(self):
        self.right_wrapper = ctk.CTkFrame(self, fg_color="transparent")
        self.right_wrapper.grid(row=0, column=1, sticky="nsew", padx=20, pady=16)
        self.right_wrapper.grid_columnconfigure(0, weight=1)
        self.right_wrapper.grid_rowconfigure(1, weight=1)

        # Update notification banner (hidden by default)
        self.update_banner = ctk.CTkFrame(
            self.right_wrapper,
            fg_color="#1E1B4B",
            corner_radius=8,
            border_width=1,
            border_color="#4F46E5"
        )
        self.lbl_banner_text = ctk.CTkLabel(
            self.update_banner,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#C7D2FE"
        )
        self.lbl_banner_text.pack(side="left", padx=16, pady=8)

        self.btn_banner_update = ctk.CTkButton(
            self.update_banner,
            text="Şimdi Güncelle",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#6366F1",
            hover_color="#4F46E5",
            height=26,
            width=100,
            command=self._perform_banner_update
        )
        self.btn_banner_update.pack(side="right", padx=(4, 12), pady=6)

        self.btn_banner_dismiss = ctk.CTkButton(
            self.update_banner,
            text="✕",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color="#312E81",
            height=26,
            width=26,
            command=lambda: self.update_banner.grid_forget()
        )
        self.btn_banner_dismiss.pack(side="right", padx=(0, 4), pady=6)

        self.content_container = ctk.CTkFrame(self.right_wrapper, fg_color="transparent")
        self.content_container.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)

        # 1. Home / Mode Selector
        self.view_home = ModeSelector(
            self.content_container,
            on_select_mode=self._select_mode_and_navigate
        )

        # 2. Download Panel
        self.view_download = DownloadPanel(
            self.content_container,
            engine=self.engine,
            settings=self.settings,
            on_back=lambda: self._navigate_to("home")
        )

        # 3. Queue Panel
        self.view_queue = QueuePanel(
            self.content_container,
            engine=self.engine
        )

        # 4. Downloads Panel
        self.view_downloads = DownloadsPanel(
            self.content_container,
            settings=self.settings
        )

        # 5. Settings Panel
        self.view_settings = SettingsPanel(
            self.content_container,
            settings=self.settings,
            cookie_manager=self.cookie_manager,
            on_open_wizard=self.open_login_wizard
        )

    def _navigate_to(self, view_name: str):
        for v in (self.view_home, self.view_download, self.view_queue, self.view_downloads, self.view_settings):
            v.grid_forget()

        if view_name == "home":
            self.view_home.grid(row=0, column=0, sticky="nsew")
        elif view_name == "download":
            self.view_download.grid(row=0, column=0, sticky="nsew")
        elif view_name == "queue":
            self.view_queue.refresh()
            self.view_queue.grid(row=0, column=0, sticky="nsew")
        elif view_name == "downloads":
            self.view_downloads.refresh()
            self.view_downloads.grid(row=0, column=0, sticky="nsew")
        elif view_name == "settings":
            self.view_settings.refresh_session_status()
            self.view_settings.grid(row=0, column=0, sticky="nsew")

    def _select_mode_and_navigate(self, mode: URLType):
        self.view_download.set_mode(mode)
        self._navigate_to("download")

    def open_login_wizard(self):
        wizard = LoginWizard(
            self,
            cookie_manager=self.cookie_manager,
            on_success=self._on_login_success
        )

    def _on_login_success(self):
        self.refresh_session_pill()
        self.view_settings.refresh_session_status()
        self.view_download.log_panel.log("success", f"Instagram oturumu açıldı (@{self.cookie_manager.username})")

    def refresh_session_pill(self):
        if self.cookie_manager.is_authenticated:
            u = self.cookie_manager.username or "user"
            self.btn_session_pill.configure(
                text=f"🟢 @{u}",
                text_color="#10B981",
                border_color="#065F46"
            )
        else:
            self.btn_session_pill.configure(
                text="🔴 Oturum Aç",
                text_color="#EF4444",
                border_color="#991B1B"
            )

    def _toggle_language(self):
        new_lang = "en" if get_language() == "tr" else "tr"
        set_language(new_lang)
        self.settings.language = new_lang
        self.settings.save()

    def _on_language_change(self):
        self.btn_nav_hl.configure(text="📦 " + t("nav.highlight"))
        self.btn_nav_story.configure(text="📱 " + t("nav.story"))
        self.btn_nav_queue.configure(text="📋 " + t("nav.queue"))
        self.btn_nav_downloads.configure(text="📁 " + t("nav.downloads"))
        self.btn_nav_settings.configure(text="⚙️ " + t("nav.settings"))
        self.btn_lang_toggle.configure(text="🌐 " + ("English" if get_language() == "tr" else "Türkçe"))
        self.refresh_session_pill()

    def _poll_engine_messages(self):
        """Polls engine queue and feeds logs, progress, and card updates."""
        try:
            while not self.engine.message_queue.empty():
                msg = self.engine.message_queue.get_nowait()
                if msg.msg_type == "log":
                    lvl = msg.data.get("level", "info")
                    text = msg.data.get("message", "")
                    self.view_download.log_panel.log(lvl, text)
                elif msg.msg_type == "progress":
                    pct = msg.data.get("progress", 0.0)
                    speed = msg.data.get("speed", "")
                    self.view_download.progress_widget.update_progress(pct, detail=speed, stage="İndiriliyor...")
                elif msg.msg_type in ("status_change", "task_added", "finished"):
                    self.view_queue.refresh()
                    if msg.msg_type == "finished":
                        self.view_download.progress_widget.reset()
                        self.view_downloads.refresh()
        except Exception:
            pass
        finally:
            self.after(100, self._poll_engine_messages)

    def _show_from_tray(self):
        self.after(0, self.deiconify)
        self.after(0, self.lift)

    def _on_close_requested(self):
        # Cleanly quit application
        self._quit_application()

    def _quit_application(self):
        self.tray.stop()
        self.engine.shutdown()
        self.destroy()

    def _check_engine_updates_async(self):
        import threading
        from storyvault.core.engine_updater import check_ytdlp_update

        def worker():
            chk = check_ytdlp_update()
            if chk.get("update_available"):
                lat = chk.get("latest_version", "")
                self.after(0, lambda: self._show_update_banner(lat))

        threading.Thread(target=worker, daemon=True).start()

    def _show_update_banner(self, latest_ver: str):
        self._latest_engine_ver = latest_ver
        self.lbl_banner_text.configure(
            text=f"⚡ StoryVault İndirme Motoru Güncellemesi Mevcut (v{latest_ver}) - Instagram uyumluluğu için güncellemeniz önerilir."
        )
        self.update_banner.grid(row=0, column=0, sticky="ew", pady=(0, 8))

    def _perform_banner_update(self):
        import threading
        from storyvault.core.engine_updater import download_and_install_engine

        self.btn_banner_update.configure(state="disabled", text="İndiriliyor...")

        def worker():
            def on_prog(pct, msg):
                self.after(0, lambda: self.lbl_banner_text.configure(text=f"⚡ Motor Güncelleniyor: {msg}"))

            ok = download_and_install_engine(progress_cb=on_prog)
            if ok:
                self.after(0, lambda: self.lbl_banner_text.configure(text="✅ İndirme motoru başarıyla güncellendi!"))
                self.after(3000, lambda: self.update_banner.grid_forget())
            else:
                self.after(0, lambda: self.lbl_banner_text.configure(text="❌ Motor güncellemesi başarısız oldu."))
                self.after(0, lambda: self.btn_banner_update.configure(state="normal", text="Tekrar Dene"))

        threading.Thread(target=worker, daemon=True).start()

