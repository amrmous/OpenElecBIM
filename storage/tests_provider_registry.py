from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROVIDERS_DIR = PROJECT_ROOT / "storage" / "providers"

sys.path.insert(0, str(PROVIDERS_DIR))

from provider_registry import create_default_registry


TEST_ROOT = PROJECT_ROOT / "storage" / "tests" / "registry_mock_storage"

registry = create_default_registry()

print("PROVIDER REGISTRY = OK")
print("Registered Providers =", registry.names())

assert registry.has("mock") is True
assert registry.has("MOCK") is True

provider = registry.create(
    "mock",
    root_path=TEST_ROOT,
)

assert provider.provider_name == "mock"

connected = provider.connect()

assert connected is True
assert provider.connected is True

print("Has mock =", registry.has("mock"))
print("Created Provider =", provider.provider_name)
print("Connected =", provider.connected)
print("Registry Test = PASS")
