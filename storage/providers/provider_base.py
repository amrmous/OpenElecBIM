from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StorageProvider(ABC):
    """
    Standard interface for all OpenElecBIM storage providers.

    Providers may be:
    - Google Drive
    - Local filesystem
    - OneDrive
    - S3
    - Any future storage backend
    """

    provider_name: str = "unknown"

    @abstractmethod
    def connect(self) -> bool:
        """Establish or validate the provider connection."""
        raise NotImplementedError

    @abstractmethod
    def list(self, prefix: str = "") -> list[dict[str, Any]]:
        """List objects/files under an optional prefix."""
        raise NotImplementedError

    @abstractmethod
    def upload(
        self,
        source_path: str,
        destination: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Upload a local file/object to the provider."""
        raise NotImplementedError

    @abstractmethod
    def download(
        self,
        source: str,
        destination_path: str,
    ) -> dict[str, Any]:
        """Download an object/file from the provider."""
        raise NotImplementedError

    @abstractmethod
    def exists(self, reference: str) -> bool:
        """Check whether an object exists."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, reference: str) -> bool:
        """Delete an object/file."""
        raise NotImplementedError

    @abstractmethod
    def get_metadata(self, reference: str) -> dict[str, Any]:
        """Return provider metadata for an object."""
        raise NotImplementedError
