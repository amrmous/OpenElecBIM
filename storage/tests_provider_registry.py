from pathlib import Path
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SCRIPTS_DIR = PROJECT_ROOT / "storage" / "scripts"
PROVIDERS_DIR = PROJECT_ROOT / "storage" / "providers"

sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(PROVIDERS_DIR))

from provider_registry import create_default_registry


registry = create_default_registry()

print("PROVIDER REGISTRY = OK")
print("Registered Providers =", registry.names())

assert registry.has("mock") is True
assert registry.has("MOCK") is True
assert registry.has("google_drive") is True

with tempfile.TemporaryDirectory(prefix="openelec_registry_test_") as temp_dir:
    provider = registry.create(
        "mock",
        root_path=temp_dir,
    )

    assert provider.provider_name == "mock"
    assert provider.connect() is True
    assert provider.connected is True

    print("Has mock =", registry.has("mock"))
    print("Has google_drive =", registry.has("google_drive"))
    print("Created Provider =", provider.provider_name)
    print("Connected =", provider.connected)

print("REGISTRY TEST = PASS")
