"""
Application entry point and initialization lifecycle for StorySepeti.
"""

import sys
import os
from pathlib import Path

# Ensure root directory is on sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from storysepeti.config.settings import AppSettings
from storysepeti.cookies.manager import CookieManager
from storysepeti.i18n import set_language
from storysepeti.gui.main_window import MainWindow

def run():
    # 1. Load persistent user settings
    settings = AppSettings.load()

    # 2. Configure active UI language
    set_language(settings.language)

    # 3. Initialize secure cookie manager
    cookie_manager = CookieManager()

    # 4. Create and start main GUI
    app = MainWindow(settings=settings, cookie_manager=cookie_manager)
    app.mainloop()

if __name__ == "__main__":
    run()
