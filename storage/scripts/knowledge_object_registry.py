from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = PROJECT_ROOT / "storage" / "config" / "knowledge_object_registry.json"


class KnowledgeObjectRegistry:
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
            "knowledge_objects": []
        }

    def _load(self) -> dict:
        if not self.registry_path.exists():
            data = self._default_registry()
            self._save(data)
            return data

        with self.registry_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("Knowledge object registry must be a JSON object.")

        data.setdefault("version", 1)
        data.setdefault("project", "OpenElecBIM")
        data.setdefault("knowledge_objects", [])

        if not isinstance(data["knowledge_objects"], list):
            raise ValueError("'knowledge_objects' must be a list.")

        return data

    def _save(self, data: dict | None = None) -> None:
        if data is not None:
            self.registry = data

        temp_path = self.registry_path.with_suffix(".tmp")

        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(
                self.registry,
                f,
                ensure_ascii=False,
                indent=2,
            )
            f.write("\n")

        temp_path.replace(self.registry_path)

    def reload(self) -> None:
        self.registry = self._load()

    def get_objects(self) -> list[dict]:
        return list(self.registry.get("knowledge_objects", []))

    def get_object(self, object_id: str) -> dict | None:
        for obj in self.get_objects():
            if obj.get("object_id") == object_id:
                return obj
        return None

    def find_by_hash(self, content_hash: str) -> list[dict]:
        return [
            obj
            for obj in self.get_objects()
            if obj.get("content_hash") == content_hash
        ]

    def find_by_type(self, object_type: str) -> list[dict]:
        return [
            obj
            for obj in self.get_objects()
            if obj.get("object_type") == object_type
        ]

    def register_object(
        self,
        object_id: str,
        object_type: str,
        title: str,
        content_hash: str,
        source: str | None = None,
        version: int = 1,
        language: str | None = None,
        metadata: dict | None = None,
    ) -> dict:

        if self.get_object(object_id):
            raise ValueError(
                f"Knowledge object already exists: {object_id}"
            )

        if self.find_by_hash(content_hash):
            raise ValueError(
                f"An object with this content hash already exists: {content_hash}"
            )

        now = self.utc_now()

        obj = {
            "object_id": object_id,
            "object_type": object_type,
            "title": title,
            "source": source,
            "content_hash": content_hash,
            "version": version,
            "language": language,
            "created_at": now,
            "updated_at": now,
            "metadata": metadata or {},
        }

        self.registry["knowledge_objects"].append(obj)
        self._save()

        return obj

    def update_metadata(
        self,
        object_id: str,
        metadata: dict,
    ) -> dict:

        obj = self.get_object(object_id)

        if obj is None:
            raise KeyError(
                f"Knowledge object not found: {object_id}"
            )

        obj["metadata"] = metadata
        obj["updated_at"] = self.utc_now()
        self._save()

        return obj

    def unregister_object(self, object_id: str) -> dict:
        objects = self.registry["knowledge_objects"]

        for index, obj in enumerate(objects):
            if obj.get("object_id") == object_id:
                removed = objects.pop(index)
                self._save()
                return removed

        raise KeyError(
            f"Knowledge object not found: {object_id}"
        )


if __name__ == "__main__":
    registry = KnowledgeObjectRegistry()

    print("KNOWLEDGE OBJECT REGISTRY = OK")
    print("Registry Version =", registry.registry["version"])
    print("Registered Objects =", len(registry.get_objects()))
