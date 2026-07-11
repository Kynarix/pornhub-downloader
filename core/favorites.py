
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from core.settings import DATA_DIR


class FavoritesStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (DATA_DIR / "favorites.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._items: list[dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self._items = data
            except (json.JSONDecodeError, OSError):
                self._items = []
        else:
            self.save()

    def save(self) -> None:
        self.path.write_text(
            json.dumps(self._items, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def list(self) -> list[dict[str, Any]]:
        return list(self._items)

    def ids(self) -> set[str]:
        return {str(i.get("id") or i.get("url")) for i in self._items}

    def has(self, item_id: str) -> bool:
        return any(str(i.get("id")) == str(item_id) for i in self._items)

    def add(self, item: dict[str, Any]) -> dict[str, Any]:
        item_id = str(item.get("id") or "")
        if not item_id:
            return {"ok": False, "error": "id gerekli"}
        # upsert
        self._items = [i for i in self._items if str(i.get("id")) != item_id]
        row = {
            "id": item_id,
            "title": item.get("title") or "",
            "url": item.get("url") or "",
            "thumbnail": item.get("thumbnail") or "",
            "duration": item.get("duration"),
            "duration_text": item.get("duration_text") or "",
            "uploader": item.get("uploader") or "",
            "added_at": time.time(),
        }
        self._items.insert(0, row)
        self.save()
        return {"ok": True, "item": row, "items": self.list()}

    def remove(self, item_id: str) -> dict[str, Any]:
        before = len(self._items)
        self._items = [i for i in self._items if str(i.get("id")) != str(item_id)]
        self.save()
        return {"ok": True, "removed": before != len(self._items), "items": self.list()}

    def toggle(self, item: dict[str, Any]) -> dict[str, Any]:
        item_id = str(item.get("id") or "")
        if self.has(item_id):
            res = self.remove(item_id)
            res["favorited"] = False
            return res
        res = self.add(item)
        res["favorited"] = True
        return res

    def clear(self) -> dict[str, Any]:
        self._items = []
        self.save()
        return {"ok": True, "items": []}
