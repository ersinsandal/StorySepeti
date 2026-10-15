"""
Automated Desktop Browser Cookie Extractor.
Extracts Instagram session cookies from Chrome, Edge, Firefox, Brave, and Opera.
Handles database file locks and decrypts cookies safely.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class BrowserExtractionResult:
    success: bool
    cookies: Optional[List[Dict[str, Any]]] = None
    is_locked: bool = False
    error: Optional[str] = None

SUPPORTED_BROWSERS = ["all", "edge", "chrome", "firefox", "brave", "opera"]

def extract_cookies_from_browser(browser_name: str) -> BrowserExtractionResult:
    """
    Extracts Instagram cookies from the designated browser or scans all supported browsers.
    """
    b_name = (browser_name or "").lower().strip()

    if b_name in ("all", "tümü", "otomatik"):
        # Auto-scan Edge, Chrome, Firefox, Brave, Opera
        scan_order = ["edge", "chrome", "firefox", "brave", "opera"]
        last_res = None
        for b in scan_order:
            res = _extract_single_browser(b)
            if res.success:
                return res
            last_res = res
        return last_res or BrowserExtractionResult(
            success=False,
            error="Hiçbir tarayıcıda aktif bir Instagram oturumu bulunamadı."
        )

    return _extract_single_browser(b_name)

def _extract_single_browser(b_name: str) -> BrowserExtractionResult:
    # Try browser_cookie3
    try:
        import browser_cookie3
        extractor_fn = getattr(browser_cookie3, b_name, None)
        if not extractor_fn:
            return BrowserExtractionResult(
                success=False,
                error=f"Unsupported browser: {browser_name}"
            )
        
        try:
            cj = extractor_fn(domain_name="instagram.com")
            cookie_list = []
            for c in cj:
                cookie_list.append({
                    "domain": c.domain,
                    "flag": True,
                    "path": c.path,
                    "secure": c.secure,
                    "expires": int(c.expires) if c.expires else 0,
                    "name": c.name,
                    "value": c.value
                })
            
            if any(c["name"] == "sessionid" for c in cookie_list):
                return BrowserExtractionResult(success=True, cookies=cookie_list)
            else:
                return BrowserExtractionResult(
                    success=False,
                    error="No active Instagram session found in browser."
                )
        except Exception as e:
            err_str = str(e).lower()
            is_locked = any(w in err_str for w in ("locked", "busy", "permission", "sharing violation", "another process", "admin", "shadow"))
            return BrowserExtractionResult(
                success=False,
                is_locked=is_locked,
                error=str(e)
            )

    except ImportError:
        return BrowserExtractionResult(
            success=False,
            error="Browser extraction library is not available."
        )

def get_installed_browsers() -> List[str]:
    """Returns list of supported browsers."""
    return SUPPORTED_BROWSERS.copy()
