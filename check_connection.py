import os
import requests
from dhanhq import dhanhq

# 1) Read environment variables
CLIENT_ID = os.getenv("DHAN_CLIENT_ID")
ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")

if not CLIENT_ID or not ACCESS_TOKEN:
    raise SystemExit("❌ Missing DHAN_CLIENT_ID / DHAN_ACCESS_TOKEN")

print("✅ Environment loaded successfully")

# 2) Create Dhan client
dhan = dhanhq(client_id=CLIENT_ID, access_token=ACCESS_TOKEN)
print("✅ Dhan client created")

# 3) Call a simple authenticated endpoint (profile)
url = dhan.base_url + "/profile"
headers = dhan.header

response = requests.get(url, headers=headers, timeout=30)

print("HTTP status:", response.status_code)
print("Response body:")
print(response.text)