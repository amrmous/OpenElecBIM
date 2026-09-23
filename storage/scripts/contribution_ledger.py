from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = PROJECT_ROOT / "storage" / "config" / "contribution_ledger.json"


class ContributionLedger:
    def __init__(self, ledger_path: Path | None = None):
        self.ledger_path = Path(ledger_path or LEDGER_PATH)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger = self._load()

    @staticmethod
    def utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def calculate_entry_hash(entry: dict) -> str:
        payload = {
            "contribution_id": entry["contribution_id"],
            "contributor_id": entry["contributor_id"],
            "object_id": entry["object_id"],
            "replica_id": entry["replica_id"],
            "storage_profile_id": entry["storage_profile_id"],
            "action": entry["action"],
            "content_hash": entry["content_hash"],
            "timestamp": entry["timestamp"],
            "previous_entry_hash": entry["previous_entry_hash"],
        }

        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _default_ledger(self) -> dict:
        return {
            "version": 1,
            "project": "OpenElecBIM",
            "entries": []
        }

    def _load(self) -> dict:
        if not self.ledger_path.exists():
            data = self._default_ledger()
            self._save(data)
            return data

        with self.ledger_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("Contribution ledger must be a JSON object.")

        data.setdefault("version", 1)
        data.setdefault("project", "OpenElecBIM")
        data.setdefault("entries", [])

        if not isinstance(data["entries"], list):
            raise ValueError("'entries' must be a list.")

        return data

    def _save(self, data: dict | None = None) -> None:
        if data is not None:
            self.ledger = data

        temp_path = self.ledger_path.with_suffix(".tmp")

        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(
                self.ledger,
                f,
                ensure_ascii=False,
                indent=2,
            )
            f.write("\n")

        temp_path.replace(self.ledger_path)

    def reload(self) -> None:
        self.ledger = self._load()

    def get_entries(self) -> list[dict]:
        return list(self.ledger.get("entries", []))

    def get_entry(self, contribution_id: str) -> dict | None:
        for entry in self.get_entries():
            if entry.get("contribution_id") == contribution_id:
                return entry
        return None

    def find_by_contributor(self, contributor_id: str) -> list[dict]:
        return [
            entry
            for entry in self.get_entries()
            if entry.get("contributor_id") == contributor_id
        ]

    def find_by_object(self, object_id: str) -> list[dict]:
        return [
            entry
            for entry in self.get_entries()
            if entry.get("object_id") == object_id
        ]

    def _get_previous_hash(self) -> str | None:
        entries = self.get_entries()

        if not entries:
            return None

        return entries[-1].get("entry_hash")

    def record_contribution(
        self,
        contribution_id: str,
        contributor_id: str,
        object_id: str,
        replica_id: str,
        storage_profile_id: str,
        action: str,
        content_hash: str,
        metadata: dict | None = None,
    ) -> dict:

        if self.get_entry(contribution_id):
            raise ValueError(
                f"Contribution already exists: {contribution_id}"
            )

        timestamp = self.utc_now()
        previous_entry_hash = self._get_previous_hash()

        entry = {
            "contribution_id": contribution_id,
            "contributor_id": contributor_id,
            "object_id": object_id,
            "replica_id": replica_id,
            "storage_profile_id": storage_profile_id,
            "action": action,
            "content_hash": content_hash,
            "timestamp": timestamp,
            "previous_entry_hash": previous_entry_hash,
            "metadata": metadata or {},
        }

        entry["entry_hash"] = self.calculate_entry_hash(entry)

        self.ledger["entries"].append(entry)
        self._save()

        return entry

    def verify_entry(self, contribution_id: str) -> bool:
        entry = self.get_entry(contribution_id)

        if entry is None:
            return False

        expected_hash = self.calculate_entry_hash(entry)

        return expected_hash == entry.get("entry_hash")

    def verify_chain(self) -> bool:
        previous_hash = None

        for entry in self.get_entries():
            if entry.get("previous_entry_hash") != previous_hash:
                return False

            expected_hash = self.calculate_entry_hash(entry)

            if expected_hash != entry.get("entry_hash"):
                return False

            previous_hash = entry.get("entry_hash")

        return True


if __name__ == "__main__":
    ledger = ContributionLedger()

    print("CONTRIBUTION LEDGER = OK")
    print("Ledger Version =", ledger.ledger["version"])
    print("Registered Contributions =", len(ledger.get_entries()))
    print("Chain Valid =", ledger.verify_chain())
