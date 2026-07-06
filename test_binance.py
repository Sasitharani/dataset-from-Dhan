import hmac
import hashlib
import time
import requests

API_KEY = "YOUR_API_KEY_HERE"
SECRET_KEY = "YOUR_SECRET_KEY_HERE"
BASE_URL = "https://fapi.binance.com"

def get_signature(secret_key, query_string):
    return hmac.new(
        bytes(secret_key, 'utf-8'),
        bytes(query_string, 'utf-8'),
        hashlib.sha256
    ).hexdigest()

# Test 1: Get Account Info
timestamp = int(time.time() * 1000)
query_string = f"timestamp={timestamp}"
signature = get_signature(SECRET_KEY, query_string)

headers = {"X-MBX-APIKEY": API_KEY}
url = f"{BASE_URL}/fapi/v2/account?{query_string}&signature={signature}"

print(f"Testing: {url}")
print(f"Headers: {headers}")

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"\n✅ Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS! API Key works!")
        data = response.json()
        print(f"Account info: {data.keys()}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ Exception: {str(e)}")
