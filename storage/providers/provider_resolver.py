from __future__ import annotations

from typing import Any

from storage_profile_registry import StorageProfileRegistry
from provider_registry import ProviderRegistry


class ProviderResolver:
    """
    Resolves an OpenElecBIM Storage Profile into a provider instance.

    Storage profiles contain provider identity and storage references.
    Provider-specific runtime configuration is supplied explicitly through
    provider_kwargs.
    """

    def __init__(
        self,
        profile_registry: StorageProfileRegistry,
        provider_registry: ProviderRegistry,
    ) -> None:
        self.profile_registry = profile_registry
        self.provider_registry = provider_registry

    def resolve(
        self,
        storage_profile_id: str,
        **provider_kwargs: Any,
    ) -> Any:
        profile = self.profile_registry.get_profile(
            storage_profile_id
        )

        if profile is None:
            raise KeyError(
                f"Storage profile not found: {storage_profile_id}"
            )

        if not profile.get("enabled", False):
            raise RuntimeError(
                f"Storage profile is disabled: {storage_profile_id}"
            )

        provider_name = profile.get("provider")

        if not provider_name:
            raise ValueError(
                f"Storage profile has no provider: {storage_profile_id}"
            )

        provider_kwargs = dict(provider_kwargs)

        if provider_name.strip().lower() == "google_drive":
            account_reference = profile.get("account_reference")
            root_reference = profile.get("root_reference")

            if not account_reference:
                raise ValueError(
                    f"Google Drive profile has no account_reference: "
                    f"{storage_profile_id}"
                )

            if not root_reference:
                raise ValueError(
                    f"Google Drive profile has no root_reference: "
                    f"{storage_profile_id}"
                )

            provider_kwargs.setdefault(
                "account_reference",
                account_reference,
            )
            provider_kwargs.setdefault(
                "root_reference",
                root_reference,
            )

        return self.provider_registry.create(
            provider_name,
            **provider_kwargs,
        )
