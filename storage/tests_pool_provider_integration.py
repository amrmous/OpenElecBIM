from pathlib import Path
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SCRIPTS_DIR = PROJECT_ROOT / "storage" / "scripts"
PROVIDERS_DIR = PROJECT_ROOT / "storage" / "providers"

sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(PROVIDERS_DIR))

from storage_pool_manager import StoragePoolManager


pool = StoragePoolManager()

profile_id = "runtime_pool_mock_profile"

# Temporary runtime profile.
# It is added only to the in-memory registry and is never saved.
pool.profiles.registry["storage_profiles"].append(
    {
        "storage_profile_id": profile_id,
        "contributor_id": "contributor_001",
        "provider": "mock",
        "display_name": "Runtime Pool Mock",
        "account_reference": None,
        "root_reference": None,
        "enabled": True,
        "metadata": {
            "runtime_only": True,
        },
    }
)

with tempfile.TemporaryDirectory(prefix="openelec_pool_test_") as temp_dir:
    provider = pool.get_provider(
        profile_id,
        connect=True,
        root_path=temp_dir,
    )

    assert provider.provider_name == "mock"
    assert provider.connected is True

    summary = pool.get_pool_summary()

    assert summary["active_provider_profiles"] == 1

    print("POOL PROVIDER INTEGRATION = OK")
    print("Profile ID =", profile_id)
    print("Runtime Provider =", provider.provider_name)
    print("Connected =", provider.connected)
    print(
        "Active Provider Profiles =",
        summary["active_provider_profiles"],
    )

# ------------------------------------------------------------
# Validate one current, known-good Google Drive graph.
# No Google connection is required for graph validation.
# ------------------------------------------------------------
graph = pool.validate_storage_graph(
    contributor_id="contributor_001",
    storage_profile_id="storage_profile_google_drive_001",
    object_id="knowledge_object_15ee39008a544900adde3574d8e480ca",
    replica_id="replica_44b7a15817f64092bb165ddb7e199129",
    contribution_id="contribution_347d7537e04e490d910c0b917ee358c2",
)

assert graph["valid"] is True

print()
print("CURRENT STORAGE GRAPH = VALID")
print("Contributor =", graph["contributor"]["contributor_id"])
print(
    "Profile =",
    graph["storage_profile"]["storage_profile_id"],
)
print(
    "Object =",
    graph["knowledge_object"]["object_id"],
)
print("Replica =", graph["replica"]["replica_id"])
print(
    "Contribution =",
    graph["contribution"]["contribution_id"],
)

print("POOL + PROVIDER INTEGRATION TEST = PASS")
