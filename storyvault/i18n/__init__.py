"""
Internationalization (i18n) system for StoryVault.
Provides instantaneous language switching with subscriber callbacks.
"""

import json
from pathlib import Path
from typing import Callable, Dict, List

_current_lang: str = "tr"
_translations: Dict[str, str] = {}
_callbacks: List[Callable[[], None]] = []

def _load_translations(lang: str) -> Dict[str, str]:
    path = Path(__file__).parent / f"{lang}.json"
    if not path.exists():
        path = Path(__file__).parent / "tr.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def set_language(lang: str) -> None:
    global _current_lang, _translations
    _current_lang = lang if lang in ("tr", "en") else "tr"
    _translations = _load_translations(_current_lang)
    for cb in _callbacks:
        try:
            cb()
        except Exception:
            pass

def get_language() -> str:
    return _current_lang

def register_listener(cb: Callable[[], None]) -> None:
    """Register a UI widget or panel callback to update its text on language toggle."""
    if cb not in _callbacks:
        _callbacks.append(cb)

def unregister_listener(cb: Callable[[], None]) -> None:
    if cb in _callbacks:
        _callbacks.remove(cb)

def t(key: str, **kwargs) -> str:
    """Translate a key into the active language, with optional format arguments."""
    global _translations
    if not _translations:
        _translations = _load_translations(_current_lang)
    text = _translations.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text

# Initialize on import
_translations = _load_translations(_current_lang)
