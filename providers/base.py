
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from core.models import VideoInfo


class Provider(ABC):
    """C-ready provider contract. MVP uses resolve only."""

    id: str
    name: str

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        ...

    @abstractmethod
    def resolve(self, url: str) -> VideoInfo:
        ...

    def search(self, query: str, page: int = 1) -> dict[str, Any]:
        """Stub for scope C."""
        return {
            "ok": False,
            "error": "search_not_implemented",
            "message": "Arama yakında eklenecek.",
            "items": [],
            "page": page,
            "query": query,
        }

    def browse(self, category: str = "", page: int = 1) -> dict[str, Any]:
        """Stub for scope C."""
        return {
            "ok": False,
            "error": "browse_not_implemented",
            "message": "Göz atma yakında eklenecek.",
            "items": [],
            "page": page,
            "category": category,
        }
