from pathlib import Path
import json
import re

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OAUTH_FILE = PROJECT_ROOT / "storage" / "config" / "oauth_client.json"
TOKEN_DIR = PROJECT_ROOT / "storage" / "state" / "google_drive_tokens"

SCOPES = [
    "https://www.googleapis.com/auth/drive"
]


class GoogleDriveAdapter:
    def __init__(self, oauth_file=OAUTH_FILE, account_reference=None):
        self.oauth_file = Path(oauth_file)

        if not self.oauth_file.exists():
            raise FileNotFoundError(
                f"OAuth client file not found: {self.oauth_file}"
            )

        self.account_reference = account_reference
        self.service = None
        self.account = None
        self.usage = None
        self.limit = None
        self.credentials = None

    def _token_file(self):
        TOKEN_DIR.mkdir(parents=True, exist_ok=True)

        if self.account_reference:
            safe_name = re.sub(
                r"[^A-Za-z0-9._-]+",
                "_",
                self.account_reference.strip()
            )
        else:
            safe_name = "default"

        return TOKEN_DIR / f"{safe_name}.json"

    def connect(self):
        token_file = self._token_file()
        credentials = None

        if token_file.exists():
            try:
                credentials = Credentials.from_authorized_user_file(
                    str(token_file),
                    SCOPES
                )
            except Exception:
                credentials = None

        if credentials and not credentials.valid:
            if credentials.expired and credentials.refresh_token:
                from google.auth.transport.requests import Request
                credentials.refresh(Request())
            else:
                credentials = None

        if credentials is None:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.oauth_file),
                SCOPES
            )

            credentials = flow.run_local_server(port=0)

            token_file.write_text(
                credentials.to_json(),
                encoding="utf-8"
            )

        self.credentials = credentials

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

        actual_email = self.account.get("emailAddress")

        if (
            self.account_reference
            and actual_email
            and actual_email.lower() != self.account_reference.lower()
        ):
            raise RuntimeError(
                "Connected Google account does not match the requested "
                f"account_reference: {self.account_reference}"
            )

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
    adapter = GoogleDriveAdapter(
        account_reference="01097033409f@gmail.com"
    )

    about = adapter.connect()

    print("GOOGLE DRIVE ADAPTER = OK")
    print("Account =", adapter.account.get("emailAddress"))
    print("Usage Bytes =", adapter.get_usage_bytes())
    print("Limit Bytes =", adapter.get_limit_bytes())
    print("Available Bytes =", adapter.get_available_bytes())
    print("Usage Percent =", round(adapter.get_usage_percent(), 2))
    print("Status =", adapter.get_status())
    print("TOKEN FILE =", adapter._token_file())
