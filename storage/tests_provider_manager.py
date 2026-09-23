from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STORAGE_DIR = PROJECT_ROOT / "storage"
PROVIDERS_DIR = STORAGE_DIR / "providers"
SCRIPTS_DIR = STORAGE_DIR / "scripts"

sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(PROVIDERS_DIR))

from storage_profile_registry import StorageProfileRegistry
from provider_registry import create_default_registry
from provider_manager import ProviderManager
from mock_provider import MockStorageProvider


profile_registry = StorageProfileRegistry()
provider_registry = create_default_registry()

# Temporary test mapping:
# existing profile = google_drive
# actual implementation = mock
if not provider_registry.has("google_drive"):
    provider_registry.register(
        "google_drive",
        MockStorageProvider,
    )

manager = ProviderManager(
    profile_registry=profile_registry,
    provider_registry=provider_registry,
)

profile_id = "storage_profile_test_001"

provider = manager.get_provider(
    profile_id,
    root_path=PROJECT_ROOT
    / "storage"
    / "tests"
    / "manager_mock_storage",
)

assert provider.provider_name == "mock"
assert provider.connected is True
assert manager.has_provider(profile_id) is True

# The manager should return the same cached instance.
provider_again = manager.get_provider(
    profile_id,
    root_path=PROJECT_ROOT
    / "storage"
    / "tests"
    / "manager_mock_storage",
)

assert provider_again is provider

active = manager.active_profiles()

assert profile_id in active

print("PROVIDER MANAGER = OK")
print("Profile ID =", profile_id)
print("Provider =", provider.provider_name)
print("Connected =", provider.connected)
print("Cached Same Instance =", provider_again is provider)
print("Active Profiles =", active)

assert manager.disconnect(profile_id) is True
assert manager.has_provider(profile_id) is False

print("Disconnect = OK")
print("PROVIDER MANAGER TEST = PASS")
