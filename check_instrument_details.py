import os
from dotenv import load_dotenv
from coindcx import Client
import json

load_dotenv()

API_KEY = os.getenv('COINDCX_API_KEY')
API_SECRET = os.getenv('COINDCX_API_SECRET')

client = Client(api_key=API_KEY, api_secret=API_SECRET)

print("=" * 80)
print("🔍 CHECK INSTRUMENT DETAILS")
print("=" * 80)

# Get active instruments
print("\n✅ Fetching futures instruments...")
try:
    instruments = client.futures.get_active_instruments()
    print(f"Found {len(instruments)} instruments")
    
    # Find BTC_USDT
    for inst in instruments:
        if 'BTC' in inst.get('symbol', '').upper() and 'USDT' in inst.get('symbol', '').upper():
            print(f"\n✓ Found: {inst.get('symbol', 'N/A')}")
            print(f"  Full details:")
            print(json.dumps(inst, indent=2))
            break
except Exception as e:
    print(f"Error: {e}")

