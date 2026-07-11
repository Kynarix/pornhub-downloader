
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SETTINGS_PATH = DATA_DIR / "settings.json"

THEMES = [
    {"id": "ph", "label": "Pornhub", "accent": "#ff9000", "preview": ["#000000", "#ff9000"]},
    {"id": "crimson", "label": "Crimson", "accent": "#e02424", "preview": ["#0a0000", "#e02424"]},
    {"id": "azure", "label": "Azure", "accent": "#1a73e8", "preview": ["#0f1419", "#1a73e8"]},
    {"id": "mint", "label": "Mint", "accent": "#00bfa5", "preview": ["#071412", "#00bfa5"]},
    {"id": "violet", "label": "Violet", "accent": "#7c4dff", "preview": ["#0d0a14", "#7c4dff"]},
    {"id": "sand", "label": "Sand", "accent": "#f4a261", "preview": ["#12100e", "#f4a261"]},
]

DEFAULTS: dict[str, Any] = {
    "download_dir": str(Path.home() / "Downloads" / "HubDownloader"),
    "concurrent_downloads": 1,
    "theme": "crimson",
    "appearance": "light",
    "animations": True,
    "auto_best_quality": True,
}


class Settings:
    def __init__(self, path: Path = SETTINGS_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data = dict(DEFAULTS)
        self.load()

    def load(self) -> None:
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    self._data.update(loaded)
            except (json.JSONDecodeError, OSError):
                pass
        # migrate old theme values
        if self._data.get("theme") in ("light", "dark"):
            self._data["appearance"] = self._data["theme"]
            self._data["theme"] = "ph"
        Path(self._data["download_dir"]).mkdir(parents=True, exist_ok=True)
        self.save()

    def save(self) -> None:
        self.path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        if key == "download_dir":
            Path(str(value)).mkdir(parents=True, exist_ok=True)
        self.save()

    def update(self, patch: dict[str, Any]) -> dict[str, Any]:
        for key, value in (patch or {}).items():
            if key in DEFAULTS or key in self._data:
                if key == "concurrent_downloads":
                    try:
                        value = max(1, min(4, int(value)))
                    except (TypeError, ValueError):
                        value = 1
                if key == "theme" and value not in {t["id"] for t in THEMES}:
                    continue
                if key == "appearance" and value not in ("dark", "light"):
                    continue
                if key in ("animations", "auto_best_quality"):
                    value = bool(value)
                self._data[key] = value
                if key == "download_dir":
                    Path(str(value)).mkdir(parents=True, exist_ok=True)
        self.save()
        return self.to_dict()

    def to_dict(self) -> dict[str, Any]:
        data = dict(self._data)
        data["themes"] = THEMES
        return data
