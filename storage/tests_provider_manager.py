from pathlib import Path
import json
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STORAGE_DIR = PROJECT_ROOT / "storage"
PROVIDERS_DIR = STORAGE_DIR / "providers"
SCRIPTS_DIR = STORAGE_DIR / "scripts"

sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(PROVIDERS_DIR))

from storage_profile_registry import StorageProfileRegistry
from provider_registry import create_default_registry
from provider_manager import ProviderManager


with tempfile.TemporaryDirectory(prefix="openelec_manager_test_") as temp_dir:
    temp_dir = Path(temp_dir)

    registry_file = temp_dir / "storage_profile_registry.json"
    mock_root = temp_dir / "manager_mock_storage"

    registry_file.write_text(
        json.dumps(
            {
                "version": 1,
                "project": "OpenElecBIM",
                "storage_profiles": [
                    {
                        "storage_profile_id": "runtime_manager_mock",
                        "contributor_id": "contributor_001",
                        "provider": "mock",
                        "display_name": "Runtime Manager Mock",
                        "account_reference": None,
                        "root_reference": None,
                        "enabled": True,
                        "metadata": {},
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    profile_registry = StorageProfileRegistry(
        registry_path=registry_file
    )

    provider_registry = create_default_registry()

    manager = ProviderManager(
        profile_registry=profile_registry,
        provider_registry=provider_registry,
    )

    profile_id = "runtime_manager_mock"

    provider = manager.get_provider(
        profile_id,
        root_path=mock_root,
    )

    assert provider.provider_name == "mock"
    assert provider.connected is True
    assert manager.has_provider(profile_id) is True

    provider_again = manager.get_provider(
        profile_id,
        root_path=mock_root,
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

    print("Disconnect Cache Removal = OK")

print("PROVIDER MANAGER TEST = PASS")
