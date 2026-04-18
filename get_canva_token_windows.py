#!/usr/bin/env python3
# get_canva_token_windows.py - ขอ Access Token จาก Canva (สำหรับ Windows)
# วิธีรัน: python get_canva_token_windows.py

import base64, hashlib, secrets, urllib.parse, json
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

# ══════════════════════════════════════════════════════
# ← ใส่ค่าจาก Canva Developer Portal ตรงนี้
CLIENT_ID = "your_client_id_here"
CLIENT_SECRET = "your_client_secret_here"

# ใช้ localhost สำหรับ Windows
REDIRECT_URI = "http://localhost:8080/callback"
# ══════════════════════════════════════════════════════

# สร้าง PKCE
code_verifier = secrets.token_urlsafe(64)
code_challenge = base64.urlsafe_b64encode(
 hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b"=").decode()

# สร้าง URL สำหรับ authorize
auth_url = (
 "https://www.canva.com/api/oauth/authorize"
 f"?client_id={CLIENT_ID}"
 f"&response_type=code"
 f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
 f"&scope=asset:write%20asset:read"
 f"&code_challenge={code_challenge}"
 f"&code_challenge_method=S256"
)

print("\n" + "="*60)
print("STEP 1: Open this URL in your browser:")
print("="*60)
print(auth_url)
print("="*60 + "\n")
print("STEP 2: Login Canva if not logged in")
print("STEP 3: Click 'Allow' or 'Authorize'")
print("STEP 4: Come back to this terminal\n")
print("Waiting for callback on port 8080...")

# รอรับ callback
auth_code = None

class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  global auth_code
  params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
  auth_code = params.get("code", [None])[0]
  self.send_response(200)
  self.end_headers()
  self.wfile.write(b"<h1>Authorization OK!</h1><p>Check your terminal</p>")
 
 def log_message(self, *args):
  pass

server = HTTPServer(("localhost", 8080), Handler)
print(f"\nServer running at {REDIRECT_URI}")
print("Press Ctrl+C to stop the server\n")

# Handle one request
server.handle_request()

# ตรวจสอบว่าได้ code หรือไม่
if not auth_code:
 print("\nERROR: No authorization code received! Try again.")
 exit(1)

# แลก code เป็น token
print("\nExchanging code for Access Token...")
creds = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
res = requests.post(
 "https://api.canva.com/rest/v1/oauth/token",
 headers={
 "Authorization": f"Basic {creds}",
 "Content-Type": "application/x-www-form-urlencoded"
 },
 data={
 "grant_type": "authorization_code",
 "code": auth_code,
 "code_verifier": code_verifier,
 "redirect_uri": REDIRECT_URI
 }
)

if res.status_code != 200:
 print(f"\nERROR: Failed to get token: {res.status_code}")
 print(res.text)
 exit(1)

token_data = res.json()

with open("canva_token.json", "w") as f:
 json.dump(token_data, f, indent=2)

print("\n" + "="*60)
print("SUCCESS! Token saved to canva_token.json")
print("="*60)
print(f"Access Token: {token_data.get('access_token', 'ERROR')[:40]}...")
print(f"Expires in: {token_data.get('expires_in', 0) // 3600} hours")
print(f"File: canva_token.json")
print("="*60 + "\n")
