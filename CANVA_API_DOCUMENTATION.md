# Canva API — Export Video to Google Drive
> บทสนทนาเกี่ยวกับการใช้ Canva Connect API เพื่อ export วิดีโอและอัปโหลดไปยัง Google Drive

---

## 1. Canva Developer (canva.dev) ทำอะไรได้บ้าง?

### สองแพลตฟอร์มหลัก
- **Apps SDK** — สร้าง app ที่ทำงานภายใน Canva Editor
- **Connect APIs** — นำ Canva ไปฝังในแพลตฟอร์มอื่นผ่าน REST API

### Use Cases ที่ทำได้
| ความสามารถ | รายละเอียด |
|---|---|
| Add Design Tools | สร้าง plugin เพิ่ม tools ใน editor เช่น AI effects, visual filters |
| Embed Canva | ฝัง Canva editor เข้าไปในเว็บหรือแอปของตัวเอง |
| Connect to Data Sources | ดึงข้อมูลจากแหล่งภายนอกมาใช้สร้างดีไซน์อัตโนมัติ |
| Autofill Designs | ป้อนข้อมูลจริงลง Brand Template อัตโนมัติ |
| Publish Instantly | ส่งดีไซน์ไปยัง platform อื่นโดยตรง |
| Manage Brand Templates | จัดการ template ขององค์กรผ่าน API |
| Bulk Create | สร้างดีไซน์จำนวนมากพร้อมกันจากข้อมูล |
| Design Interaction | อ่าน/แก้ไข layout, content, pages, metadata ของดีไซน์ |
| Resize Designs | ปรับขนาดดีไซน์เป็น format/aspect ratio ต่าง ๆ อัตโนมัติ |
| Reply to Comments | รับและตอบ comment ใน Canva จากแพลตฟอร์มอื่น |
| Expand URLs | วาง link จากแพลตฟอร์มอื่นให้ Canva AI ดึงข้อมูลมาออกแบบได้ |

### เครื่องมือและ API อื่น ๆ
- **SCIM API** — sync ผู้ใช้/บัญชีในองค์กรอัตโนมัติ
- **Audit Logs** — ตรวจสอบการเปลี่ยนแปลงของทีม
- **Flourish Charts** — แปลงข้อมูลเป็น interactive chart/infographic
- **Canva Dev MCP Server** — เชื่อม AI assistant เข้ากับ Canva docs โดยตรง

---

## 2. Export วิดีโอ MP4 และเก็บใน Google Drive ทำได้ไหม?

**ได้เลย!** โดยใช้ Flow ดังนี้:

```
Canva Design (วิดีโอที่ตัดต่อแล้ว)
 ↓ [Canva Connect API — Export Job]
 ดาวน์โหลด MP4 (ผ่าน URL ชั่วคราว 24 ชม.)
 ↓ [Google Drive API]
 อัปโหลดเก็บใน Google Drive
```

---

## 3. Step 1 — Create Design Export Job

### Endpoint
```
POST https://api.canva.com/rest/v1/exports
```

### Headers
| Header | ค่า |
|---|---|
| `Authorization` | `Bearer {access_token}` |
| `Content-Type` | `application/json` |

### Body (สำหรับ MP4)
```json
{
 "design_id": "DAxxxxxxx",
 "format": {
 "type": "mp4",
 "quality": "horizontal_1080p",
 "export_quality": "pro",
 "pages": [1, 2, 3]
 }
}
```

### ค่า quality ที่ใช้ได้
- `horizontal_480p` / `vertical_480p`
- `horizontal_720p` / `vertical_720p`
- `horizontal_1080p` / `vertical_1080p`
- `horizontal_4k` / `vertical_4k`

### Response
```json
{
 "job": {
 "id": "e08861ae-3b29-45db-8dc1-1fe0bf7f1cc8",
 "status": "in_progress"
 }
}
```

> **job_id** คือ `id` ในค่า response นี้ เอาไปใช้ใน Step 2 ได้เลย

### หา Design ID
เปิด Canva แล้วดูที่ URL:
```
https://www.canva.com/design/DAVZr1z5464/edit
 ↑
 design_id = DAVZr1z5464
```

### Python Code
```python
import requests

ACCESS_TOKEN = "your_access_token_here"
DESIGN_ID = "DAxxxxxxx"

headers = {
 "Authorization": f"Bearer {ACCESS_TOKEN}",
 "Content-Type": "application/json"
}

body = {
 "design_id": DESIGN_ID,
 "format": {
 "type": "mp4",
 "quality": "horizontal_1080p",
 "export_quality": "pro"
 }
}

response = requests.post(
 "https://api.canva.com/rest/v1/exports",
 headers=headers,
 json=body
)

data = response.json()
job_id = data["job"]["id"]
status = data["job"]["status"]

print(f"Job ID: {job_id}")
print(f"Status: {status}")
```

### Rate Limits
- Integration: 750 ครั้ง/5 นาที, 5,000 ครั้ง/24 ชั่วโมง
- Document: 75 ครั้ง/5 นาที
- User: 75 ครั้ง/5 นาที, 500 ครั้ง/24 ชั่วโมง

---

## 4. Token มาจากไหน?

Token มาจาก **OAuth 2.0** ของ Canva โดยผ่านกระบวนการดังนี้:

```
[Developer Portal]
 สร้าง Integration → ได้ Client ID + Client Secret
 ↓
[OAuth Flow]
 ผู้ใช้ล็อกอิน Canva + อนุญาต → ได้ Authorization Code
 ↓
[Exchange Code → Token]
 ส่ง Code + Client Secret → ได้ Access Token
 ↓
[ใช้งาน API]
 Bearer {access_token}
```

### Step A — สร้าง Integration
1. ไปที่ [canva.com/developers](https://www.canva.com/developers) → Your Integrations → Create an integration
2. บันทึก **Client ID** และ **Client Secret**

### Scopes ที่ต้องเปิด
- `design:content:read`
- `design:meta:read`

### Step B — Authorization URL
```
https://www.canva.com/api/oauth/authorize
 ?code_challenge=<hash>
 &code_challenge_method=S256
 &scope=design:content:read design:meta:read
 &response_type=code
 &client_id=<YOUR_CLIENT_ID>
 &redirect_uri=http://127.0.0.1:3001/oauth/redirect
```

### Step C — แลก Code เอา Token
```python
import requests, base64

credentials = base64.b64encode(
 f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
).decode()

response = requests.post(
 "https://api.canva.com/rest/v1/oauth/token",
 headers={
 "Authorization": f"Basic {credentials}",
 "Content-Type": "application/x-www-form-urlencoded"
 },
 data={
 "grant_type": "authorization_code",
 "code": "<code_จาก_redirect>",
 "code_verifier": "<code_verifier_ที่เก็บไว้>",
 "redirect_uri": "http://127.0.0.1:3001/oauth/redirect"
 }
)

token_data = response.json()
access_token = token_data["access_token"]
refresh_token = token_data["refresh_token"]
```

### สิ่งที่ต้องมี
| สิ่งที่ต้องการ | ได้มาจาก |
|---|---|
| Client ID | Developer Portal |
| Client Secret | Developer Portal (เห็นครั้งเดียวตอน generate) |
| Access Token | OAuth flow (แลกจาก authorization code) |
| Refresh Token | ได้มาพร้อม access token |

---

## 5. Step 2 — Poll Export Job Status

### Endpoint
```
GET https://api.canva.com/rest/v1/exports/{exportId}
```

- `exportId` คือ `job_id` ที่ได้จาก Step 1
- Rate limit: 120 requests/นาที

### Response

**กำลังประมวลผล:**
```json
{
 "job": {
 "id": "e08861ae-3b29-45db-8dc1-1fe0bf7f1cc8",
 "status": "in_progress"
 }
}
```

**สำเร็จ:**
```json
{
 "job": {
 "id": "e08861ae-3b29-45db-8dc1-1fe0bf7f1cc8",
 "status": "success",
 "urls": [
 "https://export-download.canva.com/..."
 ]
 }
}
```

**ล้มเหลว:**
```json
{
 "job": {
 "id": "e08861ae-...",
 "status": "failed",
 "error": {
 "code": "license_required",
 "message": "User doesn't have the required license..."
 }
 }
}
```

### Python Code
```python
import requests
import time

def poll_export_job(job_id, interval=3, max_wait=300):
 elapsed = 0
 while elapsed < max_wait:
 response = requests.get(
 f"https://api.canva.com/rest/v1/exports/{job_id}",
 headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
 )
 data = response.json()
 job = data["job"]
 status = job["status"]

 print(f"[{elapsed}s] Status: {status}")

 if status == "success":
 urls = job["urls"]
 print(f"✅ Export สำเร็จ! ได้ {len(urls)} ไฟล์")
 return urls
 elif status == "failed":
 error = job.get("error", {})
 print(f"❌ Export ล้มเหลว: {error.get('code')} - {error.get('message')}")
 return None

 time.sleep(interval)
 elapsed += interval

 print("⏰ Timeout: รอนานเกินไป")
 return None
```

---

## 6. Step 3 — ดาวน์โหลด MP4 → อัปโหลด Google Drive

### สิ่งที่ต้องมีก่อน
1. ไปที่ [console.cloud.google.com](https://console.cloud.google.com)
2. สร้าง Project → เปิด **Google Drive API**
3. สร้าง **Service Account** → ดาวน์โหลด JSON key
4. Share Drive folder ให้ email ของ Service Account

### ติดตั้ง Library
```bash
pip install requests google-api-python-client google-auth
```

### Python Code
```python
import requests
import os
import tempfile
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

SERVICE_ACCOUNT_FILE = "service_account.json"
DRIVE_FOLDER_ID = "1aBcDeFgHiJkLmNoPqRsTuV"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def upload_to_drive(file_path, file_name, folder_id):
 creds = service_account.Credentials.from_service_account_file(
 SERVICE_ACCOUNT_FILE, scopes=SCOPES
 )
 service = build("drive", "v3", credentials=creds)

 file_metadata = {"name": file_name, "parents": [folder_id]}
 media = MediaFileUpload(file_path, mimetype="video/mp4", resumable=True)

 print(f"📤 กำลังอัปโหลด {file_name} ไปยัง Google Drive...")
 file = service.files().create(
 body=file_metadata,
 media_body=media,
 fields="id, name, webViewLink"
 ).execute()

 print(f"✅ อัปโหลดสำเร็จ!")
 print(f" File ID : {file['id']}")
 print(f" View Link: {file['webViewLink']}")
 return file

def download_mp4(url, save_path):
 print(f"⬇️ กำลังดาวน์โหลด MP4...")
 response = requests.get(url, stream=True)
 response.raise_for_status()
 total = int(response.headers.get("content-length", 0))
 downloaded = 0
 with open(save_path, "wb") as f:
 for chunk in response.iter_content(chunk_size=1024 * 1024):
 if chunk:
 f.write(chunk)
 downloaded += len(chunk)
 if total:
 pct = downloaded / total * 100
 print(f" {pct:.1f}%", end="\r")
 print(f"\n✅ ดาวน์โหลดเสร็จ")
 return save_path

def process_export(download_urls, design_name="canva_video"):
 results = []
 for i, url in enumerate(download_urls):
 file_name = f"{design_name}_{i+1}.mp4" if len(download_urls) > 1 else f"{design_name}.mp4"
 with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
 tmp_path = tmp.name
 try:
 download_mp4(url, tmp_path)
 file_info = upload_to_drive(tmp_path, file_name, DRIVE_FOLDER_ID)
 results.append(file_info)
 finally:
 if os.path.exists(tmp_path):
 os.remove(tmp_path)
 return results
```

### หา Folder ID
```
https://drive.google.com/drive/folders/1aBcDeFgHiJkLmNoPqRsTuV
 ↑
 FOLDER_ID อยู่ตรงนี้
```

### ข้อควรระวัง
| เรื่อง | รายละเอียด |
|---|---|
| URL หมดอายุ | 24 ชั่วโมง — ต้องดาวน์โหลดทันที |
| ไฟล์ใหญ่ | ใช้ `stream=True` + `resumable=True` |
| Service Account | ต้อง share Drive folder ให้ email ของ service account ก่อน |
| Temp file | ใช้ `tempfile` แล้วลบทิ้งหลังอัปโหลดเสมอ |

---

## 7. Pipeline รวม 3 Steps

```python
# ==============================
# MAIN PIPELINE: Canva → Drive
# ==============================

ACCESS_TOKEN = "canva_access_token"
DESIGN_ID = "DAxxxxxxx"

# Step 1: สร้าง export job
job_id = create_export_job(ACCESS_TOKEN, DESIGN_ID)

# Step 2: Poll จนได้ URL
urls = poll_export_job(job_id)

# Step 3: ดาวน์โหลด + อัปโหลด Drive
if urls:
 process_export(urls, design_name="my_school_video")
```

### ภาพรวม Flow ทั้งหมด
```
design_id → Step 1 สร้าง export job
 ↓
 job_id → Step 2 poll ดู status
 ↓
 download_url → Step 3 โหลด + อัปโหลด Drive
```

---

## 8. หมายเหตุ — Error: Access blocked (n8n)

Error `400: invalid_request` จาก Google OAuth ใน n8n มีสาเหตุหลัก:

1. **Redirect URI ไม่ตรงกัน** — เพิ่ม URI ใน Google Cloud Console:
 ```
 http://localhost:5678/rest/oauth2-credential/callback
 ```
2. **OAuth Consent Screen ยังไม่ได้ตั้งค่า** — กรอก App name / Support email
3. **ยังอยู่ใน Testing mode** — เพิ่ม email เป็น Test user ใน OAuth consent screen

---

*Export จาก Claude.ai — วันที่ 18 เมษายน 2569*
