"""
Engine Updater for StorySepeti.
Allows automatic and in-app updating of yt-dlp download engine without requiring
technical knowledge, pip, or command-line commands from the user.
"""

import os
import sys
import json
import urllib.request
import subprocess
from pathlib import Path
from typing import Optional, Callable, Dict, Any

GITHUB_LATEST_RELEASE_API = "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"
GITHUB_EXE_DOWNLOAD_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"

def get_engines_dir() -> Path:
    """Returns local engines storage directory in APPDATA or portable directory."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        base_dir = Path(appdata) / "StorySepeti" / "engines"
    else:
        base_dir = Path("engines")
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir

def get_custom_ytdlp_path() -> Optional[Path]:
    """Returns path to standalone yt-dlp.exe if installed and valid."""
    p = get_engines_dir() / "yt-dlp.exe"
    if p.exists() and p.is_file() and p.stat().st_size > 1024 * 1024:
        return p
    return None

def get_current_ytdlp_version() -> str:
    """Returns current active version of yt-dlp engine."""
    custom_exe = get_custom_ytdlp_path()
    if custom_exe:
        try:
            res = subprocess.run([str(custom_exe), "--version"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass

    try:
        import yt_dlp.version
        return getattr(yt_dlp.version, "__version__", "unknown")
    except Exception:
        return "2026.08.19"

def get_ytdlp_command() -> list:
    """
    Returns command prefix to invoke yt-dlp.
    Prefers standalone updated yt-dlp.exe in engines directory; falls back to bundled module.
    """
    custom_exe = get_custom_ytdlp_path()
    if custom_exe:
        return [str(custom_exe)]
    return [sys.executable, "-m", "yt_dlp"]

def check_ytdlp_update() -> Dict[str, Any]:
    """
    Queries GitHub API to determine if a newer version of yt-dlp is available.
    """
    cur_ver = get_current_ytdlp_version()
    result = {
        "current_version": cur_ver,
        "latest_version": cur_ver,
        "update_available": False,
        "release_notes": "",
        "download_url": GITHUB_EXE_DOWNLOAD_URL
    }

    try:
        req = urllib.request.Request(
            GITHUB_LATEST_RELEASE_API,
            headers={
                "User-Agent": "StorySepeti-Engine-Updater/1.0",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        with urllib.request.urlopen(req, timeout=6) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                tag = data.get("tag_name", "").lstrip("v").strip()
                if tag:
                    result["latest_version"] = tag
                    result["release_notes"] = data.get("name", "")
                    if tag != cur_ver and cur_ver != "unknown":
                        # Compare release dates or strings (e.g. 2026.08.19)
                        if tag > cur_ver:
                            result["update_available"] = True
    except Exception as e:
        result["error"] = str(e)

    return result

def download_and_install_engine(
    progress_cb: Optional[Callable[[float, str], None]] = None
) -> bool:
    """
    Downloads the latest standalone yt-dlp.exe from GitHub releases with progress reporting.
    Installs it to the engines directory.
    """
    target_dir = get_engines_dir()
    target_file = target_dir / "yt-dlp.exe"
    temp_file = target_dir / "yt-dlp.exe.tmp"

    try:
        if progress_cb:
            progress_cb(0.05, "İndirme başlatılıyor...")

        req = urllib.request.Request(
            GITHUB_EXE_DOWNLOAD_URL,
            headers={"User-Agent": "StorySepeti-Engine-Updater/1.0"}
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 64 * 1024

            with open(temp_file, "wb") as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0 and progress_cb:
                        pct = min(0.95, downloaded / total_size)
                        mb_done = downloaded / (1024 * 1024)
                        mb_total = total_size / (1024 * 1024)
                        progress_cb(pct, f"İndiriliyor: {mb_done:.1f} MB / {mb_total:.1f} MB")

        # Verify temp file
        if temp_file.exists() and temp_file.stat().st_size > 1024 * 1024:
            # Overwrite final file
            if target_file.exists():
                try:
                    target_file.unlink()
                except Exception:
                    pass
            temp_file.replace(target_file)

            if progress_cb:
                progress_cb(1.0, "İndirme motoru başarıyla güncellendi!")
            return True
        else:
            if temp_file.exists():
                temp_file.unlink()
            return False

    except Exception as e:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass
        if progress_cb:
            progress_cb(0.0, f"Hata: {str(e)}")
        return False
