"""
Filename sanitization, template formatting, and collision avoidance for Windows.
"""

import re
from pathlib import Path
from typing import Optional

TR_MAP = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
FORBIDDEN_CHARS = r'[\/:*?"<>|\r\n\t]'

def sanitize_filename(name: str, max_length: int = 120) -> str:
    """
    Sanitizes string for Windows filesystem:
    - Transliterates Turkish characters
    - Removes forbidden Windows filesystem symbols
    - Trims dots and whitespaces
    """
    if not name:
        return "unnamed"
    # Convert Turkish chars
    s = name.translate(TR_MAP)
    # Remove forbidden chars
    s = re.sub(FORBIDDEN_CHARS, "_", s)
    # Collapse multiple underscores/spaces
    s = re.sub(r"[_\s]+", "_", s)
    # Strip leading/trailing dots and spaces
    s = s.strip(". _")
    if not s:
        s = "unnamed"
    return s[:max_length]

def get_unique_path(target_path: Path) -> Path:
    """
    If target_path exists, appends _v2, _v3, etc. to prevent accidental overwrites.
    """
    if not target_path.exists():
        return target_path
    
    parent = target_path.parent
    stem = target_path.stem
    suffix = target_path.suffix

    counter = 2
    while True:
        candidate = parent / f"{stem}_v{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
        if counter > 1000:
            return candidate

def format_media_filename(
    username: str,
    media_type: str, # "HL" for highlight, "ST" for story
    index: int,
    media_id: str,
    resolution: Optional[str] = None,
    ext: str = "mp4"
) -> str:
    u = sanitize_filename(username, 30)
    m_id = sanitize_filename(media_id, 30) if media_id else "media"
    res_part = f"_{resolution}" if resolution else ""
    extension = ext.lstrip(".")
    return f"{u}_{media_type}_{index:03d}_{m_id}{res_part}.{extension}"
