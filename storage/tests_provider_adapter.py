from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROVIDERS_DIR = PROJECT_ROOT / "storage" / "providers"

sys.path.insert(0, str(PROVIDERS_DIR))

from mock_provider import MockStorageProvider


TEST_ROOT = PROJECT_ROOT / "storage" / "tests" / "mock_storage"
SOURCE_FILE = PROJECT_ROOT / "storage" / "tests" / "provider_test_source.txt"
DOWNLOAD_FILE = PROJECT_ROOT / "storage" / "tests" / "provider_test_download.txt"

SOURCE_FILE.parent.mkdir(parents=True, exist_ok=True)

SOURCE_FILE.write_text(
    "OpenElecBIM Provider Adapter Test\n",
    encoding="utf-8",
)

provider = MockStorageProvider(TEST_ROOT)

assert provider.connect() is True

uploaded = provider.upload(
    str(SOURCE_FILE),
    "objects/provider_test_source.txt",
    metadata={
        "test": True,
        "project": "OpenElecBIM",
    },
)

assert provider.exists("objects/provider_test_source.txt") is True

metadata = provider.get_metadata(
    "objects/provider_test_source.txt"
)

downloaded = provider.download(
    "objects/provider_test_source.txt",
    str(DOWNLOAD_FILE),
)

items = provider.list("objects")

assert provider.delete("objects/provider_test_source.txt") is True
assert provider.exists("objects/provider_test_source.txt") is False

print("PROVIDER ADAPTER = OK")
print("Provider =", provider.provider_name)
print("Connected =", provider.connected)
print("Uploaded Reference =", uploaded["reference"])
print("Uploaded Hash =", uploaded["content_hash"])
print("Metadata Hash =", metadata["content_hash"])
print("Downloaded Hash =", downloaded["content_hash"])
print("Listed Objects =", len(items))
print("Deleted = True")
print("Exists After Delete =", provider.exists("objects/provider_test_source.txt"))
