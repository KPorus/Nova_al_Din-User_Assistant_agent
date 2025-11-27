import os
import pathlib
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

KEYFILE_PATH = os.getcwd() + "/gdoc/credentials/oauth.keys.json"
GDRIVE_CREDENTIALS_PATH = os.getcwd() + "/gdoc/credentials/.gdrive-server-credentials.json"
GDOC_CREDENTIALS_PATH = os.getcwd() + "/gdoc/credentials/.gdoc-server-credentials.json"
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]
PORT = 8080
SCOPES = [
    'https://www.googleapis.com/auth/documents',
]

def get_docs_service():
    authenticate_and_save("docs")
    creds = Credentials.from_authorized_user_file(GDOC_CREDENTIALS_PATH, SCOPES)
    return build('docs', 'v1', credentials=creds)

def get_drive_service():
    authenticate_and_save("drive")
    creds = Credentials.from_authorized_user_file(GDRIVE_CREDENTIALS_PATH, DRIVE_SCOPES)
    return build("drive", "v3", credentials=creds)

def authenticate_and_save(app: str = "drive"):
    
    if(app == "drive"):
        if os.path.exists(GDRIVE_CREDENTIALS_PATH):
            return
        creds = None
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                # Save the refreshed credentials
                    with open(GDRIVE_CREDENTIALS_PATH, "w") as f:
                        f.write(creds.to_json())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                creds = None
        flow = InstalledAppFlow.from_client_secrets_file(KEYFILE_PATH, DRIVE_SCOPES)
        creds = flow.run_local_server(port=PORT,    access_type='offline',
    prompt='consent')
        pathlib.Path(os.path.dirname(GDRIVE_CREDENTIALS_PATH)).mkdir(parents=True, exist_ok=True)
        with open(GDRIVE_CREDENTIALS_PATH, "w") as f:
            f.write(creds.to_json())
        print(f"Credentials saved to {GDRIVE_CREDENTIALS_PATH}")
    elif(app == "docs"):
        if os.path.exists(GDOC_CREDENTIALS_PATH):
            return
        creds = None
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                # Save the refreshed credentials
                    with open(GDOC_CREDENTIALS_PATH, "w") as f:
                        f.write(creds.to_json())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                creds = None
        flow = InstalledAppFlow.from_client_secrets_file(KEYFILE_PATH, SCOPES)
        creds = flow.run_local_server(port=PORT,    access_type='offline', prompt='consent')
        pathlib.Path(os.path.dirname(GDOC_CREDENTIALS_PATH)).mkdir(parents=True, exist_ok=True)
        with open(GDOC_CREDENTIALS_PATH, "w") as f:
            f.write(creds.to_json())
        print(f"Credentials saved to {GDOC_CREDENTIALS_PATH}")
