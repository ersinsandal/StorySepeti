"""
Live Interactive Instagram Browser Login for StorySepeti.
Opens an automated, clean browser window (Chrome or Edge) to Instagram login.
Monitors the session until user successfully logs in, automatically captures cookies,
and closes the browser without requiring any extensions or file handling.
"""

import time
import threading
from typing import List, Dict, Any, Callable, Optional

def _create_driver():
    """Tries creating Chrome driver first; falls back to Edge if Chrome is not available."""
    # 1. Try Chrome
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        opts = ChromeOptions()
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        driver = webdriver.Chrome(options=opts)
        return driver, "Chrome"
    except Exception:
        pass

    # 2. Try Edge
    try:
        from selenium import webdriver
        from selenium.webdriver.edge.options import Options as EdgeOptions
        opts = EdgeOptions()
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        driver = webdriver.Edge(options=opts)
        return driver, "Edge"
    except Exception as e:
        raise RuntimeError(f"Tarayıcı başlatılamadı: {e}")

def run_live_browser_login(
    on_status: Callable[[str], None],
    on_success: Callable[[List[Dict[str, Any]]], None],
    on_error: Callable[[str], None],
    timeout_seconds: int = 300
) -> None:
    """
    Runs in a background thread. Launches interactive browser and watches for login.
    """
    driver = None
    try:
        on_status("Tarayıcı penceresi açılıyor...")
        driver, b_name = _create_driver()

        on_status(f"Instagram açılıyor ({b_name})... Lütfen açılan pencerede hesabınıza giriş yapın.")
        driver.get("https://www.instagram.com/accounts/login/")

        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            try:
                # Check current cookies
                raw_cookies = driver.get_cookies()
                has_session = any(c.get("name") == "sessionid" and c.get("value") for c in raw_cookies)
                has_user = any(c.get("name") == "ds_user_id" and c.get("value") for c in raw_cookies)

                if has_session and has_user:
                    on_status("Giriş tespit edildi! Çerezler güvenle alınıyor...")
                    time.sleep(1) # Allow any last token to settle
                    raw_cookies = driver.get_cookies()

                    # Convert to standard format
                    cookie_list = []
                    for c in raw_cookies:
                        cookie_list.append({
                            "domain": c.get("domain", ".instagram.com"),
                            "flag": True,
                            "path": c.get("path", "/"),
                            "secure": c.get("secure", True),
                            "expires": int(c.get("expiry", 0) or 0),
                            "name": c.get("name", ""),
                            "value": c.get("value", "")
                        })

                    driver.quit()
                    driver = None
                    on_success(cookie_list)
                    return

            except Exception as e:
                err_str = str(e).lower()
                if "no such window" in err_str or "target window already closed" in err_str:
                    on_error("Giriş penceresi kullanıcı tarafından kapatıldı.")
                    return

            time.sleep(1)

        # Timeout reached
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        on_error("Giriş zaman aşımına uğradı (5 dakika içinde giriş yapılmadı).")

    except Exception as e:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        on_error(f"Hata oluştu: {str(e)}")
