from pathlib import Path
import json
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SCRIPTS_DIR = PROJECT_ROOT / "storage" / "scripts"
PROVIDERS_DIR = PROJECT_ROOT / "storage" / "providers"

sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(PROVIDERS_DIR))

from contributor_registry import ContributorRegistry
from storage_profile_registry import StorageProfileRegistry
from knowledge_object_registry import KnowledgeObjectRegistry
from replica_registry import ReplicaRegistry
from contribution_ledger import ContributionLedger
from provider_registry import create_default_registry
from provider_manager import ProviderManager
from storage_pool_manager import StoragePoolManager
from storage_service import StorageService


with tempfile.TemporaryDirectory(prefix="openelec_storage_service_") as temp_dir:
    temp_dir = Path(temp_dir)

    source = temp_dir / "runtime_source.txt"
    source.write_text(
        "OpenElecBIM StorageService isolated runtime test\n"
        "Knowledge Object -> Replica -> Contribution Ledger\n"
        "SHA-256 integrity verification\n",
        encoding="utf-8",
    )

    provider_root = temp_dir / "mock_provider"
    download_path = temp_dir / "downloaded.txt"

    # --------------------------------------------------------
    # Build isolated registries.
    # --------------------------------------------------------
    contributor_file = temp_dir / "contributors.json"
    profile_file = temp_dir / "profiles.json"
    object_file = temp_dir / "objects.json"
    replica_file = temp_dir / "replicas.json"
    ledger_file = temp_dir / "ledger.json"

    contributor_file.write_text(
        json.dumps(
            {
                "version": 2,
                "project": "OpenElecBIM",
                "storage_providers": {},
                "contributors": [
                    {
                        "contributor_id": "contributor_001",
                        "display_name": "Runtime Contributor",
                        "contributor_type": "individual",
                        "enabled": True,
                        "metadata": {
                            "runtime_only": True,
                        },
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    profile_file.write_text(
        json.dumps(
            {
                "version": 1,
                "project": "OpenElecBIM",
                "storage_profiles": [
                    {
                        "storage_profile_id": "runtime_storage_service_profile",
                        "contributor_id": "contributor_001",
                        "provider": "mock",
                        "display_name": "Runtime StorageService Mock",
                        "account_reference": None,
                        "root_reference": None,
                        "enabled": True,
                        "metadata": {
                            "runtime_only": True,
                        },
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    object_file.write_text(
        json.dumps(
            {
                "version": 1,
                "project": "OpenElecBIM",
                "knowledge_objects": [],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    replica_file.write_text(
        json.dumps(
            {
                "version": 1,
                "project": "OpenElecBIM",
                "replicas": [],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    ledger_file.write_text(
        json.dumps(
            {
                "version": 1,
                "project": "OpenElecBIM",
                "entries": [],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # Build current architecture with isolated registries.
    # --------------------------------------------------------
    pool = StoragePoolManager()

    pool.contributors = ContributorRegistry(
        registry_file=contributor_file
    )

    pool.profiles = StorageProfileRegistry(
        registry_path=profile_file
    )

    pool.objects = KnowledgeObjectRegistry(
        registry_path=object_file
    )

    pool.replicas = ReplicaRegistry(
        registry_path=replica_file
    )

    pool.ledger = ContributionLedger(
        ledger_path=ledger_file
    )

    pool.provider_registry = create_default_registry()

    pool.provider_manager = ProviderManager(
        profile_registry=pool.profiles,
        provider_registry=pool.provider_registry,
    )

    service = StorageService(pool)

    profile_id = "runtime_storage_service_profile"

    # --------------------------------------------------------
    # CREATE TRANSACTION
    # --------------------------------------------------------
    result = service.store_file(
        source,
        contributor_id="contributor_001",
        storage_profile_id=profile_id,
        object_type="document",
        title="Runtime StorageService Test",
        language="en",
        destination="objects/runtime/runtime_source.txt",
        metadata={
            "runtime_test": True,
        },
        provider_kwargs={
            "root_path": str(provider_root),
        },
    )

    print("=" * 80)
    print("STORAGESERVICE CREATE TRANSACTION")
    print("=" * 80)
    print("Success            =", result["success"])
    print("Duplicate          =", result["duplicate"])
    print("Operation          =", result["operation"])
    print("Provider           =", result["provider"])
    print("Object ID          =", result["object_id"])
    print("Replica ID         =", result["replica_id"])
    print("Contribution ID    =", result["contribution_id"])
    print("Content Hash       =", result["content_hash"])

    assert result["success"] is True
    assert result["duplicate"] is False
    assert result["verification"]["hashes_match"] is True
    assert result["verification"]["ledger_entry_valid"] is True
    assert result["verification"]["ledger_chain_valid"] is True

    # --------------------------------------------------------
    # DUPLICATE TRANSACTION
    # --------------------------------------------------------
    duplicate = service.store_file(
        source,
        contributor_id="contributor_001",
        storage_profile_id=profile_id,
        object_type="document",
        title="Runtime StorageService Test",
        language="en",
        destination="objects/runtime/runtime_source.txt",
        metadata={
            "runtime_test": True,
        },
        provider_kwargs={
            "root_path": str(provider_root),
        },
    )

    print()
    print("DUPLICATE DETECTION")
    print("Success            =", duplicate["success"])
    print("Duplicate          =", duplicate["duplicate"])
    print("Status             =", duplicate["transaction"]["status"])

    assert duplicate["success"] is True
    assert duplicate["duplicate"] is True
    assert duplicate["transaction"]["status"] == "already_exists"

    # --------------------------------------------------------
    # DOWNLOAD + INTEGRITY
    # --------------------------------------------------------
    download = service.download_file(
        result["replica_id"],
        download_path,
        provider_kwargs={
            "root_path": str(provider_root),
        },
    )

    print()
    print("=" * 80)
    print("STORAGESERVICE DOWNLOAD VERIFICATION")
    print("=" * 80)
    print("Success            =", download["success"])
    print("Destination        =", download["destination"])
    print("Expected Hash      =", download["expected_hash"])
    print("Downloaded Hash    =", download["downloaded_hash"])
    print("Hashes Match       =", download["hashes_match"])

    assert download["success"] is True
    assert download["hashes_match"] is True
    assert download_path.is_file()

    print()
    print("=" * 80)
    print("STORAGESERVICE FULL ISOLATED TEST = PASS")
    print("=" * 80)
