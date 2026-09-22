from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OAUTH_FILE = PROJECT_ROOT / 'storage' / 'config' / 'oauth_client.json'
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
flow = InstalledAppFlow.from_client_secrets_file(str(OAUTH_FILE), SCOPES)
credentials = flow.run_local_server(port=0)
service = build('drive', 'v3', credentials=credentials)
about = service.about().get(fields='user(displayName,emailAddress),storageQuota(limit,usage)').execute()
print('GOOGLE DRIVE CONNECTION = OK')
print('Account =', about.get('user', {}).get('emailAddress'))
print('Display Name =', about.get('user', {}).get('displayName'))
print('Storage Usage =', about.get('storageQuota', {}).get('usage'))
print('Storage Limit =', about.get('storageQuota', {}).get('limit'))
