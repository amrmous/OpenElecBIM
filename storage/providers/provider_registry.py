from __future__ import annotations

from typing import Any, Callable

from mock_provider import MockStorageProvider
from google_drive_provider import GoogleDriveStorageProvider


class ProviderRegistry:
    """
    Registry and factory for OpenElecBIM storage providers.
    """

    def __init__(self) -> None:
        self._factories: dict[str, Callable[..., Any]] = {}

    def register(
        self,
        provider_name: str,
        factory: Callable[..., Any],
    ) -> None:
        name = provider_name.strip().lower()

        if not name:
            raise ValueError("Provider name cannot be empty.")

        if name in self._factories:
            raise ValueError(
                f"Provider already registered: {name}"
            )

        self._factories[name] = factory

    def unregister(self, provider_name: str) -> bool:
        name = provider_name.strip().lower()
        return self._factories.pop(name, None) is not None

    def has(self, provider_name: str) -> bool:
        return provider_name.strip().lower() in self._factories

    def names(self) -> list[str]:
        return sorted(self._factories.keys())

    def create(
        self,
        provider_name: str,
        **kwargs: Any,
    ) -> Any:
        name = provider_name.strip().lower()

        factory = self._factories.get(name)

        if factory is None:
            raise KeyError(
                f"Provider is not registered: {name}"
            )

        return factory(**kwargs)


def create_default_registry() -> ProviderRegistry:
    registry = ProviderRegistry()

    registry.register(
        "mock",
        MockStorageProvider,
    )

    registry.register(
        "google_drive",
        GoogleDriveStorageProvider,
    )

    return registry
