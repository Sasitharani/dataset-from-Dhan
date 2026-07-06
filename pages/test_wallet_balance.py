import requests
import json
import hmac
import hashlib
import time

API_KEY = "YOUR_API_KEY"
SECRET_KEY = "YOUR_SECRET_KEY"

def create_signature(secret_key, json_body):
    secret_bytes = bytes(secret_key, encoding='utf-8')
    signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()
    return signature

def get_wallet_balance():
    """Fetch wallet balance - both spot AND futures"""
    
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
    
    # Try wallet endpoints
    endpoints = [
        ("Wallet Details", "https://api.coindcx.com/exchange/v1/wallets/details"),
        ("Wallet Balance", "https://api.coindcx.com/exchange/v1/wallets/balance"),
        ("Wallet Info", "https://api.coindcx.com/exchange/v1/wallets/info"),
    ]
    
    for name, url in endpoints:
        print(f"\n{'='*60}")
        print(f"Testing: {name}")
        print(f"URL: {url}")
        print(f"{'='*60}")
        
        try:
            response = requests.post(url, data=json_body, headers=headers, timeout=10)
            
            print(f"Status: {response.status_code}")
            print(f"Response:")
            print(response.text)
            
            if response.status_code == 200:
                print(f"\n✅ SUCCESS! {name} works!")
                data = response.json()
                print(f"\nParsed Response:")
                print(json.dumps(data, indent=2))
                return data
        
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n\n⚠️ If all endpoints fail, try these alternatives:")
    print("1. Check if wallet feature is enabled")
    print("2. Contact CoinDCX support")

get_wallet_balance()
