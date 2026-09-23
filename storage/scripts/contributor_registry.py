import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

REGISTRY_FILE = (
    PROJECT_ROOT
    / "storage"
    / "config"
    / "storage_registry.json"
)


class ContributorRegistry:
    def __init__(self, registry_file=REGISTRY_FILE):
        self.registry_file = Path(registry_file)
        self.registry = self._load()

    def _load(self):
        if not self.registry_file.exists():
            raise FileNotFoundError(
                f"Storage registry not found: {self.registry_file}"
            )

        with self.registry_file.open("r", encoding="utf-8-sig") as file:
            return json.load(file)

    def _save(self):
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

        with self.registry_file.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as file:
            json.dump(
                self.registry,
                file,
                ensure_ascii=False,
                indent=2,
            )
            file.write("\n")

    @staticmethod
    def utc_now():
        return datetime.now(timezone.utc).isoformat()

    def reload(self):
        self.registry = self._load()
        return self.registry

    def get_contributors(self):
        contributors = self.registry.get("contributors", [])

        if not isinstance(contributors, list):
            raise ValueError(
                "storage_registry.json: contributors must be a list"
            )

        return contributors

    def get_contributor(self, contributor_id):
        for contributor in self.get_contributors():
            if contributor.get("contributor_id") == contributor_id:
                return contributor

        return None

    def exists(self, contributor_id):
        return self.get_contributor(contributor_id) is not None

    def register_contributor(
        self,
        contributor_id,
        display_name,
        contributor_type="individual",
        metadata=None,
    ):
        contributor_id = str(contributor_id).strip()
        display_name = str(display_name).strip()

        if not contributor_id:
            raise ValueError("contributor_id cannot be empty")

        if not display_name:
            raise ValueError("display_name cannot be empty")

        if self.exists(contributor_id):
            raise ValueError(
                f"Contributor already exists: {contributor_id}"
            )

        contributor = {
            "contributor_id": contributor_id,
            "display_name": display_name,
            "contributor_type": contributor_type,
            "enabled": True,
            "created_at": self.utc_now(),
            "metadata": metadata or {},
        }

        self.registry.setdefault("contributors", [])

        if not isinstance(self.registry["contributors"], list):
            raise ValueError(
                "storage_registry.json: contributors must be a list"
            )

        self.registry["contributors"].append(contributor)
        self._save()

        return contributor

    def update_contributor(
        self,
        contributor_id,
        display_name=None,
        contributor_type=None,
        enabled=None,
        metadata=None,
    ):
        contributor = self.get_contributor(contributor_id)

        if contributor is None:
            raise KeyError(
                f"Contributor not found: {contributor_id}"
            )

        if display_name is not None:
            contributor["display_name"] = str(display_name).strip()

        if contributor_type is not None:
            contributor["contributor_type"] = str(
                contributor_type
            ).strip()

        if enabled is not None:
            contributor["enabled"] = bool(enabled)

        if metadata is not None:
            contributor["metadata"] = metadata

        contributor["updated_at"] = self.utc_now()

        self._save()

        return contributor

    def unregister_contributor(self, contributor_id):
        contributors = self.get_contributors()

        for index, contributor in enumerate(contributors):
            if contributor.get("contributor_id") == contributor_id:
                removed = contributors.pop(index)
                self._save()
                return removed

        raise KeyError(
            f"Contributor not found: {contributor_id}"
        )


if __name__ == "__main__":
    registry = ContributorRegistry()

    print("CONTRIBUTOR REGISTRY = OK")
    print("Registry Version =", registry.registry.get("version"))
    print(
        "Registered Contributors =",
        len(registry.get_contributors()),
    )
