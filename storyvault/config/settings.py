"""
Configuration and settings management for StoryVault.
Persists in %APPDATA%/StoryVault/settings.json.
"""

import os
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Literal

def get_app_dir() -> Path:
    app_data = os.environ.get("APPDATA")
    if app_data:
        base = Path(app_data) / "StoryVault"
    else:
        base = Path.home() / ".storyvault"
    base.mkdir(parents=True, exist_ok=True)
    return base

@dataclass
class AppSettings:
    output_dir: str = str(Path.home() / "Downloads" / "StoryVault")
    language: Literal["tr", "en"] = "tr"
    quality_mode: Literal["max", "1080p", "fast"] = "max"
    concurrent_fragments: int = 4
    open_explorer_on_done: bool = True
    notify_on_done: bool = True
    cookie_method: Literal["auto", "manual"] = "auto"
    last_browser: str = "chrome"

    @classmethod
    def load(cls) -> "AppSettings":
        settings_file = get_app_dir() / "settings.json"
        if not settings_file.exists():
            instance = cls()
            instance.save()
            return instance
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Filter unknown keys to avoid TypeError
            valid_keys = cls.__dataclass_fields__.keys()
            filtered = {k: v for k, v in data.items() if k in valid_keys}
            return cls(**filtered)
        except Exception:
            return cls()

    def save(self) -> None:
        settings_file = get_app_dir() / "settings.json"
        try:
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Settings] Error saving settings: {e}")
