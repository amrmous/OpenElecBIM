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
from provider_resolver import ProviderResolver


profile_registry = StorageProfileRegistry()
provider_registry = create_default_registry()

resolver = ProviderResolver(
    profile_registry=profile_registry,
    provider_registry=provider_registry,
)

profile_id = "storage_profile_test_001"

profile = profile_registry.get_profile(profile_id)

assert profile is not None
assert profile["provider"] == "google_drive"

print("PROFILE FOUND = OK")
print("Profile ID =", profile["storage_profile_id"])
print("Provider =", profile["provider"])

# The existing test profile says google_drive.
# For this architecture test, register a temporary mock factory
# under the same provider name to prove profile -> provider resolution.
from mock_provider import MockStorageProvider

if not provider_registry.has("google_drive"):
    provider_registry.register(
        "google_drive",
        MockStorageProvider,
    )

provider = resolver.resolve(
    profile_id,
    root_path=PROJECT_ROOT / "storage" / "tests" / "resolver_mock_storage",
)

assert provider.provider_name == "mock"

assert provider.connect() is True

print("RESOLVER = OK")
print("Resolved Provider =", provider.provider_name)
print("Connected =", provider.connected)
print("PROFILE -> PROVIDER TEST = PASS")
