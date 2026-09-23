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
from provider_resolver import ProviderResolver


with tempfile.TemporaryDirectory(prefix="openelec_resolver_test_") as temp_dir:
    temp_dir = Path(temp_dir)
    registry_file = temp_dir / "storage_profile_registry.json"

    registry_file.write_text(
        json.dumps(
            {
                "version": 1,
                "project": "OpenElecBIM",
                "storage_profiles": [
                    {
                        "storage_profile_id": "runtime_mock_profile",
                        "contributor_id": "contributor_001",
                        "provider": "mock",
                        "display_name": "Runtime Mock Profile",
                        "account_reference": None,
                        "root_reference": None,
                        "enabled": True,
                        "metadata": {},
                    },
                    {
                        "storage_profile_id": "runtime_google_profile",
                        "contributor_id": "contributor_001",
                        "provider": "google_drive",
                        "display_name": "Runtime Google Profile",
                        "account_reference": "test@example.com",
                        "root_reference": "google-root-test",
                        "enabled": True,
                        "metadata": {},
                    },
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

    resolver = ProviderResolver(
        profile_registry=profile_registry,
        provider_registry=provider_registry,
    )

    # --------------------------------------------------------
    # Mock profile -> Mock Provider
    # --------------------------------------------------------
    mock_provider = resolver.resolve(
        "runtime_mock_profile",
        root_path=temp_dir / "mock_storage",
    )

    assert mock_provider.provider_name == "mock"
    assert mock_provider.connect() is True
    assert mock_provider.connected is True

    print("MOCK PROFILE FOUND = OK")
    print("Resolved Mock Provider =", mock_provider.provider_name)
    print("Mock Connected =", mock_provider.connected)

    # --------------------------------------------------------
    # Google profile -> Google Drive Provider
    # Resolve only; do NOT connect / OAuth here.
    # --------------------------------------------------------
    google_provider = resolver.resolve(
        "runtime_google_profile"
    )

    assert google_provider.provider_name == "google_drive"

    print("GOOGLE PROFILE RESOLUTION = OK")
    print("Resolved Google Provider =", google_provider.provider_name)

print("PROVIDER RESOLVER TEST = PASS")
