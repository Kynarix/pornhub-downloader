
from __future__ import annotations

import os
import subprocess
import sys
from typing import Any

import webview

from core.downloader import Downloader
from core.favorites import FavoritesStore
from core.history import HistoryStore
from core.models import DownloadJob
from core.queue import DownloadQueue
from core.settings import Settings
from providers.registry import ProviderRegistry


class Api:
    """JS bridge — only public methods; all state is _private."""

    def __init__(self) -> None:
        self._settings = Settings()
        self._history = HistoryStore()
        self._favorites = FavoritesStore()
        self._registry = ProviderRegistry()
        self._downloader = Downloader()
        self._queue = DownloadQueue(
            self._downloader,
            self._history,
            workers=int(self._settings.get("concurrent_downloads", 1)),
        )

    def get_settings(self) -> dict:
        return {"ok": True, "settings": self._settings.to_dict()}

    def update_settings(self, patch: dict) -> dict:
        try:
            settings = self._settings.update(patch or {})
            # concurrent workers are fixed at queue creation; note in UI
            return {"ok": True, "settings": settings}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def set_download_dir(self, path: str) -> dict:
        if not path:
            return {"ok": False, "error": "Geçersiz klasör"}
        self._settings.set("download_dir", path)
        return {"ok": True, "settings": self._settings.to_dict()}

    def pick_download_dir(self) -> dict:
        windows = webview.windows
        if not windows:
            return {"ok": False, "error": "Pencere yok"}
        result = windows[0].create_file_dialog(webview.FOLDER_DIALOG)
        if not result:
            return {"ok": False, "cancelled": True}
        path = result[0] if isinstance(result, (list, tuple)) else result
        self._settings.set("download_dir", str(path))
        return {"ok": True, "path": str(path), "settings": self._settings.to_dict()}

    def resolve_url(self, url: str) -> dict:
        url = (url or "").strip()
        if not url:
            return {"ok": False, "error": "URL gerekli"}
        try:
            provider = self._registry.resolve_provider(url)
            info = provider.resolve(url)
            return {"ok": True, "video": info.to_dict(), "provider": provider.id}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def enqueue(self, payload: dict) -> dict:
        try:
            url = (payload.get("url") or "").strip()
            title = payload.get("title") or "video"
            format_id = payload.get("format_id") or "bv*+ba/b"
            format_label = payload.get("format_label") or format_id
            thumbnail = payload.get("thumbnail") or ""
            output_dir = payload.get("output_dir") or self._settings.get("download_dir")
            job = DownloadJob.create(
                url=url,
                title=title,
                format_id=format_id,
                format_label=format_label,
                output_dir=output_dir,
                thumbnail=thumbnail,
            )
            return {"ok": True, "job": self._queue.add(job)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def enqueue_best(self, payload: dict) -> dict:
        """One-click: resolve formats, pick best, enqueue."""
        url = (payload.get("url") or "").strip()
        if not url:
            return {"ok": False, "error": "URL gerekli"}
        try:
            provider = self._registry.resolve_provider(url)
            info = provider.resolve(url)
            fmt = info.formats[0] if info.formats else None
            format_id = fmt.format_id if fmt else "bv*+ba/b"
            format_label = fmt.label if fmt else "best"
            job = DownloadJob.create(
                url=info.webpage_url or url,
                title=info.title or payload.get("title") or "video",
                format_id=format_id,
                format_label=format_label,
                output_dir=self._settings.get("download_dir"),
                thumbnail=info.thumbnail or payload.get("thumbnail") or "",
            )
            return {
                "ok": True,
                "job": self._queue.add(job),
                "video": info.to_dict(),
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_queue(self) -> dict:
        return {"ok": True, "jobs": self._queue.list_jobs()}

    def cancel_job(self, job_id: str) -> dict:
        return {"ok": self._queue.cancel(job_id)}

    def clear_finished(self) -> dict:
        self._queue.clear_finished()
        return {"ok": True, "jobs": self._queue.list_jobs()}

    def get_history(self) -> dict:
        return {"ok": True, "items": self._history.list()}

    def clear_history(self) -> dict:
        self._history.clear()
        return {"ok": True}

    def search(self, query: str, page: int = 1) -> dict:
        provider = self._registry.get("pornhub")
        if not provider:
            return {"ok": False, "error": "provider_missing"}
        result = provider.search(query, page)
        if result.get("ok"):
            favs = self._favorites.ids()
            for item in result.get("items") or []:
                item["favorited"] = str(item.get("id")) in favs
        return result

    def browse(self, category: str = "hot", page: int = 1) -> dict:
        provider = self._registry.get("pornhub")
        if not provider:
            return {"ok": False, "error": "provider_missing"}
        result = provider.browse(category, page)
        if result.get("ok"):
            favs = self._favorites.ids()
            for item in result.get("items") or []:
                item["favorited"] = str(item.get("id")) in favs
        return result

    def list_catalog(self) -> dict:
        provider = self._registry.get("pornhub")
        if not provider:
            return {"ok": False, "error": "provider_missing"}
        return provider.list_catalog()

    def get_favorites(self) -> dict:
        return {"ok": True, "items": self._favorites.list()}

    def toggle_favorite(self, item: dict) -> dict:
        return self._favorites.toggle(item or {})

    def remove_favorite(self, item_id: str) -> dict:
        return self._favorites.remove(item_id)

    def clear_favorites(self) -> dict:
        return self._favorites.clear()

    def list_providers(self) -> dict:
        return {"ok": True, "providers": self._registry.list()}

    def open_path(self, path: str) -> dict:
        if not path:
            return {"ok": False}
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def ping(self) -> dict[str, Any]:
        return {"ok": True, "pong": True}
