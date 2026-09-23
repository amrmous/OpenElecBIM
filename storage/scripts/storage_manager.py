import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

REGISTRY_FILE = (
    PROJECT_ROOT
    / "storage"
    / "config"
    / "storage_registry.json"
)

LOCAL_CONFIG_FILE = (
    PROJECT_ROOT
    / "storage"
    / "config"
    / "storage.local.json"
)


class StorageManager:
    def __init__(
        self,
        registry_file=REGISTRY_FILE,
        local_config_file=LOCAL_CONFIG_FILE,
    ):
        self.registry_file = Path(registry_file)
        self.local_config_file = Path(local_config_file)

        self.registry = self._load_json(self.registry_file)
        self.local_config = self._load_local_config()

    def _load_json(self, file_path):
        if not file_path.exists():
            raise FileNotFoundError(
                f"Storage configuration not found: {file_path}"
            )

        with file_path.open("r", encoding="utf-8-sig") as file:
            return json.load(file)

    def _load_local_config(self):
        if not self.local_config_file.exists():
            return {
                "version": 1,
                "contributors": {}
            }

        return self._load_json(self.local_config_file)

    def reload(self):
        self.registry = self._load_json(self.registry_file)
        self.local_config = self._load_local_config()
        return self.registry

    # ---------------------------------------------------------
    # Public registry
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Local private configuration
    # ---------------------------------------------------------

    def get_local_contributors(self):
        return self.local_config.get("contributors", {})

    def get_local_contributor(self, contributor_id):
        return self.get_local_contributors().get(
            contributor_id,
            {}
        )

    def get_local_profiles(self, contributor_id="local_owner"):
        contributor = self.get_local_contributor(contributor_id)

        return contributor.get("storage_profiles", [])

    def get_local_profile(
        self,
        profile_id,
        contributor_id="local_owner",
    ):
        profiles = self.get_local_profiles(contributor_id)

        for profile in profiles:
            if profile.get("profile_id") == profile_id:
                return profile

        return None

    def get_enabled_local_profiles(
        self,
        contributor_id="local_owner",
    ):
        return [
            profile
            for profile in self.get_local_profiles(contributor_id)
            if profile.get("enabled", False)
        ]

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    def get_summary(self):
        return {
            "version": self.get_version(),
            "providers": list(self.get_providers().keys()),
            "contributors": len(self.get_contributors()),
            "public_profiles": len(self.get_all_profiles()),
            "local_profiles": len(
                self.get_local_profiles()
            ),
            "enabled_local_profiles": len(
                self.get_enabled_local_profiles()
            ),
        }


if __name__ == "__main__":
    manager = StorageManager()
    summary = manager.get_summary()

    print("STORAGE MANAGER = OK")
    print("Registry Version =", summary["version"])
    print("Providers =", summary["providers"])
    print("Public Contributors =", summary["contributors"])
    print("Public Storage Profiles =", summary["public_profiles"])
    print("Local Storage Profiles =", summary["local_profiles"])
    print("Enabled Local Profiles =", summary["enabled_local_profiles"])

    print()
    print("LOCAL PROFILES")

    for profile in manager.get_enabled_local_profiles():
        print(
            "-",
            profile.get("profile_id"),
            "|",
            profile.get("provider"),
            "|",
            profile.get("account_email"),
        )