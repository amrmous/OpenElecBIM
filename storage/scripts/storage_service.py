from pathlib import Path
import hashlib
import uuid


class StorageService:
    def __init__(self, pool=None):
        if pool is None:
            from storage.scripts.storage_pool_manager import StoragePoolManager
            pool = StoragePoolManager()

        self.pool = pool

    @staticmethod
    def calculate_sha256(file_path: str | Path) -> str:
        path = Path(file_path)
        digest = hashlib.sha256()

        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)

        return digest.hexdigest()

    @staticmethod
    def _id(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex}"

    def _rollback(
        self,
        *,
        provider,
        uploaded_reference: str | None,
        replica_id: str | None,
        object_id: str | None,
        object_created: bool,
        ledger_created: bool,
    ) -> dict:

        rollback = {
            "attempted": True,
            "provider_deleted": False,
            "replica_removed": False,
            "object_removed": False,
            "ledger_preserved": ledger_created,
            "errors": [],
        }

        if ledger_created:
            if replica_id:
                try:
                    replica = self.pool.get_replica(replica_id)
                    if replica:
                        self.pool.replicas.update_status(
                            replica_id,
                            "needs_verification",
                        )
                except Exception as exc:
                    rollback["errors"].append(
                        f"replica_quarantine: {type(exc).__name__}: {exc}"
                    )

            return rollback

        if uploaded_reference:
            try:
                rollback["provider_deleted"] = bool(
                    provider.delete(uploaded_reference)
                )
            except Exception as exc:
                rollback["errors"].append(
                    f"provider_delete: {type(exc).__name__}: {exc}"
                )

        if replica_id:
            try:
                self.pool.replicas.unregister_replica(replica_id)
                rollback["replica_removed"] = True
            except KeyError:
                rollback["replica_removed"] = True
            except Exception as exc:
                rollback["errors"].append(
                    f"replica_unregister: {type(exc).__name__}: {exc}"
                )

        if object_created and object_id:
            try:
                self.pool.objects.unregister_object(object_id)
                rollback["object_removed"] = True
            except KeyError:
                rollback["object_removed"] = True
            except Exception as exc:
                rollback["errors"].append(
                    f"object_unregister: {type(exc).__name__}: {exc}"
                )

        return rollback

    def download_file(
        self,
        replica_id: str,
        destination_path: str | Path,
        provider_kwargs: dict | None = None,
    ) -> dict:
        """
        Download a stored replica and verify its SHA-256 integrity.

        The replica remains the source of truth for:
        - object_id
        - storage_profile_id
        - provider reference
        - expected content hash
        """

        replica = self.pool.get_replica(replica_id)

        if replica is None:
            raise ValueError(
                f"Replica not found: {replica_id}"
            )

        if replica.get("status", "active") != "active":
            raise ValueError(
                f"Replica is not active: {replica_id}"
            )

        storage_profile_id = replica.get("storage_profile_id")

        if not storage_profile_id:
            raise ValueError(
                f"Replica has no storage profile: {replica_id}"
            )

        reference = replica.get("reference")

        if not reference:
            raise ValueError(
                f"Replica has no provider reference: {replica_id}"
            )

        expected_hash = replica.get("content_hash")

        if not expected_hash:
            raise ValueError(
                f"Replica has no content hash: {replica_id}"
            )

        destination = Path(destination_path).resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)

        provider = self.pool.get_provider(
            storage_profile_id,
            connect=True,
            **(provider_kwargs or {}),
        )

        provider_name = getattr(
            provider,
            "provider_name",
            replica.get("provider", "unknown"),
        )

        download_result = provider.download(
            reference,
            str(destination),
        )

        if not destination.exists():
            raise RuntimeError(
                "Provider download completed without creating destination file: "
                f"{destination}"
            )

        downloaded_hash = self.calculate_sha256(destination)

        hashes_match = (
            downloaded_hash == expected_hash
        )

        if not hashes_match:
            return {
                "success": False,
                "operation": "download",
                "provider": provider_name,
                "object_id": replica.get("object_id"),
                "replica_id": replica_id,
                "storage_profile_id": storage_profile_id,
                "reference": reference,
                "destination": str(destination),
                "download": download_result,
                "expected_hash": expected_hash,
                "downloaded_hash": downloaded_hash,
                "hashes_match": False,
                "error": {
                    "type": "HashMismatch",
                    "message": (
                        "Downloaded file hash does not match replica content hash."
                    ),
                },
            }

        return {
            "success": True,
            "operation": "download",
            "provider": provider_name,
            "object_id": replica.get("object_id"),
            "replica_id": replica_id,
            "storage_profile_id": storage_profile_id,
            "reference": reference,
            "destination": str(destination),
            "download": download_result,
            "expected_hash": expected_hash,
            "downloaded_hash": downloaded_hash,
            "hashes_match": True,
        }

    def store_file(
        self,
        source_path: str | Path,
        contributor_id: str,
        storage_profile_id: str,
        *,
        object_type: str = "document",
        title: str | None = None,
        language: str | None = None,
        destination: str | None = None,
        metadata: dict | None = None,
        provider_kwargs: dict | None = None,
    ) -> dict:

        source = Path(source_path).resolve()

        if not source.exists():
            raise FileNotFoundError(
                f"Source file not found: {source}"
            )

        if not source.is_file():
            raise ValueError(
                f"Source path is not a file: {source}"
            )

        contributor = self.pool.get_contributor(contributor_id)

        if contributor is None:
            raise ValueError(
                f"Contributor not found: {contributor_id}"
            )

        if not contributor.get("enabled", False):
            raise ValueError(
                f"Contributor is disabled: {contributor_id}"
            )

        profile = self.pool.get_profile(storage_profile_id)

        if profile is None:
            raise ValueError(
                f"Storage profile not found: {storage_profile_id}"
            )

        if not profile.get("enabled", False):
            raise ValueError(
                f"Storage profile is disabled: {storage_profile_id}"
            )

        content_hash = self.calculate_sha256(source)

        existing_objects = self.pool.objects.find_by_hash(content_hash)

        existing_object = (
            existing_objects[0]
            if existing_objects
            else None
        )

        object_id = (
            existing_object.get("object_id")
            if existing_object
            else None
        )

        if existing_object:
            existing_replicas = self.pool.replicas.find_by_object(
                object_id
            )

            matching_replicas = [
                replica
                for replica in existing_replicas
                if (
                    replica.get("storage_profile_id")
                    == storage_profile_id
                    and replica.get("content_hash")
                    == content_hash
                    and replica.get("status", "active")
                    == "active"
                )
            ]

            if matching_replicas:
                existing_replica = matching_replicas[0]

                return {
                    "success": True,
                    "duplicate": True,
                    "operation": "already_exists",
                    "provider": profile.get(
                        "provider",
                        "unknown",
                    ),
                    "object_id": object_id,
                    "replica_id": existing_replica.get(
                        "replica_id"
                    ),
                    "contribution_id": None,
                    "content_hash": content_hash,
                    "object_created": False,
                    "replica_created": False,
                    "object": existing_object,
                    "replica": existing_replica,
                    "message": (
                        "Knowledge object replica already exists "
                        "for this storage profile and content hash."
                    ),
                    "verification": {
                        "content_hash": content_hash,
                        "existing_object_hash": existing_object.get(
                            "content_hash"
                        ),
                        "hashes_match": (
                            content_hash
                            == existing_object.get("content_hash")
                        ),
                    },
                    "transaction": {
                        "status": "already_exists",
                        "rolled_back": False,
                        "ledger_created": False,
                    },
                }

            operation = "replica_add"
            object_created = False

        else:
            operation = "create"
            object_created = True

        provider = self.pool.get_provider(
            storage_profile_id,
            connect=True,
            **(provider_kwargs or {}),
        )

        provider_name = getattr(
            provider,
            "provider_name",
            profile.get("provider", "unknown"),
        )

        replica_id = self._id("replica")
        contribution_id = self._id("contribution")

        if object_created:
            object_id = self._id("knowledge_object")

        if destination is None:
            destination = (
                f"objects/{content_hash[:2]}/{source.name}"
            )

        upload_result = None
        object_result = None
        replica_result = None
        contribution_result = None

        uploaded_reference = None
        ledger_created = False

        try:
            upload_result = provider.upload(
                source,
                destination,
                metadata={
                    **(metadata or {}),
                    "content_hash": content_hash,
                    "source_name": source.name,
                    "object_id": object_id,
                    "operation": operation,
                },
            )

            uploaded_reference = upload_result.get(
                "reference",
                destination,
            )

            uploaded_hash = upload_result.get("content_hash")

            if uploaded_hash != content_hash:
                raise ValueError(
                    "Provider upload hash mismatch: "
                    f"expected={content_hash}, "
                    f"actual={uploaded_hash}"
                )

            if object_created:
                object_result = self.pool.objects.register_object(
                    object_id=object_id,
                    object_type=object_type,
                    title=title or source.stem,
                    content_hash=content_hash,
                    source=str(source),
                    version=1,
                    language=language,
                    metadata={
                        **(metadata or {}),
                        "provider": provider_name,
                        "storage_profile_id": storage_profile_id,
                        "contributor_id": contributor_id,
                    },
                )
            else:
                object_result = self.pool.get_object(object_id)

                if object_result is None:
                    raise RuntimeError(
                        "Canonical object disappeared before replica creation: "
                        f"{object_id}"
                    )

            replica_result = self.pool.replicas.register_replica(
                replica_id=replica_id,
                object_id=object_id,
                contributor_id=contributor_id,
                storage_profile_id=storage_profile_id,
                provider=provider_name,
                reference=uploaded_reference,
                content_hash=content_hash,
                hash_algorithm="sha256",
                status="active",
                metadata={
                    **(metadata or {}),
                    "uploaded_hash": uploaded_hash,
                    "operation": operation,
                },
            )

            contribution_result = (
                self.pool.ledger.record_contribution(
                    contribution_id=contribution_id,
                    contributor_id=contributor_id,
                    object_id=object_id,
                    replica_id=replica_id,
                    storage_profile_id=storage_profile_id,
                    action=operation,
                    content_hash=content_hash,
                    metadata={
                        **(metadata or {}),
                        "provider": provider_name,
                        "reference": uploaded_reference,
                    },
                )
            )

            ledger_created = True

            ledger_entry_valid = (
                self.pool.ledger.verify_entry(
                    contribution_id
                )
            )

            ledger_chain_valid = (
                self.pool.ledger.verify_chain()
            )

            object_hash = object_result.get("content_hash")
            replica_hash = replica_result.get("content_hash")
            ledger_hash = contribution_result.get("content_hash")

            hashes_match = (
                content_hash
                == object_hash
                == replica_hash
                == ledger_hash
            )

            success = (
                hashes_match
                and ledger_entry_valid
                and ledger_chain_valid
            )

            if not success:
                raise RuntimeError(
                    "Storage transaction verification failed "
                    "after ledger creation"
                )

            return {
                "success": True,
                "duplicate": False,
                "operation": operation,
                "provider": provider_name,
                "upload": upload_result,
                "object": object_result,
                "replica": replica_result,
                "contribution": contribution_result,
                "object_id": object_id,
                "replica_id": replica_id,
                "contribution_id": contribution_id,
                "content_hash": content_hash,
                "object_created": object_created,
                "replica_created": True,
                "verification": {
                    "content_hash": content_hash,
                    "object_hash": object_hash,
                    "replica_hash": replica_hash,
                    "ledger_hash": ledger_hash,
                    "hashes_match": hashes_match,
                    "ledger_entry_valid": ledger_entry_valid,
                    "ledger_chain_valid": ledger_chain_valid,
                },
                "transaction": {
                    "status": "committed",
                    "rolled_back": False,
                    "ledger_created": True,
                },
            }

        except Exception as exc:

            rollback = self._rollback(
                provider=provider,
                uploaded_reference=uploaded_reference,
                replica_id=replica_id,
                object_id=object_id,
                object_created=object_created,
                ledger_created=ledger_created,
            )

            return {
                "success": False,
                "duplicate": False,
                "operation": operation,
                "provider": provider_name,
                "upload": upload_result,
                "object": object_result,
                "replica": replica_result,
                "contribution": contribution_result,
                "object_id": object_id,
                "replica_id": replica_id,
                "contribution_id": contribution_id,
                "content_hash": content_hash,
                "object_created": object_created,
                "replica_created": replica_result is not None,
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                },
                "transaction": {
                    "status": (
                        "rolled_back"
                        if not ledger_created
                        else "ledger_preserved_after_failure"
                    ),
                    "rolled_back": True,
                    "ledger_created": ledger_created,
                    "rollback": rollback,
                },
            }
