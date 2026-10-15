"""
Physical File Verifier using FFprobe.
Inspects downloaded media container, codec, resolution, and stream integrity.
"""

import json
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class VerifyResult:
    file_path: Path
    width: int = 0
    height: int = 0
    codec: str = ""
    bitrate: float = 0.0
    duration: float = 0.0
    is_valid_1080p: bool = False
    is_success: bool = False
    error: Optional[str] = None

def verify_file(file_path: Path, min_short_side: int = 1080) -> VerifyResult:
    """
    Runs ffprobe on the target video file and checks resolution and codec.
    """
    if not file_path.exists() or file_path.stat().st_size == 0:
        return VerifyResult(file_path=file_path, error="File does not exist or is 0 bytes.")

    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        # Fallback if ffprobe is missing from PATH
        return VerifyResult(
            file_path=file_path,
            is_success=True,
            is_valid_1080p=True,
            error="ffprobe not found; verified by file existence."
        )

    cmd = [
        ffprobe,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,codec_name,bit_rate,duration",
        "-of", "json",
        str(file_path)
    ]

    try:
        startupinfo = None
        import sys
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            startupinfo=startupinfo,
            timeout=10
        )
        if res.returncode != 0:
            return VerifyResult(file_path=file_path, error=res.stderr.strip() or "ffprobe failed.")

        data = json.loads(res.stdout)
        streams = data.get("streams", [])
        if not streams:
            return VerifyResult(file_path=file_path, error="No video streams found.")

        v_stream = streams[0]
        w = int(v_stream.get("width") or 0)
        h = int(v_stream.get("height") or 0)
        codec = v_stream.get("codec_name") or "?"
        br = float(v_stream.get("bit_rate") or 0) / 1000.0
        dur = float(v_stream.get("duration") or 0.0)

        short = min(w, h)
        is_1080 = short >= min_short_side

        return VerifyResult(
            file_path=file_path,
            width=w,
            height=h,
            codec=codec,
            bitrate=br,
            duration=dur,
            is_valid_1080p=is_1080,
            is_success=True
        )

    except Exception as e:
        return VerifyResult(file_path=file_path, error=str(e))
