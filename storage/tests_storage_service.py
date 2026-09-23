from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from storage.scripts.storage_pool_manager import StoragePoolManager
from storage.providers.mock_provider import MockStorageProvider
from storage.scripts.storage_service import StorageService


TEST_SOURCE = PROJECT_ROOT / "storage" / "tests" / "end_to_end_source.txt"
TEST_SOURCE.parent.mkdir(parents=True, exist_ok=True)

TEST_SOURCE.write_text(
    "OpenElecBIM End-to-End Storage Transaction Test\n"
    "Electrical BIM Knowledge Object\n"
    "SHA-256 integrity test\n",
    encoding="utf-8",
)

MOCK_ROOT = (
    PROJECT_ROOT
    / "storage"
    / "tests"
    / "e2e_mock_storage"
)

MOCK_ROOT.mkdir(parents=True, exist_ok=True)

pool = StoragePoolManager()

pool.provider_registry.unregister("google_drive")
pool.provider_registry.register(
    "google_drive",
    MockStorageProvider,
)

service = StorageService(pool)

result = service.store_file(
    TEST_SOURCE,
    contributor_id="contributor_001",
    storage_profile_id="storage_profile_test_001",
    object_type="document",
    title="OpenElecBIM End-to-End Test",
    language="en",
    destination="objects/e2e/end_to_end_source.txt",
    metadata={
        "test": True,
        "stage": "end_to_end_storage",
    },
    provider_kwargs={
        "root_path": str(MOCK_ROOT),
    },
)

print()
print("========================================")
print("OPEN ELECBIM END-TO-END STORAGE TEST")
print("========================================")
print("Success              =", result["success"])
print("Provider             =", result["provider"])
print("Object ID            =", result["object"]["object_id"])
print("Replica ID           =", result["replica"]["replica_id"])
if result.get("duplicate", False):
    print("Contribution ID      = None (existing transaction)")
    print("Content SHA-256      =", result["content_hash"])
    print("Transaction Status   =", result["transaction"]["status"])
    print("Duplicate            =", result["duplicate"])
else:
    print("Contribution ID      =", result["contribution"]["contribution_id"])
    print("Content SHA-256      =", result["verification"]["content_hash"])
    print("Object Hash          =", result["verification"]["object_hash"])
    print("Replica Hash         =", result["verification"]["replica_hash"])
    print("Ledger Hash          =", result["verification"]["ledger_hash"])
    print("Hashes Match         =", result["verification"]["hashes_match"])
    print("Ledger Entry Valid   =", result["verification"]["ledger_entry_valid"])
    print("Ledger Chain Valid   =", result["verification"]["ledger_chain_valid"])
print("========================================")

if not result["success"]:
    raise SystemExit("END-TO-END TEST FAILED")

print("END-TO-END STORAGE TEST = PASS")
