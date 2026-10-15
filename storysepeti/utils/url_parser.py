"""
Instagram URL Parser and Canonicalization Engine.
Identifies whether a given input is a single highlight, profile highlights, single story,
all active stories, or an encrypted/base64 short link (/s/...).
"""

import re
import base64
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class URLType(Enum):
    SINGLE_HIGHLIGHT = "SINGLE_HIGHLIGHT"
    PROFILE_HIGHLIGHTS = "PROFILE_HIGHLIGHTS"
    SINGLE_STORY = "SINGLE_STORY"
    USER_STORIES = "USER_STORIES"
    UNKNOWN = "UNKNOWN"

@dataclass
class URLParseResult:
    url_type: URLType
    canonical_url: str
    username: Optional[str] = None
    media_id: Optional[str] = None
    raw_input: str = ""

def decode_short_highlight_token(token: str) -> Optional[str]:
    """
    Decodes an Instagram /s/<token> short link.
    Example token: 'aGlnaGxpZ2h0OjE3ODY0OTM5MDYxNjQ0NTg0' -> 'highlight:17864939061644584'
    """
    try:
        padding = -len(token) % 4
        padded = token + ("=" * padding)
        decoded = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8", errors="ignore")
        match = re.search(r"highlight:(\d+)", decoded)
        if match:
            return match.group(1)
        if decoded.isdigit():
            return decoded
    except Exception:
        pass
    return None

def parse_url(input_str: str) -> URLParseResult:
    """
    Parses any Instagram URL or username string and returns normalized URL and metadata.
    """
    raw = (input_str or "").strip()
    if not raw:
        return URLParseResult(URLType.UNKNOWN, "", raw_input=raw)

    # 1. Short highlight link /s/<token>
    short_match = re.search(r"(?:https?://)?(?:www\.)?instagram\.com/s/([A-Za-z0-9_\-]+)", raw, re.IGNORECASE)
    if short_match:
        token = short_match.group(1)
        hl_id = decode_short_highlight_token(token)
        if hl_id:
            return URLParseResult(
                url_type=URLType.SINGLE_HIGHLIGHT,
                canonical_url=f"https://www.instagram.com/stories/highlights/{hl_id}/",
                media_id=hl_id,
                raw_input=raw
            )
        # Fallback to the short URL directly if decoding failed
        return URLParseResult(
            url_type=URLType.SINGLE_HIGHLIGHT,
            canonical_url=f"https://www.instagram.com/s/{token}",
            raw_input=raw
        )

    # 2. Canonical highlight: /stories/highlights/<id>/
    hl_match = re.search(r"(?:https?://)?(?:www\.)?instagram\.com/stories/highlights/(\d+)", raw, re.IGNORECASE)
    if hl_match:
        hl_id = hl_match.group(1)
        return URLParseResult(
            url_type=URLType.SINGLE_HIGHLIGHT,
            canonical_url=f"https://www.instagram.com/stories/highlights/{hl_id}/",
            media_id=hl_id,
            raw_input=raw
        )

    # 3. Single active story: /stories/<username>/<story_id>/
    single_story_match = re.search(r"(?:https?://)?(?:www\.)?instagram\.com/stories/([A-Za-z0-9._]+)/(\d+)", raw, re.IGNORECASE)
    if single_story_match:
        username = single_story_match.group(1)
        story_id = single_story_match.group(2)
        return URLParseResult(
            url_type=URLType.SINGLE_STORY,
            canonical_url=f"https://www.instagram.com/stories/{username}/{story_id}/",
            username=username,
            media_id=story_id,
            raw_input=raw
        )

    # 4. User active stories: /stories/<username>/ (without numeric story id)
    user_stories_match = re.search(r"(?:https?://)?(?:www\.)?instagram\.com/stories/([A-Za-z0-9._]+)/?(?:\?.*)?$", raw, re.IGNORECASE)
    if user_stories_match:
        username = user_stories_match.group(1)
        if username.lower() not in ("highlights", "explore"):
            return URLParseResult(
                url_type=URLType.USER_STORIES,
                canonical_url=f"https://www.instagram.com/stories/{username}/",
                username=username,
                raw_input=raw
            )

    # 5. User profile URL: instagram.com/<username>
    profile_match = re.search(r"(?:https?://)?(?:www\.)?instagram\.com/([A-Za-z0-9._]+)/?(?:\?.*)?$", raw, re.IGNORECASE)
    if profile_match:
        username = profile_match.group(1)
        excluded = {"p", "reel", "stories", "tv", "explore", "direct", "accounts"}
        if username.lower() not in excluded:
            return URLParseResult(
                url_type=URLType.PROFILE_HIGHLIGHTS,
                canonical_url=f"https://www.instagram.com/{username}/",
                username=username,
                raw_input=raw
            )

    # 6. Plain username or @username
    clean_username = raw.lstrip("@").strip()
    if re.match(r"^[A-Za-z0-9._]{1,30}$", clean_username):
        return URLParseResult(
            url_type=URLType.PROFILE_HIGHLIGHTS,
            canonical_url=f"https://www.instagram.com/{clean_username}/",
            username=clean_username,
            raw_input=raw
        )

    return URLParseResult(URLType.UNKNOWN, raw, raw_input=raw)
