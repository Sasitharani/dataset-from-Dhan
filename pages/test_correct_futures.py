import requests
import json
import hmac
import hashlib
import time

API_KEY = "YOUR_NEW_API_KEY"
SECRET_KEY = "YOUR_NEW_SECRET_KEY"

def create_signature(secret_key, json_body):
    secret_bytes = bytes(secret_key, encoding='utf-8')
    signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()
    return signature

def test_futures_endpoints():
    """Test CORRECT futures endpoints from official docs"""
    
    timestamp = int(round(time.time() * 1000))
    body = {"timestamp": timestamp}
    json_body = json.dumps(body, separators=(',', ':'))
    
    secret_bytes = bytes(SECRET_KEY, encoding='utf-8')
    signature = create_signature(SECRET_KEY, json_body)
    
    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': API_KEY,
        'X-AUTH-SIGNATURE': signature
    }
    
    # CORRECT futures endpoints from docs
    endpoints = [
        ("List Positions", "https://api.coindcx.com/exchange/v1/futures/positions"),
        ("Get Instruments", "https://api.coindcx.com/exchange/v1/futures/instruments"),
        ("Get Active Instruments", "https://api.coindcx.com/exchange/v1/futures/active_instruments"),
        ("List Orders", "https://api.coindcx.com/exchange/v1/futures/orders"),
    ]
    
    for name, url in endpoints:
        print(f"\n{'='*70}")
        print(f"Testing: {name}")
        print(f"URL: {url}")
        print(f"{'='*70}")
        
        try:
            response = requests.post(url, data=json_body, headers=headers, timeout=10)
            
            print(f"✓ Status: {response.status_code}")
            print(f"✓ Response:")
            print(response.text)
            
            if response.status_code == 200:
                print(f"\n✅ SUCCESS! {name} endpoint works!")
                data = response.json()
                print(f"\nParsed JSON:")
                print(json.dumps(data, indent=2))
        
        except Exception as e:
            print(f"✗ Error: {e}")

test_futures_endpoints()
