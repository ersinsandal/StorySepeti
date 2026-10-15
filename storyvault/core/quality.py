"""
Instagram Media Quality Analysis and Stream Selection Engine.
Selects optimal formats with strict 1080p+ short-side rules and DASH stream handling.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

@dataclass
class VideoFormatInfo:
    width: int
    height: int
    codec: str
    bitrate: float
    is_audio: bool
    protocol: str
    format_id: str

@dataclass
class MediaReport:
    index: int
    media_id: str
    has_hq: bool
    selected_width: int
    selected_height: int
    selected_codec: str
    selected_bitrate: float
    audio_only_available: bool
    available_formats: List[VideoFormatInfo]

def is_video_format(fmt: Dict[str, Any]) -> bool:
    vcodec = fmt.get("vcodec")
    if not vcodec or vcodec == "none":
        return False
    width = fmt.get("width")
    height = fmt.get("height")
    return isinstance(width, (int, float)) and isinstance(height, (int, float))

def is_audio_only(fmt: Dict[str, Any]) -> bool:
    vcodec = fmt.get("vcodec")
    acodec = fmt.get("acodec")
    return (vcodec == "none" or not vcodec) and bool(acodec and acodec != "none")

def short_side(fmt: Dict[str, Any]) -> int:
    w = int(fmt.get("width") or 0)
    h = int(fmt.get("height") or 0)
    return min(w, h)

def format_bitrate(fmt: Dict[str, Any]) -> float:
    return float(fmt.get("tbr") or fmt.get("vbr") or 0)

def format_filesize(fmt: Dict[str, Any]) -> int:
    return int(fmt.get("filesize") or fmt.get("filesize_approx") or 0)

def quality_key(fmt: Dict[str, Any]) -> Tuple[int, int, float, int]:
    w = int(fmt.get("width") or 0)
    h = int(fmt.get("height") or 0)
    pixels = w * h
    return (short_side(fmt), pixels, format_bitrate(fmt), format_filesize(fmt))

def analyze_formats(info: Dict[str, Any], min_short_side: int = 1080) -> List[MediaReport]:
    """
    Analyzes all video entries in a yt-dlp single-json dump.
    Returns structured quality reports for each playlist item.
    """
    entries = info.get("entries")
    if entries is None:
        # Single entry (not a playlist)
        entries = [info]

    reports: List[MediaReport] = []

    for fallback_idx, entry in enumerate(entries, start=1):
        if not entry:
            continue

        index = entry.get("playlist_index") or fallback_idx
        video_id = entry.get("id") or f"item_{index}"
        formats = entry.get("formats") or []

        video_formats = [f for f in formats if is_video_format(f)]
        audio_formats = [f for f in formats if is_audio_only(f)]

        if not video_formats:
            continue

        video_formats.sort(key=quality_key, reverse=True)
        best = video_formats[0]

        best_w = int(best.get("width") or 0)
        best_h = int(best.get("height") or 0)
        best_codec = best.get("vcodec") or "?"
        best_br = format_bitrate(best)

        hq_formats = [f for f in video_formats if short_side(f) >= min_short_side]
        has_hq = len(hq_formats) > 0

        selected = hq_formats[0] if has_hq else best
        selected_w = int(selected.get("width") or 0)
        selected_h = int(selected.get("height") or 0)
        selected_codec = selected.get("vcodec") or "?"
        selected_br = format_bitrate(selected)

        fmt_list = []
        for f in video_formats:
            fmt_list.append(VideoFormatInfo(
                width=int(f.get("width") or 0),
                height=int(f.get("height") or 0),
                codec=f.get("vcodec") or "?",
                bitrate=format_bitrate(f),
                is_audio=f.get("acodec") not in (None, "none"),
                protocol=f.get("protocol") or "?",
                format_id=str(f.get("format_id", ""))
            ))

        reports.append(MediaReport(
            index=index,
            media_id=video_id,
            has_hq=has_hq,
            selected_width=selected_w,
            selected_height=selected_h,
            selected_codec=selected_codec,
            selected_bitrate=selected_br,
            audio_only_available=len(audio_formats) > 0,
            available_formats=fmt_list
        ))

    return reports

def build_format_selector(quality_mode: str = "max") -> str:
    """
    Returns yt-dlp format selector string based on chosen quality preference.
    """
    if quality_mode == "fast":
        return (
            "bestvideo[width>=720][height>=720]+bestaudio/"
            "bestvideo[width>=720][height>=720]/"
            "best[width>=720][height>=720]/"
            "bestvideo+bestaudio/best"
        )
    # Default is "max" / "1080p"
    return (
        "bestvideo[width>=1080][height>=1080]+bestaudio/"
        "bestvideo[width>=1080][height>=1080]/"
        "best[width>=1080][height>=1080]/"
        "bestvideo+bestaudio/best"
    )
