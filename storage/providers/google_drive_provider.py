from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from provider_base import StorageProvider
from google_drive_adapter import GoogleDriveAdapter


class GoogleDriveStorageProvider(StorageProvider):
    """
    Google Drive implementation of the OpenElecBIM StorageProvider contract.

    Storage is scoped to one OpenElecBIM root folder.
    Duplicate detection is based on SHA-256 content identity,
    not filename.
    """

    provider_name = "google_drive"

    ROOT_MIME_TYPE = "application/vnd.google-apps.folder"
    CONTENT_HASH_PROPERTY = "open_elec_bim_content_hash"

    def __init__(
        self,
        account_reference: str,
        root_reference: str,
        oauth_file: str | Path | None = None,
    ):
        self.account_reference = account_reference
        self.root_reference = root_reference

        if not root_reference:
            raise ValueError(
                "root_reference is required for Google Drive storage."
            )

        if oauth_file is None:
            self.adapter = GoogleDriveAdapter(
                account_reference=account_reference
            )
        else:
            self.adapter = GoogleDriveAdapter(
                oauth_file=oauth_file,
                account_reference=account_reference,
            )

        self.service = None
        self.connected = False

    def connect(self) -> bool:
        self.adapter.connect()
        self.service = self.adapter.service

        self._verify_root()

        self.connected = True
        return True

    def _require_connection(self) -> None:
        if not self.connected or self.service is None:
            raise RuntimeError(
                "Google Drive storage provider is not connected."
            )

    def _verify_root(self) -> None:
        """
        Verify that root_reference exists, is a folder,
        and is not trashed.
        """
        self._require_service()

        try:
            root = (
                self.service.files()
                .get(
                    fileId=self.root_reference,
                    fields="id,name,mimeType,trashed,parents",
                )
                .execute()
            )
        except Exception as exc:
            raise RuntimeError(
                f"Unable to access OpenElecBIM root "
                f"'{self.root_reference}': {exc}"
            ) from exc

        if root.get("trashed", False):
            raise RuntimeError(
                "OpenElecBIM root folder is trashed."
            )

        if root.get("mimeType") != self.ROOT_MIME_TYPE:
            raise RuntimeError(
                "OpenElecBIM root_reference does not point to a folder."
            )

    def _require_service(self) -> None:
        if self.service is None:
            raise RuntimeError(
                "Google Drive service is not initialized."
            )

    @staticmethod
    def _calculate_hash(path: Path) -> str:
        digest = hashlib.sha256()

        with path.open("rb") as file:
            for chunk in iter(
                lambda: file.read(1024 * 1024),
                b"",
            ):
                digest.update(chunk)

        return digest.hexdigest()

    @staticmethod
    def _escape_query_value(value: str) -> str:
        return value.replace("\\", "\\\\").replace("'", "\\'")

    def _root_query(self) -> str:
        escaped_root = self._escape_query_value(
            self.root_reference
        )

        return (
            "trashed = false "
            f"and '{escaped_root}' in parents"
        )

    def list(self, prefix: str = "") -> list[dict[str, Any]]:
        self._require_connection()

        query = (
            self._root_query()
            + " and mimeType != "
            "'application/vnd.google-apps.folder'"
        )

        if prefix:
            escaped = self._escape_query_value(prefix)
            query += f" and name contains '{escaped}'"

        results: list[dict[str, Any]] = []
        page_token = None

        while True:
            response = (
                self.service.files()
                .list(
                    q=query,
                    fields=(
                        "nextPageToken,"
                        "files("
                        "id,"
                        "name,"
                        "size,"
                        "mimeType,"
                        "modifiedTime,"
                        "createdTime,"
                        "md5Checksum,"
                        "properties,"
                        "parents"
                        ")"
                    ),
                    pageSize=1000,
                    pageToken=page_token,
                )
                .execute()
            )

            for item in response.get("files", []):
                results.append(
                    self._metadata_from_drive_file(item)
                )

            page_token = response.get("nextPageToken")

            if not page_token:
                break

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
            raise FileNotFoundError(
                f"Source file not found: {source}"
            )

        content_hash = self._calculate_hash(source)

        existing = self._find_by_content_hash(content_hash)

        if existing is not None:
            return {
                "provider": self.provider_name,
                "reference": existing["id"],
                "name": existing.get("name"),
                "size": int(existing.get("size", 0) or 0),
                "content_hash": content_hash,
                "metadata": existing.get("properties", {}),
                "already_exists": True,
            }

        file_name = Path(destination).name or source.name

        from googleapiclient.http import MediaFileUpload

        properties: dict[str, str] = {}

        for key, value in (metadata or {}).items():
            properties[str(key)] = str(value)

        properties[
            self.CONTENT_HASH_PROPERTY
        ] = content_hash

        media = MediaFileUpload(
            str(source),
            resumable=True,
        )

        body = {
            "name": file_name,
            "parents": [self.root_reference],
            "properties": properties,
        }

        created = (
            self.service.files()
            .create(
                body=body,
                media_body=media,
                fields=(
                    "id,"
                    "name,"
                    "size,"
                    "mimeType,"
                    "modifiedTime,"
                    "createdTime,"
                    "md5Checksum,"
                    "properties,"
                    "parents"
                ),
            )
            .execute()
        )

        return {
            "provider": self.provider_name,
            "reference": created["id"],
            "name": created.get("name", file_name),
            "size": int(
                created.get(
                    "size",
                    source.stat().st_size,
                )
                or 0
            ),
            "content_hash": content_hash,
            "metadata": created.get(
                "properties",
                properties,
            ),
            "already_exists": False,
        }

    def download(
        self,
        source: str,
        destination_path: str,
    ) -> dict[str, Any]:
        self._require_connection()

        item = self._get_scoped_file(
            source,
            fields=(
                "id,"
                "name,"
                "size,"
                "mimeType,"
                "properties,"
                "parents"
            ),
        )

        from googleapiclient.http import MediaIoBaseDownload
        import io

        destination = Path(destination_path).resolve()
        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        request = self.service.files().get_media(
            fileId=item["id"]
        )

        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(
            buffer,
            request,
        )

        done = False

        while not done:
            _, done = downloader.next_chunk()

        destination.write_bytes(
            buffer.getvalue()
        )

        return {
            "provider": self.provider_name,
            "reference": source,
            "destination": str(destination),
            "content_hash": self._calculate_hash(
                destination
            ),
            "size": destination.stat().st_size,
        }

    def exists(self, reference: str) -> bool:
        self._require_connection()

        try:
            item = (
                self.service.files()
                .get(
                    fileId=reference,
                    fields="id,trashed,parents",
                )
                .execute()
            )

            if item.get("trashed", False):
                return False

            return self._is_in_root(item)

        except Exception as exc:
            if self._is_not_found(exc):
                return False

            raise

    def delete(self, reference: str) -> bool:
        self._require_connection()

        if not self.exists(reference):
            return False

        self.service.files().delete(
            fileId=reference
        ).execute()

        return True

    def get_metadata(
        self,
        reference: str,
    ) -> dict[str, Any]:
        self._require_connection()

        item = self._get_scoped_file(
            reference,
            fields=(
                "id,"
                "name,"
                "size,"
                "mimeType,"
                "modifiedTime,"
                "createdTime,"
                "md5Checksum,"
                "properties,"
                "parents"
            ),
        )

        return self._metadata_from_drive_file(
            item
        )

    def _find_by_content_hash(
        self,
        content_hash: str,
    ) -> dict[str, Any] | None:
        escaped_hash = self._escape_query_value(
            content_hash
        )

        query = (
            self._root_query()
            + " and mimeType != "
            "'application/vnd.google-apps.folder' "
            + "and properties has { "
            f"key='{self.CONTENT_HASH_PROPERTY}' "
            f"and value='{escaped_hash}' "
            "}"
        )

        response = (
            self.service.files()
            .list(
                q=query,
                fields=(
                    "files("
                    "id,"
                    "name,"
                    "size,"
                    "mimeType,"
                    "modifiedTime,"
                    "createdTime,"
                    "md5Checksum,"
                    "properties,"
                    "parents"
                    ")"
                ),
                pageSize=10,
            )
            .execute()
        )

        files = response.get("files", [])

        return files[0] if files else None

    def _get_scoped_file(
        self,
        reference: str,
        fields: str,
    ) -> dict[str, Any]:
        try:
            item = (
                self.service.files()
                .get(
                    fileId=reference,
                    fields=fields,
                )
                .execute()
            )
        except Exception as exc:
            if self._is_not_found(exc):
                raise FileNotFoundError(
                    f"Google Drive file not found: {reference}"
                ) from exc

            raise

        if item.get("trashed", False):
            raise FileNotFoundError(
                f"Google Drive file is trashed: {reference}"
            )

        if not self._is_in_root(item):
            raise PermissionError(
                "Google Drive reference is outside the "
                "OpenElecBIM root."
            )

        return item

    def _is_in_root(
        self,
        item: dict[str, Any],
    ) -> bool:
        parents = item.get("parents", [])

        return self.root_reference in parents

    def _metadata_from_drive_file(
        self,
        item: dict[str, Any],
    ) -> dict[str, Any]:
        properties = item.get(
            "properties",
            {},
        )

        return {
            "provider": self.provider_name,
            "reference": item.get("id"),
            "name": item.get("name"),
            "size": int(
                item.get("size", 0) or 0
            ),
            "mime_type": item.get("mimeType"),
            "created_time": item.get(
                "createdTime"
            ),
            "modified_time": item.get(
                "modifiedTime"
            ),
            "md5_checksum": item.get(
                "md5Checksum"
            ),
            "content_hash": properties.get(
                self.CONTENT_HASH_PROPERTY
            ),
            "metadata": properties,
            "parents": item.get(
                "parents",
                [],
            ),
        }

    @staticmethod
    def _is_not_found(
        exc: Exception,
    ) -> bool:
        return (
            getattr(
                exc,
                "status_code",
                None,
            )
            == 404
            or "404" in str(exc)
        )
