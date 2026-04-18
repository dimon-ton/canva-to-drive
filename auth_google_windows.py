#!/usr/bin/env python3
# Run this on Windows to authorize Google Drive
# Then copy google_token.json to the Linux server

import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

flow = InstalledAppFlow.from_client_secrets_file("google_credentials.json", SCOPES)
creds = flow.run_local_server(port=0)

token_data = {
    "token": creds.token,
    "refresh_token": creds.refresh_token,
    "token_uri": creds.token_uri,
    "client_id": creds.client_id,
    "client_secret": creds.client_secret,
    "scopes": list(creds.scopes),
}

with open("google_token.json", "w") as f:
    json.dump(token_data, f, indent=2)

print("✅ Saved google_token.json — copy this file to the Linux server")
