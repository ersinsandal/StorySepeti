"""
Interactive Instagram Session Wizard for StorySepeti.
Guides user through automated browser extraction or manual Netscape TXT upload.
"""

import threading
import webbrowser
from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk
from typing import Callable, Optional

from storysepeti.i18n import t, register_listener
from storysepeti.cookies.manager import CookieManager
from storysepeti.cookies.browser_extractor import get_installed_browsers

class LoginWizard(ctk.CTkToplevel):
    def __init__(self, master, cookie_manager: CookieManager, on_success: Optional[Callable[[], None]] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.cookie_manager = cookie_manager
        self.on_success = on_success

        self.title("StorySepeti - Instagram Oturum Kurulumu")
        self.geometry("640x540")
        self.resizable(False, False)
        self.configure(fg_color="#0F172A")

        # Keep on top
        self.attributes("-topmost", True)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header Banner
        self.header_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=0, height=70)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.lbl_title = ctk.CTkLabel(
            self.header_frame,
            text=t("wizard.title"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#F8FAFC"
        )
        self.lbl_title.pack(anchor="w", padx=20, pady=(12, 2))

        self.lbl_sub = ctk.CTkLabel(
            self.header_frame,
            text=t("wizard.subtitle"),
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        )
        self.lbl_sub.pack(anchor="w", padx=20, pady=(0, 10))

        # Main Container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=1, column=0, sticky="nsew", padx=20, pady=16)
        self.container.grid_columnconfigure(0, weight=1)

        # Tabs: Automatic vs Manual
        self.tabview = ctk.CTkTabview(
            self.container,
            fg_color="#1E293B",
            segmented_button_fg_color="#0F172A",
            segmented_button_selected_color="#6366F1",
            corner_radius=10
        )
        self.tabview.pack(fill="both", expand=True)

        self.tab_auto = self.tabview.add("⚡ " + t("wizard.method_auto"))
        self.tab_manual = self.tabview.add("📄 " + t("wizard.method_manual"))

        self._build_auto_tab()
        self._build_manual_tab()

        # Status / Feedback Bar at bottom
        self.status_frame = ctk.CTkFrame(self, fg_color="#0B1120", height=45)
        self.status_frame.grid(row=2, column=0, sticky="ew")
        self.status_frame.grid_columnconfigure(0, weight=1)

        self.lbl_status = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#CBD5E1"
        )
        self.lbl_status.pack(side="left", padx=20, pady=10)

        self.btn_finish = ctk.CTkButton(
            self.status_frame,
            text="Ana Ekrana Geç",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            width=120,
            height=28,
            command=self._finish_and_close
        )
        # Hidden until success

        register_listener(self._on_language_change)

    def _build_auto_tab(self):
        self.tab_auto.grid_columnconfigure(0, weight=1)

        # Primary Method: Interactive Live Browser Login
        card_live = ctk.CTkFrame(self.tab_auto, fg_color="#0F172A", corner_radius=8, border_width=1, border_color="#4F46E5")
        card_live.pack(fill="x", padx=16, pady=(12, 10))

        lbl_live_title = ctk.CTkLabel(
            card_live,
            text="🌐 Tek Tıkla Giriş Yap (Önerilen & En Kolay)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#F8FAFC"
        )
        lbl_live_title.pack(anchor="w", padx=14, pady=(10, 4))

        lbl_live_desc = ctk.CTkLabel(
            card_live,
            text=(
                "Butona bastığınızda güvenli bir Instagram penceresi açılır.\n"
                "Kullanıcı adı ve şifrenizle giriş yaptığınız anda pencere otomatik kapanır\n"
                "ve oturumunuz doğrudan StorySepeti'a aktarılır. Hiçbir dosyayla uğraşmazsınız."
            ),
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8",
            justify="left"
        )
        lbl_live_desc.pack(anchor="w", padx=14, pady=(0, 10))

        self.btn_live_login = ctk.CTkButton(
            card_live,
            text="🌐 Giriş Penceresini Aç ve Bağlan",
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#6366F1",
            hover_color="#4F46E5",
            command=self._start_live_browser_login
        )
        self.btn_live_login.pack(fill="x", padx=14, pady=(0, 12))

        # Secondary Method: Extract from open browser
        card_step2 = ctk.CTkFrame(self.tab_auto, fg_color="#0F172A", corner_radius=8, border_width=1, border_color="#334155")
        card_step2.pack(fill="x", padx=16, pady=(0, 10))

        lbl_s2 = ctk.CTkLabel(
            card_step2,
            text="⚡ Alternatif: Mevcut Tarayıcıdan Aktar",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#CBD5E1"
        )
        lbl_s2.pack(anchor="w", padx=14, pady=(8, 2))

        row_b = ctk.CTkFrame(card_step2, fg_color="transparent")
        row_b.pack(fill="x", padx=14, pady=(0, 8))

        self.combo_browser = ctk.CTkComboBox(
            row_b,
            values=["Tüm Tarayıcılar (Otomatik)", "Edge", "Chrome", "Firefox", "Brave", "Opera"],
            width=220,
            height=30
        )
        self.combo_browser.set("Tüm Tarayıcılar (Otomatik)")
        self.combo_browser.pack(side="left", padx=(0, 8))

        self.btn_extract = ctk.CTkButton(
            row_b,
            text="⚡ Aktar",
            height=30,
            width=90,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            command=self._start_browser_extraction
        )
        self.btn_extract.pack(side="left")

        # Fallback quick helper frame
        self.fallback_frame = ctk.CTkFrame(self.tab_auto, fg_color="transparent")
        self.fallback_frame.pack(fill="x", padx=16, pady=(0, 6))

        btn_ext_help = ctk.CTkButton(
            self.fallback_frame,
            text="🛒 Get cookies.txt Eklentisini Aç",
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#1E293B",
            hover_color="#334155",
            command=lambda: webbrowser.open("https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc")
        )
        btn_ext_help.pack(side="left", padx=(0, 8))

        btn_txt_quick = ctk.CTkButton(
            self.fallback_frame,
            text="📁 TXT Dosyası Seç...",
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#1E293B",
            hover_color="#334155",
            command=self._pick_manual_file
        )
        btn_txt_quick.pack(side="left")

    def _start_live_browser_login(self):
        from storysepeti.cookies.live_browser_login import run_live_browser_login

        self.btn_live_login.configure(state="disabled", text="Pencere Açılıyor...")
        self.lbl_status.configure(text="🌐 Instagram giriş penceresi hazırlanıyor...", text_color="#60A5FA")

        def on_status(msg):
            self.after(0, lambda: self.lbl_status.configure(text=msg, text_color="#60A5FA"))

        def on_success(cookies):
            def apply_success():
                val = self.cookie_manager.save_cookies(cookies)
                self.btn_live_login.configure(state="normal", text="🌐 Giriş Penceresini Aç ve Bağlan")
                if val.is_valid:
                    u = val.username or "instagram_user"
                    days = val.expires_in_days
                    days_str = f" (~{days} gün geçerli)" if days is not None else ""
                    self.lbl_status.configure(
                        text=f"✅ Oturum Açıldı! Hesap: @{u}{days_str}",
                        text_color="#10B981"
                    )
                    self.btn_finish.configure(text="StorySepeti'u Kullanmaya Başla")
                    self.btn_finish.pack(side="right", padx=16, pady=8)
                else:
                    self.lbl_status.configure(text=f"❌ Çerez doğrulama hatası: {val.error_message}", text_color="#EF4444")
            self.after(0, apply_success)

        def on_error(err_msg):
            def apply_err():
                self.btn_live_login.configure(state="normal", text="🌐 Giriş Penceresini Aç ve Bağlan")
                self.lbl_status.configure(text=f"⚠️ {err_msg}", text_color="#F59E0B")
            self.after(0, apply_err)

        threading.Thread(
            target=run_live_browser_login,
            args=(on_status, on_success, on_error),
            daemon=True
        ).start()

    def _build_manual_tab(self):
        self.tab_manual.grid_columnconfigure(0, weight=1)

        # Guide Steps Card
        guide_card = ctk.CTkFrame(self.tab_manual, fg_color="#0F172A", corner_radius=8, border_width=1, border_color="#334155")
        guide_card.pack(fill="x", padx=16, pady=(12, 12))

        lbl_g_title = ctk.CTkLabel(
            guide_card,
            text="📋 Cookie Dosyası Nasıl Alınır? (Rehber)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#F8FAFC"
        )
        lbl_g_title.pack(anchor="w", padx=12, pady=(10, 4))

        guide_text = (
            "1. Tarayıcınıza 'Get cookies.txt LOCALLY' eklentisini kurun.\n"
            "2. instagram.com'a gidin ve hesabınıza normal şekilde giriş yapın.\n"
            "3. Eklenti simgesine tıklayıp 'Export' butonu ile txt dosyasını kaydedin.\n"
            "4. Aşağıdaki butonla indirdiğiniz txt dosyasını seçin."
        )
        lbl_steps = ctk.CTkLabel(
            guide_card,
            text=guide_text,
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8",
            justify="left"
        )
        lbl_steps.pack(anchor="w", padx=12, pady=(0, 10))

        # File Select Button
        self.btn_pick_file = ctk.CTkButton(
            self.tab_manual,
            text="📁 Cookie TXT Dosyasını Seç...",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#6366F1",
            hover_color="#4F46E5",
            command=self._pick_manual_file
        )
        self.btn_pick_file.pack(fill="x", padx=16, pady=(0, 10))

    def _start_browser_extraction(self):
        raw_b = self.combo_browser.get()
        if "Tüm" in raw_b or "all" in raw_b.lower():
            b_name = "all"
            status_text = "🔄 Tüm tarayıcılar (Edge, Chrome, Firefox...) taranıyor..."
        else:
            b_name = raw_b.lower()
            status_text = f"🔄 {raw_b} çerezleri taranıyor..."

        self.btn_extract.configure(state="disabled", text="Taranıyor...")
        self.lbl_status.configure(text=status_text, text_color="#60A5FA")

        def worker():
            res = self.cookie_manager.import_from_browser(b_name)
            self.after(0, lambda: self._handle_extraction_result(res))

        threading.Thread(target=worker, daemon=True).start()

    def _handle_extraction_result(self, res):
        self.btn_extract.configure(state="normal", text="⚡ Giriş Yaptım, Oturumu Aktar")
        if res.success:
            u = self.cookie_manager.username or "instagram_user"
            days = self.cookie_manager.days_remaining
            days_str = f" | Kalan süre: ~{days} gün" if days is not None else ""
            self.lbl_status.configure(
                text=f"✅ Başarılı! Hesap: @{u}{days_str}",
                text_color="#10B981"
            )
            self.btn_finish.configure(text="StorySepeti'u Kullanmaya Başla")
            self.btn_finish.pack(side="right", padx=16, pady=8)
        else:
            if res.is_locked:
                self.lbl_status.configure(
                    text="⚠️ Tarayıcı açık olduğu için dosya kilitli. Lütfen tarayıcıyı kapatıp tekrar deneyin veya aşağıdaki eklenti butonunu kullanın.",
                    text_color="#F59E0B"
                )
            else:
                self.lbl_status.configure(
                    text="ℹ️ Tarayıcılarda açık Instagram oturumu bulunamadı. Lütfen 1. Adımdan giriş yapın veya eklenti yöntemini kullanın.",
                    text_color="#F59E0B"
                )

    def _pick_manual_file(self):
        path = filedialog.askopenfilename(
            title="Instagram Cookie TXT Dosyasını Seç",
            filetypes=[("Text Dosyaları", "*.txt"), ("Tüm Dosyalar", "*.*")]
        )
        if not path:
            return

        self.lbl_status.configure(text="🔍 Dosya doğrulanıyor...", text_color="#60A5FA")
        val = self.cookie_manager.import_txt_file(Path(path))

        if val.is_valid:
            u = val.username or "instagram_user"
            days = val.expires_in_days
            days_str = f" | Kalan süre: ~{days} gün" if days is not None else ""
            self.lbl_status.configure(
                text=f"✅ Geçerli Cookie! Hesap: @{u}{days_str}",
                text_color="#10B981"
            )
            self.btn_finish.pack(side="right", padx=16, pady=8)
        else:
            self.lbl_status.configure(
                text=f"❌ Hata: {val.error_message or 'Geçersiz cookie dosyası.'}",
                text_color="#EF4444"
            )

    def _finish_and_close(self):
        if self.on_success:
            self.on_success()
        self.destroy()

    def _on_language_change(self):
        self.lbl_title.configure(text=t("wizard.title"))
        self.lbl_sub.configure(text=t("wizard.subtitle"))
