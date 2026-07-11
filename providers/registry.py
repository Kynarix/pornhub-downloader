
from __future__ import annotations

from providers.base import Provider
from providers.pornhub import PornhubProvider


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: list[Provider] = [PornhubProvider()]

    def register(self, provider: Provider) -> None:
        self._providers.append(provider)

    def list(self) -> list[dict[str, str]]:
        return [{"id": p.id, "name": p.name} for p in self._providers]

    def resolve_provider(self, url: str) -> Provider:
        for p in self._providers:
            if p.can_handle(url):
                return p
        raise ValueError("Bu URL desteklenmiyor. Pornhub linki yapıştır.")

    def get(self, provider_id: str) -> Provider | None:
        for p in self._providers:
            if p.id == provider_id:
                return p
        return None
