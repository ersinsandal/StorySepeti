"""
Windows desktop notifications with non-blocking threaded execution.
"""

import threading

def _show_toast(title: str, message: str) -> None:
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(
            title=title,
            msg=message,
            duration=4,
            threaded=True
        )
    except Exception:
        # Fallback: ignore or silent fail if notification service is unavailable
        pass

def notify_desktop(title: str, message: str) -> None:
    """Dispatches a desktop notification without blocking the caller."""
    t = threading.Thread(target=_show_toast, args=(title, message), daemon=True)
    t.start()
