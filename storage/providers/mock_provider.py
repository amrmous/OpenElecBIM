from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Any

from provider_base import StorageProvider


class MockStorageProvider(StorageProvider):
    """
    Local mock provider used for testing the storage architecture.

    It behaves like a remote provider but stores files in a local directory.
    """

    provider_name = "mock"

    def __init__(self, root_path: str | Path):
        self.root_path = Path(root_path).resolve()
        self.connected = False

    def connect(self) -> bool:
        self.root_path.mkdir(parents=True, exist_ok=True)
        self.connected = True
        return True

    def _require_connection(self) -> None:
        if not self.connected:
            raise RuntimeError("Mock storage provider is not connected.")

    def _resolve(self, reference: str) -> Path:
        path = (self.root_path / reference).resolve()

        try:
            path.relative_to(self.root_path)
        except ValueError as exc:
            raise ValueError("Reference escapes provider root.") from exc

        return path

    def list(self, prefix: str = "") -> list[dict[str, Any]]:
        self._require_connection()

        base = self._resolve(prefix) if prefix else self.root_path

        if not base.exists():
            return []

        results = []

        for path in sorted(base.rglob("*")):
            if path.is_file():
                relative = path.relative_to(self.root_path).as_posix()
                results.append(self.get_metadata(relative))

        return results

    def upload(
        self,
        source_path: str,
        destination: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._require_connection()

        source = Path(source_path).resolve()

        if not source.is_file():
            raise FileNotFoundError(f"Source file not found: {source}")

        target = self._resolve(destination)
        target.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source, target)

        content_hash = self._calculate_hash(target)

        return {
            "provider": self.provider_name,
            "reference": target.relative_to(self.root_path).as_posix(),
            "name": target.name,
            "size": target.stat().st_size,
            "content_hash": content_hash,
            "metadata": metadata or {},
        }

    def download(
        self,
        source: str,
        destination_path: str,
    ) -> dict[str, Any]:
        self._require_connection()

        source_path = self._resolve(source)

        if not source_path.is_file():
            raise FileNotFoundError(f"Provider object not found: {source}")

        destination = Path(destination_path).resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source_path, destination)

        return {
            "provider": self.provider_name,
            "reference": source,
            "destination": str(destination),
            "content_hash": self._calculate_hash(destination),
            "size": destination.stat().st_size,
        }

    def exists(self, reference: str) -> bool:
        self._require_connection()
        return self._resolve(reference).is_file()

    def delete(self, reference: str) -> bool:
        self._require_connection()

        target = self._resolve(reference)

        if not target.is_file():
            return False

        target.unlink()
        return True

    def get_metadata(self, reference: str) -> dict[str, Any]:
        self._require_connection()

        target = self._resolve(reference)

        if not target.is_file():
            raise FileNotFoundError(f"Provider object not found: {reference}")

        return {
            "provider": self.provider_name,
            "reference": reference,
            "name": target.name,
            "size": target.stat().st_size,
            "content_hash": self._calculate_hash(target),
        }

    @staticmethod
    def _calculate_hash(path: Path) -> str:
        digest = hashlib.sha256()

        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)

        return digest.hexdigest()
