"""
StoryVault - Desktop Application Launcher
Entry point supporting PyInstaller frozen execution, CLI delegation (-m yt_dlp / -m gallery_dl),
and global crash logging.
"""

import sys
import os
import multiprocessing
from pathlib import Path

# Windows PyInstaller multiprocessing guard
multiprocessing.freeze_support()

# Support executing sub-tools via `sys.executable -m <module>` in frozen environment
if len(sys.argv) > 2 and sys.argv[1] == "-m":
    module = sys.argv[2]
    cli_args = sys.argv[3:]
    if module in ("yt_dlp", "yt-dlp"):
        import yt_dlp
        sys.exit(yt_dlp.main(cli_args))
    elif module in ("gallery_dl", "gallery-dl"):
        import gallery_dl
        sys.argv = [sys.argv[0]] + cli_args
        sys.exit(gallery_dl.main())

# Crash logger wrapper to capture any early startup errors
def main():
    try:
        from storyvault.app import run
        run()
    except Exception as e:
        import traceback
        crash_log = Path("crash.log")
        with open(crash_log, "a", encoding="utf-8") as f:
            f.write("=== StoryVault Crash Log ===\n")
            traceback.print_exc(file=f)
            f.write("\n")
        raise

if __name__ == "__main__":
    main()
