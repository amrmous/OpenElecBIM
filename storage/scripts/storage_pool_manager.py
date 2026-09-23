from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SCRIPTS_DIR = PROJECT_ROOT / "storage" / "scripts"
PROVIDERS_DIR = PROJECT_ROOT / "storage" / "providers"

for path in (SCRIPTS_DIR, PROVIDERS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


from contributor_registry import ContributorRegistry
from storage_profile_registry import StorageProfileRegistry
from knowledge_object_registry import KnowledgeObjectRegistry
from replica_registry import ReplicaRegistry
from contribution_ledger import ContributionLedger

from provider_registry import create_default_registry
from provider_manager import ProviderManager


class StoragePoolManager:
    def __init__(self):
        self.contributors = ContributorRegistry()
        self.profiles = StorageProfileRegistry()
        self.objects = KnowledgeObjectRegistry()
        self.replicas = ReplicaRegistry()
        self.ledger = ContributionLedger()

        self.provider_registry = create_default_registry()

        self.provider_manager = ProviderManager(
            profile_registry=self.profiles,
            provider_registry=self.provider_registry,
        )

    def get_contributor(self, contributor_id: str) -> dict | None:
        return self.contributors.get_contributor(contributor_id)

    def get_profile(self, storage_profile_id: str) -> dict | None:
        return self.profiles.get_profile(storage_profile_id)

    def get_object(self, object_id: str) -> dict | None:
        return self.objects.get_object(object_id)

    def get_replica(self, replica_id: str) -> dict | None:
        return self.replicas.get_replica(replica_id)

    def get_contribution(self, contribution_id: str) -> dict | None:
        return self.ledger.get_entry(contribution_id)

    def get_provider(
        self,
        storage_profile_id: str,
        *,
        connect: bool = True,
        **provider_kwargs,
    ):
        """
        Resolve and return the runtime provider for a storage profile.
        """
        profile = self.get_profile(storage_profile_id)

        if profile is None:
            raise ValueError(
                f"Storage profile not found: {storage_profile_id}"
            )

        if not profile.get("enabled", False):
            raise ValueError(
                f"Storage profile is disabled: {storage_profile_id}"
            )

        return self.provider_manager.get_provider(
            storage_profile_id,
            connect=connect,
            **provider_kwargs,
        )

    def validate_contributor(self, contributor_id: str) -> dict:
        contributor = self.get_contributor(contributor_id)

        if contributor is None:
            raise ValueError(
                f"Contributor not found: {contributor_id}"
            )

        if not contributor.get("enabled", False):
            raise ValueError(
                f"Contributor is disabled: {contributor_id}"
            )

        return contributor

    def validate_profile(
        self,
        storage_profile_id: str,
        contributor_id: str,
    ) -> dict:

        profile = self.get_profile(storage_profile_id)

        if profile is None:
            raise ValueError(
                f"Storage profile not found: {storage_profile_id}"
            )

        if profile.get("contributor_id") != contributor_id:
            raise ValueError(
                "Storage profile does not belong to contributor."
            )

        if not profile.get("enabled", False):
            raise ValueError(
                f"Storage profile is disabled: {storage_profile_id}"
            )

        return profile

    def validate_object(self, object_id: str) -> dict:
        obj = self.get_object(object_id)

        if obj is None:
            raise ValueError(
                f"Knowledge object not found: {object_id}"
            )

        return obj

    def validate_replica(
        self,
        replica_id: str,
        object_id: str,
        contributor_id: str,
        storage_profile_id: str,
    ) -> dict:

        replica = self.get_replica(replica_id)

        if replica is None:
            raise ValueError(
                f"Replica not found: {replica_id}"
            )

        if replica.get("object_id") != object_id:
            raise ValueError(
                "Replica does not belong to knowledge object."
            )

        if replica.get("contributor_id") != contributor_id:
            raise ValueError(
                "Replica does not belong to contributor."
            )

        if replica.get("storage_profile_id") != storage_profile_id:
            raise ValueError(
                "Replica does not belong to storage profile."
            )

        return replica

    def validate_contribution_chain(
        self,
        contribution_id: str,
        contributor_id: str,
        object_id: str,
        replica_id: str,
        storage_profile_id: str,
    ) -> dict:

        entry = self.get_contribution(contribution_id)

        if entry is None:
            raise ValueError(
                f"Contribution not found: {contribution_id}"
            )

        if entry.get("contributor_id") != contributor_id:
            raise ValueError(
                "Contribution contributor mismatch."
            )

        if entry.get("object_id") != object_id:
            raise ValueError(
                "Contribution object mismatch."
            )

        if entry.get("replica_id") != replica_id:
            raise ValueError(
                "Contribution replica mismatch."
            )

        if entry.get("storage_profile_id") != storage_profile_id:
            raise ValueError(
                "Contribution storage profile mismatch."
            )

        if not self.ledger.verify_entry(contribution_id):
            raise ValueError(
                "Contribution entry hash is invalid."
            )

        if not self.ledger.verify_chain():
            raise ValueError(
                "Contribution ledger chain is invalid."
            )

        return entry

    def validate_storage_graph(
        self,
        contributor_id: str,
        storage_profile_id: str,
        object_id: str,
        replica_id: str,
        contribution_id: str,
    ) -> dict:

        contributor = self.validate_contributor(contributor_id)

        profile = self.validate_profile(
            storage_profile_id,
            contributor_id,
        )

        obj = self.validate_object(object_id)

        replica = self.validate_replica(
            replica_id,
            object_id,
            contributor_id,
            storage_profile_id,
        )

        contribution = self.validate_contribution_chain(
            contribution_id,
            contributor_id,
            object_id,
            replica_id,
            storage_profile_id,
        )

        return {
            "valid": True,
            "contributor": contributor,
            "storage_profile": profile,
            "knowledge_object": obj,
            "replica": replica,
            "contribution": contribution,
        }

    def get_pool_summary(self) -> dict:
        return {
            "contributors": len(
                self.contributors.get_contributors()
            ),
            "storage_profiles": len(
                self.profiles.get_profiles()
            ),
            "knowledge_objects": len(
                self.objects.get_objects()
            ),
            "replicas": len(
                self.replicas.get_replicas()
            ),
            "contributions": len(
                self.ledger.get_entries()
            ),
            "ledger_chain_valid": self.ledger.verify_chain(),
            "active_provider_profiles": len(
                self.provider_manager.active_profiles()
            ),
        }


if __name__ == "__main__":
    pool = StoragePoolManager()

    print("STORAGE POOL MANAGER = OK")

    summary = pool.get_pool_summary()

    print("Contributors =", summary["contributors"])
    print("Storage Profiles =", summary["storage_profiles"])
    print("Knowledge Objects =", summary["knowledge_objects"])
    print("Replicas =", summary["replicas"])
    print("Contributions =", summary["contributions"])
    print("Ledger Chain Valid =", summary["ledger_chain_valid"])
    print(
        "Active Provider Profiles =",
        summary["active_provider_profiles"],
    )

    graph = pool.validate_storage_graph(
        contributor_id="contributor_001",
        storage_profile_id="storage_profile_test_001",
        object_id="knowledge_object_test_001",
        replica_id="replica_test_001",
        contribution_id="contribution_test_001",
    )

    print("STORAGE GRAPH VALID =", graph["valid"])
