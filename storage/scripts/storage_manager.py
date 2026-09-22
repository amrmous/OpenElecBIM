import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_FILE = PROJECT_ROOT / "storage" / "config" / "storage_registry.json"


class StorageManager:
    def __init__(self, registry_file=REGISTRY_FILE):
        self.registry_file = Path(registry_file)
        self.registry = self._load_registry()

    def _load_registry(self):
        if not self.registry_file.exists():
            raise FileNotFoundError(
                f"Storage registry not found: {self.registry_file}"
            )

        with self.registry_file.open("r", encoding="utf-8-sig") as file:
            return json.load(file)

    def reload(self):
        self.registry = self._load_registry()
        return self.registry

    def get_version(self):
        return self.registry.get("version")

    def get_providers(self):
        return self.registry.get("storage_providers", {})

    def get_contributors(self):
        return self.registry.get("contributors", [])

    def get_provider(self, provider_name):
        return self.get_providers().get(provider_name)

    def get_provider_profiles(self, provider_name):
        provider = self.get_provider(provider_name)

        if not provider:
            return []

        return provider.get("profiles", [])

    def get_all_profiles(self):
        profiles = []

        for provider_name, provider in self.get_providers().items():
            for profile in provider.get("profiles", []):
                item = dict(profile)
                item["provider"] = provider_name
                profiles.append(item)

        return profiles

    def get_summary(self):
        return {
            "version": self.get_version(),
            "providers": list(self.get_providers().keys()),
            "contributors": len(self.get_contributors()),
            "profiles": len(self.get_all_profiles()),
        }


if __name__ == "__main__":
    manager = StorageManager()
    summary = manager.get_summary()

    print("STORAGE MANAGER = OK")
    print("Registry Version =", summary["version"])
    print("Providers =", summary["providers"])
    print("Contributors =", summary["contributors"])
    print("Storage Profiles =", summary["profiles"])