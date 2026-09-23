from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = PROJECT_ROOT / "storage" / "config" / "storage_profile_registry.json"


class StorageProfileRegistry:
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
            "storage_profiles": []
        }

    def _load(self) -> dict:
        if not self.registry_path.exists():
            data = self._default_registry()
            self._save(data)
            return data

        with self.registry_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("Storage profile registry must be a JSON object.")

        data.setdefault("version", 1)
        data.setdefault("project", "OpenElecBIM")
        data.setdefault("storage_profiles", [])

        if not isinstance(data["storage_profiles"], list):
            raise ValueError("'storage_profiles' must be a list.")

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

    def get_profiles(self) -> list[dict]:
        return list(self.registry.get("storage_profiles", []))

    def get_profile(self, profile_id: str) -> dict | None:
        for profile in self.get_profiles():
            if profile.get("storage_profile_id") == profile_id:
                return profile
        return None

    def find_by_contributor(self, contributor_id: str) -> list[dict]:
        return [
            profile
            for profile in self.get_profiles()
            if profile.get("contributor_id") == contributor_id
        ]

    def register_profile(
        self,
        storage_profile_id: str,
        contributor_id: str,
        provider: str,
        display_name: str,
        account_reference: str | None = None,
        root_reference: str | None = None,
        enabled: bool = True,
        metadata: dict | None = None,
    ) -> dict:

        if self.get_profile(storage_profile_id):
            raise ValueError(
                f"Storage profile already exists: {storage_profile_id}"
            )

        profile = {
            "storage_profile_id": storage_profile_id,
            "contributor_id": contributor_id,
            "provider": provider,
            "display_name": display_name,
            "account_reference": account_reference,
            "root_reference": root_reference,
            "enabled": enabled,
            "created_at": self.utc_now(),
            "updated_at": self.utc_now(),
            "metadata": metadata or {}
        }

        self.registry["storage_profiles"].append(profile)
        self._save()

        return profile

    def update_enabled(
        self,
        storage_profile_id: str,
        enabled: bool,
    ) -> dict:

        profile = self.get_profile(storage_profile_id)

        if profile is None:
            raise KeyError(
                f"Storage profile not found: {storage_profile_id}"
            )

        profile["enabled"] = enabled
        profile["updated_at"] = self.utc_now()
        self._save()

        return profile

    def unregister_profile(self, storage_profile_id: str) -> dict:
        profiles = self.registry["storage_profiles"]

        for index, profile in enumerate(profiles):
            if profile.get("storage_profile_id") == storage_profile_id:
                removed = profiles.pop(index)
                self._save()
                return removed

        raise KeyError(
            f"Storage profile not found: {storage_profile_id}"
        )


if __name__ == "__main__":
    registry = StorageProfileRegistry()

    print("STORAGE PROFILE REGISTRY = OK")
    print("Registry Version =", registry.registry["version"])
    print("Registered Profiles =", len(registry.get_profiles()))
