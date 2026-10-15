"""
Instagram Active Story Downloader (24-Hour Stories).
Supports both single active story item links and all active stories of a given user.
Uses direct Instagram Web API with curl_cffi for highest-speed native downloads,
capturing original photo resolutions and 60fps MP4 video streams, with fallback.
"""

import re
import sys
import time
import datetime
import subprocess
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List

from curl_cffi import requests

from .highlight import run_subprocess_with_progress
from .quality import build_format_selector
from .verifier import verify_file
from .engine_updater import get_ytdlp_command
from storysepeti.utils.url_parser import parse_url, URLType
from storysepeti.utils.file_namer import sanitize_filename, get_unique_path
from storysepeti.cookies.manual_importer import parse_netscape_file

MEDIA_EXTENSIONS = {".mp4", ".mkv", ".webm", ".mov", ".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ".mov"}

def _get_cookie_dict(cookie_dict: Optional[Dict[str, str]], cookie_path: str) -> Dict[str, str]:
    if cookie_dict:
        return cookie_dict
    if cookie_path and Path(cookie_path).exists():
        try:
            raw_list = parse_netscape_file(Path(cookie_path))
            return {c["name"]: c["value"] for c in raw_list if "name" in c and "value" in c}
        except Exception:
            pass
    return {}

def download_active_stories_native(
    url: str,
    output_dir: Path,
    cookie_dict: Dict[str, str],
    is_single: bool = False,
    username: str = "",
    log_cb: Optional[Callable[[str, str], None]] = None,
    progress_cb: Optional[Callable[[float, str], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None
) -> bool:
    """
    Downloads active stories directly via Instagram's web API.
    Bypasses broken legacy endpoints used by external scrapers.
    """
    parsed = parse_url(url)
    target_user = parsed.username or username.lstrip("@").strip()
    single_sid = parsed.media_id

    # If single_sid wasn't found by parse_url, check regex
    if not single_sid:
        sid_match = re.search(r'/stories/[^/?#]+/(\d+)', url)
        if sid_match:
            single_sid = sid_match.group(1)

    session = requests.Session(impersonate="chrome124")
    headers = {
        "X-IG-App-ID": "936619743392459",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Referer": "https://www.instagram.com/",
        "Accept": "*/*",
    }
    if "csrftoken" in cookie_dict:
        headers["X-CSRFToken"] = cookie_dict["csrftoken"]

    story_ids: List[str] = []

    if single_sid:
        story_ids = [single_sid]
        if log_cb:
            log_cb("info", f"[Tek Story] Hedef Story ID: {single_sid}")
    else:
        if not target_user:
            if log_cb:
                log_cb("error", "Geçerli bir kullanıcı adı veya story bağlantısı bulunamadı.")
            return False

        if log_cb:
            log_cb("info", f"[Tüm Aktif Story'ler] @{target_user} profili taranıyor...")

        story_page_url = f"https://www.instagram.com/stories/{target_user}/"
        try:
            r = session.get(story_page_url, headers=headers, cookies=cookie_dict, allow_redirects=True, timeout=15)
        except Exception as e:
            if log_cb:
                log_cb("error", f"Instagram bağlantı hatası: {e}")
            return False

        if "/accounts/login" in r.url or r.status_code in (401, 403):
            if log_cb:
                log_cb("error", "Instagram oturum çerezi geçersiz veya süresi dolmuş. Lütfen oturumunuzu yenileyin.")
            return False

        if r.status_code == 404:
            if log_cb:
                log_cb("error", f"@{target_user} kullanıcısı bulunamadı.")
            return False

        # Extract active story PKs from HTML
        pks = re.findall(r'"pk":"?(\d{18,20})"?', r.text)
        url_sids = re.findall(r'/stories/[^/?#]+/(\d{18,20})', r.text)

        seen = set()
        for sid in (pks + url_sids):
            if sid not in seen:
                seen.add(sid)
                story_ids.append(sid)

    if not story_ids:
        if log_cb:
            log_cb("warning", f"@{target_user or 'Kullanıcı'} için aktif story bulunamadı (Tüm story'lerin süresi dolmuş olabilir).")
        return False

    total_count = len(story_ids)
    if log_cb:
        log_cb("info", f"İndirilecek toplam story: {total_count}")

    downloaded_files: List[Path] = []

    for idx, sid in enumerate(story_ids):
        if cancel_check and cancel_check():
            if log_cb:
                log_cb("warning", "İndirme işlemi kullanıcı tarafından durduruldu.")
            return False

        info_url = f"https://www.instagram.com/api/v1/media/{sid}/info/"
        try:
            r_info = session.get(info_url, headers=headers, cookies=cookie_dict, timeout=12)
        except Exception as e:
            if log_cb:
                log_cb("warning", f"Story ({sid}) bilgisi alınamadı: {e}")
            continue

        if r_info.status_code != 200:
            if r_info.status_code in (400, 404):
                if log_cb:
                    log_cb("warning", f"Story ({sid}) silinmiş veya erişim izniniz yok.")
            continue

        try:
            data = r_info.json()
            items = data.get("items", [])
            if not items:
                continue
            item = items[0]
        except Exception:
            continue

        media_type = item.get("media_type") # 1: photo, 2: video
        uploader = item.get("user", {}).get("username") or target_user or "instagram"
        taken_at = item.get("taken_at") or int(time.time())
        date_str = datetime.datetime.fromtimestamp(taken_at).strftime("%Y%m%d")

        if media_type == 1:
            # PHOTO
            candidates = item.get("image_versions2", {}).get("candidates", [])
            if not candidates:
                continue
            candidates.sort(key=lambda c: int(c.get("width") or 0) * int(c.get("height") or 0), reverse=True)
            best_photo = candidates[0]
            dl_url = best_photo.get("url")
            w = best_photo.get("width") or ""
            h = best_photo.get("height") or ""
            res_str = f"_{w}x{h}" if w and h else ""

            target_name = f"{uploader}_ST_{date_str}_{sid}{res_str}.jpg"
            target_file = get_unique_path(output_dir / target_name)

            if log_cb:
                log_cb("info", f"[{idx+1}/{total_count}] Fotoğraf indiriliyor: {w}x{h}")

            try:
                r_dl = session.get(dl_url, timeout=20)
                if r_dl.status_code == 200:
                    with open(target_file, "wb") as f:
                        f.write(r_dl.content)
                    downloaded_files.append(target_file)
                    if log_cb:
                        log_cb("success", f"✅ İndirildi: {target_file.name}")
                    if progress_cb:
                        pct = (idx + 1) / total_count * 100.0
                        progress_cb(pct, f"{(idx+1)}/{total_count} tamamlandı")
            except Exception as e:
                if log_cb:
                    log_cb("error", f"Fotoğraf indirme hatası ({sid}): {e}")

        elif media_type == 2:
            # VIDEO
            videos = item.get("video_versions", [])
            if not videos:
                continue
            videos.sort(key=lambda v: int(v.get("width") or 0) * int(v.get("height") or 0), reverse=True)
            best_vid = videos[0]
            dl_url = best_vid.get("url")
            w = best_vid.get("width") or ""
            h = best_vid.get("height") or ""
            res_str = f"_{w}x{h}" if w and h else ""

            target_name = f"{uploader}_ST_{date_str}_{sid}{res_str}.mp4"
            target_file = get_unique_path(output_dir / target_name)

            if log_cb:
                log_cb("info", f"[{idx+1}/{total_count}] Video indiriliyor: {w}x{h}")

            try:
                r_dl = session.get(dl_url, stream=True, timeout=25)
                if r_dl.status_code == 200:
                    total_bytes = int(r_dl.headers.get("content-length") or 0)
                    downloaded_bytes = 0
                    start_t = time.time()

                    with open(target_file, "wb") as f:
                        for chunk in r_dl.iter_content(chunk_size=65536):
                            if cancel_check and cancel_check():
                                break
                            if chunk:
                                f.write(chunk)
                                downloaded_bytes += len(chunk)
                                if progress_cb and total_bytes > 0:
                                    elapsed = max(time.time() - start_t, 0.01)
                                    speed_mb = (downloaded_bytes / (1024 * 1024)) / elapsed
                                    chunk_pct = (downloaded_bytes / total_bytes)
                                    overall_pct = ((idx + chunk_pct) / total_count) * 100.0
                                    progress_cb(overall_pct, f"{speed_mb:.1f} MB/s")

                    if cancel_check and cancel_check():
                        if target_file.exists():
                            target_file.unlink()
                        return False

                    v_res = verify_file(target_file, min_short_side=720)
                    downloaded_files.append(target_file)
                    if log_cb:
                        log_cb("success", f"✅ İndirildi: {target_file.name} ({v_res.width}x{v_res.height})")
                    if progress_cb:
                        pct = (idx + 1) / total_count * 100.0
                        progress_cb(pct, f"{(idx+1)}/{total_count} tamamlandı")
            except Exception as e:
                if log_cb:
                    log_cb("error", f"Video indirme hatası ({sid}): {e}")

    if downloaded_files:
        if log_cb:
            log_cb("success", f"Aktif story indirme tamamlandı! ({len(downloaded_files)} adet medya kaydedildi)")
        return True

    return False

def download_active_stories(
    url: str,
    output_dir: Path,
    cookie_path: str,
    is_single: bool = False,
    username: str = "",
    log_cb: Optional[Callable[[str, str], None]] = None,
    progress_cb: Optional[Callable[[float, str], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
    quality_mode: str = "max",
    concurrent_fragments: int = 4,
    cookie_dict: Optional[Dict[str, str]] = None
) -> bool:
    """
    Downloads active stories for a user or a specific active story URL.
    Attempts native high-speed API first. Falls back to external tools if needed.
    """
    target_dir = output_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    c_dict = _get_cookie_dict(cookie_dict, cookie_path)

    # 1. Native Direct Download Attempt
    try:
        success = download_active_stories_native(
            url=url,
            output_dir=target_dir,
            cookie_dict=c_dict,
            is_single=is_single,
            username=username,
            log_cb=log_cb,
            progress_cb=progress_cb,
            cancel_check=cancel_check
        )
        if success:
            return True
    except Exception as e:
        if log_cb:
            log_cb("warning", f"Doğrudan indirme yöntemi hatası: {e}. Yedek motor devreye alınıyor...")

    if cancel_check and cancel_check():
        return False

    # 2. Fallback using gallery-dl + yt-dlp
    mode_label = "Tek Story" if is_single else "Tüm Aktif Story'ler"
    if log_cb:
        log_cb("info", f"[{mode_label}] Yedek motor başlatılıyor: {url}")

    initial_files = set(target_dir.iterdir()) if target_dir.exists() else set()
    login_error_detected = False

    def wrapped_log_cb(level: str, msg: str):
        nonlocal login_error_detected
        msg_lower = msg.lower()
        if "you need to log in" in msg_lower or "use --cookies" in msg_lower:
            login_error_detected = True
            return
        if "warning: your yt-dlp version" in msg_lower or "older than 90 days" in msg_lower:
            return
        if log_cb:
            log_cb(level, msg)

    # PHOTOS (gallery-dl)
    photo_cmd = [
        sys.executable,
        "-m",
        "gallery_dl",
        "--cookies", cookie_path,
        "--directory", str(target_dir),
        "-o", "extractor.instagram.videos=false",
        "--retries", "4",
        url
    ]
    run_subprocess_with_progress(photo_cmd, log_cb=wrapped_log_cb, cancel_check=cancel_check)

    if cancel_check and cancel_check():
        return False

    # VIDEOS (yt-dlp)
    format_selector = build_format_selector(quality_mode)
    output_template = str(target_dir / "%(uploader).30s_ST_%(upload_date>%Y%m%d)s_%(id)s_%(resolution)s.%(ext)s")

    dl_cmd = get_ytdlp_command() + [
        "--no-update",
        "--ignore-config",
        "--cookies", cookie_path,
        "--check-formats",
        "--format-sort-force",
        "-S", "res,br",
        "-f", format_selector,
        "--merge-output-format", "mkv",
        "--retries", "6",
        "--fragment-retries", "6",
        "--concurrent-fragments", str(concurrent_fragments),
        "--windows-filenames",
        "--print", "before_dl:[DL] %(id)s | %(resolution)s",
        "-o", output_template,
        url
    ]

    run_subprocess_with_progress(
        dl_cmd,
        log_cb=wrapped_log_cb,
        progress_cb=progress_cb,
        cancel_check=cancel_check
    )

    if cancel_check and cancel_check():
        return False

    current_files = set(target_dir.iterdir())
    new_files = [f for f in (current_files - initial_files) if f.is_file() and f.suffix.lower() in MEDIA_EXTENSIONS]
    all_media = [f for f in target_dir.iterdir() if f.is_file() and f.suffix.lower() in MEDIA_EXTENSIONS]

    if not new_files and not all_media:
        if login_error_detected:
            if log_cb:
                log_cb("error", "Instagram oturumu başarısız oldu: Çerezler geçersiz veya story'ye erişim izni yok.")
            return False
        if log_cb:
            log_cb("warning", "Bu bağlantıda indirilebilecek aktif story bulunamadı.")
        return False

    if log_cb:
        log_cb("success", f"Aktif story indirme tamamlandı! ({len(all_media)} adet medya hazır)")

    return True
