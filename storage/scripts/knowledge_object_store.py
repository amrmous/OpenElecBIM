from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_OBJECT_ROOT = (
    PROJECT_ROOT
    / "storage"
    / "objects"
)


class KnowledgeObjectStore:
    """
    Local Knowledge Object storage core.

    This class intentionally does not depend on Google Drive or any
    specific external storage provider.

    Logical identity is based on content hash.
    Physical storage location is treated as infrastructure.
    """

    def __init__(self, object_root=DEFAULT_OBJECT_ROOT):
        self.object_root = Path(object_root)
        self.object_root.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    @staticmethod
    def calculate_sha256(file_path: Path) -> str:
        sha256 = hashlib.sha256()

        with Path(file_path).open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                sha256.update(chunk)

        return sha256.hexdigest()

    @staticmethod
    def create_object_id(content_hash: str) -> str:
        return f"ko_{content_hash[:32]}"

    # ---------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------

    @staticmethod
    def utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def build_metadata(
        self,
        source_file: Path,
        content_hash: str,
        object_id: str,
        contributor_id: str | None = None,
        source: dict[str, Any] | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        source_file = Path(source_file)

        metadata = {
            "schema_version": 1,
            "object_id": object_id,
            "content_hash": content_hash,
            "hash_algorithm": "sha256",
            "file_name": source_file.name,
            "file_size": source_file.stat().st_size,
            "created_at": self.utc_now(),
            "version": 1,
            "contributor_id": contributor_id,
            "provenance": {
                "source": source or {},
                "ingestion": {
                    "ingested_at": self.utc_now(),
                    "ingestion_method": "local_file",
                },
            },
            "storage": {
                "provider": "local",
                "storage_type": "filesystem",
                "status": "verified",
            },
        }

        if extra_metadata:
            metadata["metadata"] = extra_metadata

        return metadata

    # ---------------------------------------------------------
    # Physical object paths
    # ---------------------------------------------------------

    def get_object_dir(self, object_id: str) -> Path:
        return self.object_root / object_id

    def get_object_file(self, object_id: str, file_name: str) -> Path:
        return self.get_object_dir(object_id) / file_name

    def get_metadata_file(self, object_id: str) -> Path:
        return self.get_object_dir(object_id) / "object.json"

    # ---------------------------------------------------------
    # Store
    # ---------------------------------------------------------

    def store(
        self,
        source_file,
        contributor_id: str | None = None,
        source: dict[str, Any] | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        source_file = Path(source_file)

        if not source_file.exists():
            raise FileNotFoundError(
                f"Source file not found: {source_file}"
            )

        if not source_file.is_file():
            raise ValueError(
                f"Source path is not a file: {source_file}"
            )

        content_hash = self.calculate_sha256(source_file)
        object_id = self.create_object_id(content_hash)

        object_dir = self.get_object_dir(object_id)
        object_dir.mkdir(parents=True, exist_ok=True)

        destination = object_dir / source_file.name

        if not destination.exists():
            shutil.copy2(source_file, destination)

        metadata = self.build_metadata(
            source_file=source_file,
            content_hash=content_hash,
            object_id=object_id,
            contributor_id=contributor_id,
            source=source,
            extra_metadata=extra_metadata,
        )

        metadata["storage"]["path"] = str(destination)

        metadata_file = self.get_metadata_file(object_id)

        with metadata_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                metadata,
                file,
                ensure_ascii=False,
                indent=2,
            )

        return metadata

    # ---------------------------------------------------------
    # Retrieve
    # ---------------------------------------------------------

    def retrieve(self, object_id: str) -> Path:
        object_dir = self.get_object_dir(object_id)

        if not object_dir.exists():
            raise FileNotFoundError(
                f"Knowledge Object not found: {object_id}"
            )

        metadata_file = self.get_metadata_file(object_id)

        if not metadata_file.exists():
            raise FileNotFoundError(
                f"Metadata not found for Knowledge Object: {object_id}"
            )

        with metadata_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            metadata = json.load(file)

        file_name = metadata.get("file_name")

        if not file_name:
            raise ValueError(
                f"Knowledge Object metadata has no file_name: {object_id}"
            )

        object_file = object_dir / file_name

        if not object_file.exists():
            raise FileNotFoundError(
                f"Stored object file not found: {object_file}"
            )

        return object_file

    # ---------------------------------------------------------
    # Verification
    # ---------------------------------------------------------

    def verify(self, object_id: str) -> dict[str, Any]:
        object_file = self.retrieve(object_id)

        metadata_file = self.get_metadata_file(object_id)

        with metadata_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            metadata = json.load(file)

        expected_hash = metadata.get("content_hash")

        if not expected_hash:
            raise ValueError(
                f"Knowledge Object has no content hash: {object_id}"
            )

        actual_hash = self.calculate_sha256(object_file)

        verified = actual_hash == expected_hash

        return {
            "object_id": object_id,
            "verified": verified,
            "expected_hash": expected_hash,
            "actual_hash": actual_hash,
            "file": str(object_file),
        }


if __name__ == "__main__":
    store = KnowledgeObjectStore()

    print("KNOWLEDGE OBJECT STORE = OK")
    print("Object Root =", store.object_root)
