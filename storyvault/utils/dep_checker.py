"""
Dependency checker for external tools: ffmpeg, ffprobe, yt-dlp, and gallery-dl.
Checks tools directly and avoids unnecessary child process spawning on startup.
"""

import sys
import shutil
import subprocess
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class DependencyInfo:
    name: str
    available: bool
    version: Optional[str] = None
    install_hint: str = ""
    path: Optional[str] = None

def _run_cli_version(cmd: list) -> Optional[str]:
    try:
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            startupinfo=startupinfo,
            timeout=5
        )
        if res.returncode == 0:
            first_line = (res.stdout or res.stderr or "").splitlines()
            return first_line[0].strip() if first_line else "OK"
    except Exception:
        pass
    return None

def check_all_dependencies() -> Dict[str, DependencyInfo]:
    results = {}

    # 1. FFmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    ffmpeg_ver = _run_cli_version(["ffmpeg", "-version"]) if ffmpeg_path else None
    results["ffmpeg"] = DependencyInfo(
        name="ffmpeg",
        available=bool(ffmpeg_path and ffmpeg_ver),
        version=ffmpeg_ver.split()[2] if (ffmpeg_ver and len(ffmpeg_ver.split()) >= 3) else ffmpeg_ver,
        install_hint="winget install Gyan.FFmpeg",
        path=ffmpeg_path
    )

    # 2. FFprobe
    ffprobe_path = shutil.which("ffprobe")
    ffprobe_ver = _run_cli_version(["ffprobe", "-version"]) if ffprobe_path else None
    results["ffprobe"] = DependencyInfo(
        name="ffprobe",
        available=bool(ffprobe_path and ffprobe_ver),
        version=ffprobe_ver.split()[2] if (ffprobe_ver and len(ffprobe_ver.split()) >= 3) else ffprobe_ver,
        install_hint="winget install Gyan.FFmpeg",
        path=ffprobe_path
    )

    # 3. yt-dlp (Direct module inspection)
    try:
        import yt_dlp
        yt_ver = getattr(yt_dlp.version, "__version__", "OK")
        yt_avail = True
    except Exception:
        yt_ver = None
        yt_avail = False

    results["yt-dlp"] = DependencyInfo(
        name="yt-dlp",
        available=yt_avail,
        version=str(yt_ver) if yt_ver else None,
        install_hint="pip install -U yt-dlp",
        path=sys.executable
    )

    # 4. gallery-dl (Direct module inspection)
    try:
        import gallery_dl
        gdl_ver = getattr(gallery_dl, "__version__", "OK")
        gdl_avail = True
    except Exception:
        gdl_ver = None
        gdl_avail = False

    results["gallery-dl"] = DependencyInfo(
        name="gallery-dl",
        available=gdl_avail,
        version=str(gdl_ver) if gdl_ver else None,
        install_hint="pip install -U gallery-dl",
        path=sys.executable
    )

    return results
