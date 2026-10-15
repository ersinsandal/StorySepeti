"""
Instagram Highlight Downloader and Inspector.
Executes multi-stage high quality extraction:
Stage 1: Photos via gallery-dl (original dimensions)
Stage 2: Format analysis via yt-dlp metadata dump
Stage 3: Video extraction via yt-dlp with true 1080p+ stream rules
Stage 4: Verification via FFprobe
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

from .quality import analyze_formats, build_format_selector
from .verifier import verify_file
from .engine_updater import get_ytdlp_command
from storysepeti.utils.file_namer import sanitize_filename

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ".mov"}

def run_subprocess_with_progress(
    cmd: List[str],
    log_cb: Optional[Callable[[str, str], None]] = None,
    progress_cb: Optional[Callable[[float, str], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None
) -> int:
    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        startupinfo=startupinfo,
        bufsize=1
    )

    if process.stdout:
        for line in process.stdout:
            if cancel_check and cancel_check():
                process.terminate()
                return -1

            line_str = line.strip()
            if not line_str:
                continue

            # Check for yt-dlp download progress
            # Example: [download]  67.3% of  245.12MiB at  3.21MiB/s ETA 00:45
            if "[download]" in line_str and "%" in line_str:
                try:
                    parts = line_str.split()
                    for p in parts:
                        if p.endswith("%"):
                            pct = float(p.rstrip("%"))
                            if progress_cb:
                                progress_cb(pct, line_str)
                            break
                except Exception:
                    pass
            elif "[DL]" in line_str or "[INDIRILIYOR]" in line_str or "before_dl" in line_str:
                if log_cb:
                    log_cb("info", line_str)
            else:
                if log_cb and ("error" in line_str.lower() or "warning" in line_str.lower()):
                    log_cb("warning" if "warning" in line_str.lower() else "error", line_str)

    process.wait()
    return process.returncode

def list_user_highlights(
    username: str,
    cookie_path: str,
    log_cb: Optional[Callable[[str, str], None]] = None
) -> List[Dict[str, Any]]:
    """
    Fetches all highlight albums belonging to a user using yt-dlp or gallery-dl.
    Returns list of dicts: {"id": str, "title": str, "url": str, "count": int}
    """
    clean_user = username.lstrip("@").strip()
    profile_url = f"https://www.instagram.com/{clean_user}/"

    if log_cb:
        log_cb("info", f"Highlight'lar taranıyor: @{clean_user}...")

    cmd = get_ytdlp_command() + [
        "--no-update",
        "--ignore-config",
        "--cookies",
        cookie_path,
        "--flat-playlist",
        "--dump-single-json",
        "--skip-download",
        "--no-warnings",
        profile_url
    ]

    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            startupinfo=startupinfo,
            timeout=30
        )
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout)
            entries = data.get("entries") or []
            highlights = []
            for item in entries:
                url = item.get("url") or ""
                title = item.get("title") or item.get("id") or "Highlight"
                hl_id = str(item.get("id") or "")
                if "highlights" in url or "highlight" in str(item.get("_type", "")):
                    highlights.append({
                        "id": hl_id,
                        "title": title,
                        "url": url if url.startswith("http") else f"https://www.instagram.com/stories/highlights/{hl_id}/",
                        "count": item.get("playlist_count") or 0
                    })
            if highlights:
                return highlights
    except Exception as e:
        if log_cb:
            log_cb("warning", f"Profil tarama uyarısı: {e}")

    # Fallback: Return single pseudo item for the user's highlights
    return [{
        "id": "all",
        "title": f"Tüm Highlight'lar (@{clean_user})",
        "url": f"https://www.instagram.com/{clean_user}/",
        "count": 0
    }]

def download_highlight(
    url: str,
    output_dir: Path,
    cookie_path: str,
    log_cb: Optional[Callable[[str, str], None]] = None,
    progress_cb: Optional[Callable[[float, str], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
    quality_mode: str = "max",
    concurrent_fragments: int = 4
) -> bool:
    """
    Downloads a single highlight album (photos and videos).
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. PHOTOS STAGE (gallery-dl)
    if log_cb:
        log_cb("info", "[1/4] Fotoğraflar gallery-dl ile orijinal kalitede taranıyor...")

    photo_cmd = [
        sys.executable,
        "-m",
        "gallery_dl",
        "--cookies", cookie_path,
        "--directory", str(output_dir),
        "-o", "extractor.instagram.videos=false",
        "--retries", "8",
        url
    ]
    run_subprocess_with_progress(photo_cmd, log_cb=None, cancel_check=cancel_check)

    if cancel_check and cancel_check():
        return False

    # 2. FORMAT ANALYSIS STAGE (yt-dlp)
    if log_cb:
        log_cb("info", "[2/4] Video sürümleri ve DASH manifestleri analiz ediliyor...")

    analysis_cmd = get_ytdlp_command() + [
        "--no-update",
        "--ignore-config",
        "--cookies", cookie_path,
        "--yes-playlist",
        "--dump-single-json",
        "--skip-download",
        "--no-warnings",
        url
    ]

    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    res = subprocess.run(
        analysis_cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        startupinfo=startupinfo
    )

    if res.returncode != 0:
        if log_cb:
            log_cb("error", f"Highlight metadata alınamadı: {res.stderr.strip()[:200]}")
        return False

    try:
        info_data = json.loads(res.stdout)
    except Exception:
        if log_cb:
            log_cb("error", "Metadata JSON çıktısı okunamadı.")
        return False

    reports = analyze_formats(info_data, min_short_side=1080 if quality_mode != "fast" else 720)
    hq_reports = [r for r in reports if r.has_hq] if quality_mode != "fast" else reports

    if not reports:
        if log_cb:
            log_cb("info", "Highlight albümünde video bulunamadı (sadece fotoğraf olabilir).")
        return True

    if log_cb:
        log_cb("success", f"Bulunan video: {len(reports)} adet | 1080P+ video: {len(hq_reports)} adet")

    # 3. VIDEO DOWNLOAD STAGE (yt-dlp)
    if log_cb:
        log_cb("info", f"[3/4] Videolar en yüksek kalitede indiriliyor (Eşzamanlı parça: {concurrent_fragments})...")

    indices = ",".join(str(r.index) for r in (hq_reports if hq_reports else reports))
    format_selector = build_format_selector(quality_mode)
    output_template = str(output_dir / "%(title).50s_HL_%(playlist_index)03d_%(id)s_%(resolution)s.%(ext)s")

    dl_cmd = get_ytdlp_command() + [
        "--no-update",
        "--ignore-config",
        "--cookies", cookie_path,
        "--yes-playlist",
        "--playlist-items", indices,
        "--ignore-errors",
        "--check-formats",
        "--format-sort-force",
        "-S", "res,br",
        "-f", format_selector,
        "--merge-output-format", "mkv",
        "--retries", "10",
        "--fragment-retries", "10",
        "--concurrent-fragments", str(concurrent_fragments),
        "--windows-filenames",
        "--print", "before_dl:[DL] %(playlist_index)s | %(id)s | %(resolution)s",
        "-o", output_template,
        url
    ]

    ret = run_subprocess_with_progress(
        dl_cmd,
        log_cb=log_cb,
        progress_cb=progress_cb,
        cancel_check=cancel_check
    )

    if cancel_check and cancel_check():
        return False

    # 4. PHYSICAL VERIFICATION STAGE (ffprobe)
    if log_cb:
        log_cb("info", "[4/4] İndirilen dosyalar FFprobe ile doğrulanıyor...")

    verified_count = 0
    target_reports = hq_reports if hq_reports else reports

    for r in target_reports:
        matched_file = None
        for f in output_dir.iterdir():
            if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS and r.media_id in f.name:
                matched_file = f
                break
        if matched_file:
            v_res = verify_file(matched_file, min_short_side=1080 if quality_mode != "fast" else 720)
            if v_res.is_success and v_res.is_valid_1080p:
                verified_count += 1
                if log_cb:
                    log_cb("success", f"Doğrulandı: {matched_file.name} ({v_res.width}x{v_res.height}, {v_res.codec})")
            else:
                if log_cb:
                    log_cb("warning", f"Doğrulama: {matched_file.name} ({v_res.width}x{v_res.height})")

    if log_cb:
        log_cb("success", f"Highlight indirme tamamlandı! Doğrulanan video sayısı: {verified_count}/{len(target_reports)}")

    return True
