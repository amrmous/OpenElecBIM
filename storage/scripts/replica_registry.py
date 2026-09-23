from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = PROJECT_ROOT / "storage" / "config" / "replica_registry.json"


class ReplicaRegistry:
    def __init__(self, registry_path: Path | None = None):
        self.registry_path = Path(registry_path or REGISTRY_PATH)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry = self._load()

    @staticmethod
    def utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _default_registry(self) -> dict:
        return {
            "version": 1,
            "project": "OpenElecBIM",
            "replicas": []
        }

    def _load(self) -> dict:
        if not self.registry_path.exists():
            data = self._default_registry()
            self._save(data)
            return data

        with self.registry_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("Replica registry must be a JSON object.")

        data.setdefault("version", 1)
        data.setdefault("project", "OpenElecBIM")
        data.setdefault("replicas", [])

        if not isinstance(data["replicas"], list):
            raise ValueError("'replicas' must be a list.")

        return data

    def _save(self, data: dict | None = None) -> None:
        if data is not None:
            self.registry = data

        temp_path = self.registry_path.with_suffix(".tmp")

        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(self.registry, f, ensure_ascii=False, indent=2)
            f.write("\n")

        temp_path.replace(self.registry_path)

    def reload(self) -> None:
        self.registry = self._load()

    def get_replicas(self) -> list[dict]:
        return list(self.registry.get("replicas", []))

    def get_replica(self, replica_id: str) -> dict | None:
        for replica in self.get_replicas():
            if replica.get("replica_id") == replica_id:
                return replica
        return None

    def find_by_object(self, object_id: str) -> list[dict]:
        return [
            replica
            for replica in self.get_replicas()
            if replica.get("object_id") == object_id
        ]

    def register_replica(
        self,
        replica_id: str,
        object_id: str,
        contributor_id: str,
        storage_profile_id: str,
        provider: str,
        reference: str,
        content_hash: str,
        hash_algorithm: str = "sha256",
        status: str = "active",
        metadata: dict | None = None,
    ) -> dict:
        if self.get_replica(replica_id):
            raise ValueError(f"Replica already exists: {replica_id}")

        replica = {
            "replica_id": replica_id,
            "object_id": object_id,
            "contributor_id": contributor_id,
            "storage_profile_id": storage_profile_id,
            "provider": provider,
            "reference": reference,
            "status": status,
            "content_hash": content_hash,
            "hash_algorithm": hash_algorithm,
            "created_at": self.utc_now(),
            "updated_at": self.utc_now(),
            "metadata": metadata or {}
        }

        self.registry["replicas"].append(replica)
        self._save()

        return replica

    def update_status(self, replica_id: str, status: str) -> dict:
        replica = self.get_replica(replica_id)

        if replica is None:
            raise KeyError(f"Replica not found: {replica_id}")

        replica["status"] = status
        replica["updated_at"] = self.utc_now()
        self._save()

        return replica

    def unregister_replica(self, replica_id: str) -> dict:
        replicas = self.registry["replicas"]

        for index, replica in enumerate(replicas):
            if replica.get("replica_id") == replica_id:
                removed = replicas.pop(index)
                self._save()
                return removed

        raise KeyError(f"Replica not found: {replica_id}")


if __name__ == "__main__":
    registry = ReplicaRegistry()

    print("REPLICA REGISTRY = OK")
    print("Registry Version =", registry.registry["version"])
    print("Registered Replicas =", len(registry.get_replicas()))
