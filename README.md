# Canva to Google Drive

Automates exporting a Canva design as MP4 and uploading it to Google Drive — with a public link and QR code generated automatically.

## How It Works

```
Canva Design
    ↓  [Canva Connect API]  Create export job
    ↓  Poll until complete → get download URL
    ↓  Download MP4 to temp file
    ↓  [Google Drive API]  Upload to Drive folder
    ↓  Set public permissions → generate QR code
```

## Project Structure

```
canva_upload_project/
├── get_canva_token_windows.py   # Step 1: OAuth flow to get Canva access token
├── auth_google_windows.py       # Step 2: OAuth flow to get Google Drive token
├── canva_to_drive.py            # Step 3: Main pipeline — export → download → upload
├── requirements.txt
└── .gitignore
```

**Files created at runtime (gitignored):**
- `canva_token.json` — Canva access/refresh token
- `google_token.json` — Google OAuth token
- `google_credentials.json` — Google OAuth client credentials
- `canva_export_qr.png` — QR code pointing to the uploaded file

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Canva credentials

1. Go to [canva.com/developers](https://www.canva.com/developers) → **Your Integrations** → **Create an integration**
2. Note your **Client ID** and **Client Secret**
3. Add `http://localhost:8080/callback` as a redirect URI
4. Enable scopes: `design:content:read`, `design:meta:read`

Edit `get_canva_token_windows.py` and fill in your credentials:

```python
CLIENT_ID = "your_client_id_here"
CLIENT_SECRET = "your_client_secret_here"
```

Then run:

```bash
python get_canva_token_windows.py
```

This opens a browser for Canva login, then saves `canva_token.json`.

### 3. Get Google credentials

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project → enable **Google Drive API**
3. Create **OAuth 2.0 credentials** (Desktop app) → download as `google_credentials.json`
4. Add your Google account as a test user in the OAuth consent screen

Then run:

```bash
python auth_google_windows.py
```

This opens a browser for Google login, then saves `google_token.json`.

### 4. Configure the pipeline

Edit the config block at the top of `canva_to_drive.py`:

```python
DESIGN_ID       = "DAxxxxxxx"          # from your Canva design URL
DRIVE_FOLDER_ID = "your_folder_id"     # from your Google Drive folder URL
DESIGN_NAME     = "canva_export"       # output filename prefix
```

**Finding your Design ID:** open the design in Canva — it's in the URL:
```
https://www.canva.com/design/DAxxxxxxx/edit
                              ↑
                          DESIGN_ID
```

**Finding your Drive Folder ID:**
```
https://drive.google.com/drive/folders/1aBcDeFgHiJkLmNoPqRsTuV
                                        ↑
                                    FOLDER_ID
```

### 5. Run

```bash
python canva_to_drive.py
```

**Output:**
```
[Step 1] Export job created: e08861ae-...
[Step 2] [0s] Status: in_progress
[Step 2] [5s] Status: success
[Step 3] Downloading MP4...
  100.0%
[Step 3] Download complete (45.2 MB)
[Step 3] Uploading canva_export.mp4 to Google Drive...
[Step 3] Upload done!
  File ID   : 1xYz...
  Public link: https://drive.google.com/file/d/1xYz.../view
  QR code   : canva_export_qr.png

Done — 1 file(s) uploaded to Google Drive.
```

## Export Settings

The pipeline exports at **1080p horizontal MP4** with pro quality. To change this, edit the `create_export_job` function in `canva_to_drive.py`:

```python
"format": {
    "type": "mp4",
    "quality": "horizontal_1080p",   # horizontal/vertical + 480p/720p/1080p/4k
    "export_quality": "pro",
}
```

## Notes

- Export URLs from Canva expire after **24 hours** — run the pipeline promptly after starting
- Uploaded files are made **publicly readable** (anyone with the link can view)
- Temp files are automatically deleted after upload
- Google tokens are auto-refreshed when expired
- Canva API rate limits: 750 requests / 5 min, 5,000 / 24 hours
