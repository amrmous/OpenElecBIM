from __future__ import annotations

from typing import Any

from storage_profile_registry import StorageProfileRegistry
from provider_registry import ProviderRegistry
from provider_resolver import ProviderResolver


class ProviderManager:
    """
    High-level manager for resolving and caching OpenElecBIM
    storage providers by storage profile.
    """

    def __init__(
        self,
        profile_registry: StorageProfileRegistry,
        provider_registry: ProviderRegistry,
    ) -> None:
        self.profile_registry = profile_registry
        self.provider_registry = provider_registry
        self.resolver = ProviderResolver(
            profile_registry=profile_registry,
            provider_registry=provider_registry,
        )
        self._providers: dict[str, Any] = {}

    def get_provider(
        self,
        storage_profile_id: str,
        *,
        connect: bool = True,
        **provider_kwargs: Any,
    ) -> Any:
        if storage_profile_id in self._providers:
            provider = self._providers[storage_profile_id]

            if connect and not getattr(provider, "connected", False):
                provider.connect()

            return provider

        provider = self.resolver.resolve(
            storage_profile_id,
            **provider_kwargs,
        )

        if connect:
            provider.connect()

        self._providers[storage_profile_id] = provider

        return provider

    def has_provider(self, storage_profile_id: str) -> bool:
        return storage_profile_id in self._providers

    def disconnect(self, storage_profile_id: str) -> bool:
        provider = self._providers.pop(
            storage_profile_id,
            None,
        )

        if provider is None:
            return False

        return True

    def clear(self) -> None:
        self._providers.clear()

    def active_profiles(self) -> list[str]:
        return sorted(self._providers.keys())
