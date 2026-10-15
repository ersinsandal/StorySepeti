"""
Windows System Tray Integration for StorySepeti.
Allows minimizing the app to tray and managing it from the taskbar.
"""

import threading
from typing import Callable, Optional
from PIL import Image, ImageDraw

try:
    import pystray
    from pystray import MenuItem as item
except ImportError:
    pystray = None

def _create_default_tray_icon() -> Image.Image:
    # 64x64 icon with modern purple gradient circle and 'SV' lettermark
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    # Background circle
    draw.ellipse((4, 4, 60, 60), fill=(99, 102, 241, 255))
    # Inner border
    draw.ellipse((8, 8, 56, 56), outline=(255, 255, 255, 200), width=2)
    return image

class SystemTrayApp:
    def __init__(
        self,
        on_show: Callable[[], None],
        on_quit: Callable[[], None],
        custom_icon_path: Optional[str] = None
    ):
        self.on_show = on_show
        self.on_quit = on_quit
        self.custom_icon_path = custom_icon_path
        self._icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if not pystray:
            return

        image = _create_default_tray_icon()
        menu = pystray.Menu(
            item("StorySepeti'ı Aç", self._action_show, default=True),
            item("Çıkış", self._action_quit)
        )

        self._icon = pystray.Icon("StorySepeti", image, "StorySepeti", menu)
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def _action_show(self, icon, item):
        self.on_show()

    def _action_quit(self, icon, item):
        self.stop()
        self.on_quit()

    def stop(self) -> None:
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None
