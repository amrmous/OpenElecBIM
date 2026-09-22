from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OAUTH_FILE = PROJECT_ROOT / "storage" / "config" / "oauth_client.json"

SCOPES = [
    "https://www.googleapis.com/auth/drive.metadata.readonly"
]


class GoogleDriveAdapter:
    def __init__(self, oauth_file=OAUTH_FILE):
        self.oauth_file = Path(oauth_file)

        if not self.oauth_file.exists():
            raise FileNotFoundError(
                f"OAuth client file not found: {self.oauth_file}"
            )

        self.service = None
        self.account = None
        self.usage = None
        self.limit = None

    def connect(self):
        flow = InstalledAppFlow.from_client_secrets_file(
            str(self.oauth_file),
            SCOPES
        )

        credentials = flow.run_local_server(port=0)

        self.service = build(
            "drive",
            "v3",
            credentials=credentials
        )

        about = self.service.about().get(
            fields="user(displayName,emailAddress),storageQuota(limit,usage)"
        ).execute()

        self.account = about.get("user", {})
        quota = about.get("storageQuota", {})

        self.usage = int(quota.get("usage", 0) or 0)
        self.limit = int(quota.get("limit", 0) or 0)

        return about

    def get_usage_bytes(self):
        return self.usage

    def get_limit_bytes(self):
        return self.limit

    def get_available_bytes(self):
        if self.limit <= 0:
            return None

        return max(self.limit - self.usage, 0)

    def get_usage_percent(self):
        if self.limit <= 0:
            return None

        return (self.usage / self.limit) * 100

    def get_status(self):
        if self.limit <= 0:
            return "UNKNOWN"

        percent = self.get_usage_percent()

        if percent >= 95:
            return "FULL"

        if percent >= 85:
            return "NEAR_FULL"

        return "AVAILABLE"


if __name__ == "__main__":
    adapter = GoogleDriveAdapter()
    about = adapter.connect()

    print("GOOGLE DRIVE ADAPTER = OK")
    print("Account =", adapter.account.get("emailAddress"))
    print("Usage Bytes =", adapter.get_usage_bytes())
    print("Limit Bytes =", adapter.get_limit_bytes())
    print("Available Bytes =", adapter.get_available_bytes())
    print("Usage Percent =", round(adapter.get_usage_percent(), 2))
    print("Status =", adapter.get_status())