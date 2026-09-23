from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SCRIPTS_DIR = PROJECT_ROOT / "storage" / "scripts"
PROVIDERS_DIR = PROJECT_ROOT / "storage" / "providers"

sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(PROVIDERS_DIR))

from storage_pool_manager import StoragePoolManager
from mock_provider import MockStorageProvider


pool = StoragePoolManager()

profile_id = "storage_profile_test_001"

profile = pool.get_profile(profile_id)

assert profile is not None
assert profile["provider"] == "google_drive"

# Temporary test mapping:
# Google Drive profile -> Mock implementation.
if not pool.provider_registry.has("google_drive"):
    pool.provider_registry.register(
        "google_drive",
        MockStorageProvider,
    )

provider = pool.get_provider(
    profile_id,
    root_path=PROJECT_ROOT
    / "storage"
    / "tests"
    / "pool_provider_mock_storage",
)

assert provider.provider_name == "mock"
assert provider.connected is True

summary = pool.get_pool_summary()

assert summary["active_provider_profiles"] == 1

print("POOL PROVIDER INTEGRATION = OK")
print("Profile ID =", profile_id)
print("Profile Provider =", profile["provider"])
print("Runtime Provider =", provider.provider_name)
print("Connected =", provider.connected)
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

assert graph["valid"] is True

print("Existing Storage Graph =", graph["valid"])
print("POOL + PROVIDER INTEGRATION TEST = PASS")
