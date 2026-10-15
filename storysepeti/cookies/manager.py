"""
Unified Cookie Management for StorySepeti.
Provides session persistence, automatic/manual import, expiration tracking,
and secure on-the-fly temporary Netscape cookie files for external tools.
"""

import os
import atexit
import tempfile
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Generator

from .secure_store import (
    save_encrypted_cookies,
    load_encrypted_cookies,
    remove_encrypted_cookies
)
from .manual_importer import (
    parse_netscape_file,
    validate_instagram_cookies,
    cookies_to_netscape_string,
    ValidationResult
)
from .browser_extractor import (
    extract_cookies_from_browser,
    BrowserExtractionResult
)

_created_temp_files = []

def _cleanup_all_temp_files():
    for p in _created_temp_files:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass

atexit.register(_cleanup_all_temp_files)

class CookieManager:
    def __init__(self):
        self._cached_cookies: Optional[List[Dict[str, Any]]] = None
        self._cached_validation: Optional[ValidationResult] = None
        self._load_initial_session()

    def _load_initial_session(self) -> None:
        """Loads session from encrypted storage, or migrates local txt if present."""
        cookies = load_encrypted_cookies()
        if cookies:
            val = validate_instagram_cookies(cookies)
            if val.is_valid:
                self._cached_cookies = cookies
                self._cached_validation = val
                return

        # Fallback migration: check if instagram_cookies.txt exists in working dir
        local_txt = Path("instagram_cookies.txt")
        if local_txt.exists():
            try:
                txt_cookies = parse_netscape_file(local_txt)
                val = validate_instagram_cookies(txt_cookies)
                if val.is_valid:
                    self.save_cookies(txt_cookies)
            except Exception:
                pass

    @property
    def is_authenticated(self) -> bool:
        return self._cached_validation is not None and self._cached_validation.is_valid

    @property
    def username(self) -> Optional[str]:
        return self._cached_validation.username if self._cached_validation else None

    @property
    def cookie_dict(self) -> Dict[str, str]:
        if not self._cached_cookies:
            return {}
        return {c['name']: c['value'] for c in self._cached_cookies if 'name' in c and 'value' in c}

    @property
    def days_remaining(self) -> Optional[int]:
        return self._cached_validation.expires_in_days if self._cached_validation else None

    def save_cookies(self, cookies: List[Dict[str, Any]]) -> ValidationResult:
        val = validate_instagram_cookies(cookies)
        if val.is_valid:
            save_encrypted_cookies(cookies)
            self._cached_cookies = cookies
            self._cached_validation = val
        return val

    def import_txt_file(self, file_path: Path) -> ValidationResult:
        """Imports and encrypts cookies from a local Netscape cookie file."""
        try:
            cookies = parse_netscape_file(file_path)
            return self.save_cookies(cookies)
        except Exception as e:
            return ValidationResult(is_valid=False, error_message=str(e))

    def import_from_browser(self, browser_name: str) -> BrowserExtractionResult:
        """Extracts cookies from the specified browser and encrypts them if valid."""
        res = extract_cookies_from_browser(browser_name)
        if res.success and res.cookies:
            val = self.save_cookies(res.cookies)
            if not val.is_valid:
                return BrowserExtractionResult(
                    success=False,
                    error=val.error_message or "Extracted cookies were invalid."
                )
        return res

    def logout(self) -> None:
        remove_encrypted_cookies()
        self._cached_cookies = None
        self._cached_validation = None

    @contextmanager
    def temp_netscape_file(self) -> Generator[str, None, None]:
        """
        Creates a temporary Netscape formatted file for external subprocesses
        (yt-dlp, gallery-dl) and ensures it is promptly wiped from disk upon completion.
        """
        if not self._cached_cookies:
            raise RuntimeError("No active Instagram session available.")

        netscape_data = cookies_to_netscape_string(self._cached_cookies)
        fd, temp_path = tempfile.mkstemp(prefix="sv_cookie_", suffix=".txt")
        _created_temp_files.append(temp_path)
        
        try:
            with open(fd, "w", encoding="utf-8") as f:
                f.write(netscape_data)
            yield temp_path
        finally:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                if temp_path in _created_temp_files:
                    _created_temp_files.remove(temp_path)
            except Exception:
                pass
