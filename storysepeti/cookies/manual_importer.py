"""
Netscape HTTP Cookie File Parser and Validator for Instagram.
"""

import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class ValidationResult:
    is_valid: bool
    username: Optional[str] = None
    user_id: Optional[str] = None
    expires_in_days: Optional[int] = None
    error_message: Optional[str] = None
    cookies: Optional[List[Dict[str, Any]]] = None

def parse_netscape_content(content: str) -> List[Dict[str, Any]]:
    """
    Parses Netscape cookie format string into structured cookie dictionaries.
    """
    cookies = []
    lines = content.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 7:
            domain, flag, path, secure, expiration, name, value = parts[:7]
            cookies.append({
                "domain": domain,
                "flag": flag.upper() == "TRUE",
                "path": path,
                "secure": secure.upper() == "TRUE",
                "expires": int(expiration) if expiration.isdigit() else 0,
                "name": name,
                "value": value
            })
    return cookies

def parse_netscape_file(file_path: Path) -> List[Dict[str, Any]]:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return parse_netscape_content(f.read())

def validate_instagram_cookies(cookies: List[Dict[str, Any]]) -> ValidationResult:
    """
    Validates if cookies contain essential Instagram authentication tokens:
    - sessionid
    - ds_user_id
    """
    if not cookies:
        return ValidationResult(is_valid=False, error_message="Cookie list is empty.")

    cookie_dict = {c["name"]: c for c in cookies if "instagram.com" in c.get("domain", "")}
    # In case domain is without dot
    if not cookie_dict:
        cookie_dict = {c["name"]: c for c in cookies}

    if "sessionid" not in cookie_dict:
        return ValidationResult(
            is_valid=False,
            error_message="Instagram 'sessionid' cookie not found in file."
        )

    session_cookie = cookie_dict["sessionid"]
    expires = session_cookie.get("expires", 0)
    current_time = int(time.time())

    days_left = None
    if expires and expires > 0:
        if expires < current_time:
            return ValidationResult(
                is_valid=False,
                error_message="Instagram session has already expired."
            )
        days_left = max(0, int((expires - current_time) / 86400))

    user_id = cookie_dict.get("ds_user_id", {}).get("value")
    # Some exports also contain 'username' or can be identified by user_id
    username = cookie_dict.get("username", {}).get("value") or user_id

    return ValidationResult(
        is_valid=True,
        username=username,
        user_id=user_id,
        expires_in_days=days_left,
        cookies=cookies
    )

def cookies_to_netscape_string(cookies: List[Dict[str, Any]]) -> str:
    """
    Converts list of cookie dicts back to standard Netscape file string.
    """
    lines = ["# Netscape HTTP Cookie File", "# https://curl.se/docs/http-cookies.html", ""]
    for c in cookies:
        domain = c.get("domain", ".instagram.com")
        flag = "TRUE" if c.get("flag", True) else "FALSE"
        path = c.get("path", "/")
        secure = "TRUE" if c.get("secure", True) else "FALSE"
        expires = str(c.get("expires", 0))
        name = c.get("name", "")
        value = c.get("value", "")
        if name and value:
            lines.append(f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}")
    return "\n".join(lines) + "\n"
