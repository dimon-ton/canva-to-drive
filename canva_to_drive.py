import json
import os
import time
import tempfile
import requests
import qrcode
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# ── Config ─────────────────────────────────────────────────────────────────
CANVA_TOKEN_FILE     = "canva_token.json"
DESIGN_ID            = "DAHGCBVvC5Q"
GOOGLE_TOKEN_FILE    = "google_token.json"
DRIVE_FOLDER_ID      = "1kMwk56nhT9IyrVtW5V-Rw6HArBm4TNbr"
DESIGN_NAME          = "canva_export"
# ───────────────────────────────────────────────────────────────────────────

with open(CANVA_TOKEN_FILE) as f:
    _token_data = json.load(f)
CANVA_ACCESS_TOKEN = _token_data["access_token"]

CANVA_HEADERS = {
    "Authorization": f"Bearer {CANVA_ACCESS_TOKEN}",
    "Content-Type": "application/json",
}
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.file"]


# ── Google Drive auth (load token from google_token.json) ──────────────────
def get_drive_service():
    if not os.path.exists(GOOGLE_TOKEN_FILE):
        raise FileNotFoundError(
            "google_token.json not found. Run auth_google_windows.py on Windows first."
        )
    with open(GOOGLE_TOKEN_FILE) as f:
        data = json.load(f)
    creds = Credentials(
        token=data["token"],
        refresh_token=data["refresh_token"],
        token_uri=data["token_uri"],
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        scopes=data["scopes"],
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        data["token"] = creds.token
        with open(GOOGLE_TOKEN_FILE, "w") as f:
            json.dump(data, f, indent=2)
    return build("drive", "v3", credentials=creds)


# ── Step 1: Create export job ───────────────────────────────────────────────
def create_export_job(design_id: str) -> str:
    body = {
        "design_id": design_id,
        "format": {
            "type": "mp4",
            "quality": "horizontal_1080p",
            "export_quality": "pro",
        },
    }
    resp = requests.post(
        "https://api.canva.com/rest/v1/exports",
        headers=CANVA_HEADERS,
        json=body,
    )
    if not resp.ok:
        print(f"[Step 1] ERROR {resp.status_code}: {resp.text}")
        resp.raise_for_status()
    data = resp.json()
    job_id = data["job"]["id"]
    print(f"[Step 1] Export job created: {job_id}")
    return job_id


# ── Step 2: Poll until done ─────────────────────────────────────────────────
def poll_export_job(job_id: str, interval: int = 5, max_wait: int = 900) -> list:
    elapsed = 0
    while elapsed < max_wait:
        resp = requests.get(
            f"https://api.canva.com/rest/v1/exports/{job_id}",
            headers=CANVA_HEADERS,
        )
        resp.raise_for_status()
        job = resp.json()["job"]
        status = job["status"]
        print(f"[Step 2] [{elapsed}s] Status: {status}")

        if status == "success":
            urls = job["urls"]
            print(f"[Step 2] Export ready — {len(urls)} file(s)")
            return urls
        elif status == "failed":
            err = job.get("error", {})
            raise RuntimeError(f"Export failed: {err.get('code')} — {err.get('message')}")

        time.sleep(interval)
        elapsed += interval

    raise TimeoutError(f"Export job did not finish within {max_wait}s")


# ── Step 3a: Download MP4 ───────────────────────────────────────────────────
def download_mp4(url: str, save_path: str) -> str:
    print("[Step 3] Downloading MP4...")
    resp = requests.get(url, stream=True)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    downloaded = 0
    with open(save_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    print(f"  {downloaded / total * 100:.1f}%", end="\r")
    print(f"\n[Step 3] Download complete ({downloaded / 1_000_000:.1f} MB)")
    return save_path


# ── Step 3b: Upload to Google Drive ────────────────────────────────────────
def upload_to_drive(service, file_path: str, file_name: str) -> dict:
    metadata = {"name": file_name, "parents": [DRIVE_FOLDER_ID]}
    media = MediaFileUpload(file_path, mimetype="video/mp4", resumable=True)

    print(f"[Step 3] Uploading {file_name} to Google Drive...")
    file = service.files().create(
        body=metadata,
        media_body=media,
        fields="id, name, webViewLink",
    ).execute()

    # Make file publicly accessible
    service.permissions().create(
        fileId=file["id"],
        body={"role": "reader", "type": "anyone"},
    ).execute()
    public_link = f"https://drive.google.com/file/d/{file['id']}/view"

    # Generate QR code
    qr_path = file_name.replace(".mp4", "_qr.png")
    qrcode.make(public_link).save(qr_path)

    print(f"[Step 3] Upload done!")
    print(f"  File ID   : {file['id']}")
    print(f"  Public link: {public_link}")
    print(f"  QR code   : {qr_path}")
    file["public_link"] = public_link
    file["qr_path"] = qr_path
    return file


# ── Main pipeline ───────────────────────────────────────────────────────────
def run_pipeline():
    drive_service = get_drive_service()

    job_id = create_export_job(DESIGN_ID)
    urls = poll_export_job(job_id)

    results = []
    for i, url in enumerate(urls):
        name = f"{DESIGN_NAME}.mp4" if len(urls) == 1 else f"{DESIGN_NAME}_{i + 1}.mp4"
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            download_mp4(url, tmp_path)
            info = upload_to_drive(drive_service, tmp_path, name)
            results.append(info)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    print(f"\nDone — {len(results)} file(s) uploaded to Google Drive.")
    return results


if __name__ == "__main__":
    run_pipeline()
