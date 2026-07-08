"""
Standard API Clients for CoinDCX + Dhan
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from coindcx import Client
import requests

env_path = Path('/workspaces/dataset-from-Dhan/.env')
load_dotenv(env_path, override=True)

# ==================== COINDCX ====================
COINDCX_API_KEY = os.getenv('COINDCX_API_KEY')
COINDCX_API_SECRET = os.getenv('COINDCX_API_SECRET')

class CoinDCXClient:
    """CoinDCX API Client"""
    
    def __init__(self):
        self.client = Client(api_key=COINDCX_API_KEY, api_secret=COINDCX_API_SECRET)
    
    def get_candles(self, pair, interval, limit=1000):
        try:
            candles = self.client.get_candles(pair=pair, interval=interval, limit=limit)
            return list(reversed(candles)) if candles else None
        except Exception as e:
            print(f"Error: {e}")
            return None

# ==================== DHAN ====================
DHAN_CLIENT_ID = os.getenv('DHAN_CLIENT_ID')
DHAN_ACCESS_TOKEN = os.getenv('DHAN_ACCESS_TOKEN')

class DhanClient:
    """Dhan API Client - REST API"""
    
    def __init__(self):
        print("\n[DhanClient] Initializing...")
        self.connected = False
        self.base_url = "https://api.dhan.co/v2/charts/intraday"
        self.headers = {
            "Content-Type": "application/json",
            "access-token": DHAN_ACCESS_TOKEN
        }
        
        if DHAN_ACCESS_TOKEN:
            self.connected = True
            print("[DhanClient] ✅ CONNECTED!")
        else:
            print("[DhanClient] ❌ No access token")
    
    def get_candles(self, security_id, interval, from_date, to_date):
        """Get NIFTY candles from Dhan REST API
        
        Returns list of candles:
        [{'timestamp': ts, 'open': o, 'high': h, 'low': l, 'close': c, 'volume': v}, ...]
        """
        try:
            if not self.connected:
                print("[get_candles] ❌ Not connected")
                return None
            
            print(f"[get_candles] Fetching {security_id} {interval}min {from_date} to {to_date}")
            
            # NIFTY 50 payload
            payload = {
                "securityId": str(security_id),
                "exchangeSegment": "IDX_I",  # ← KEY: IDX_I for indices
                "instrument": "INDEX",
                "interval": str(interval),
                "oi": False,
                "fromDate": from_date,
                "toDate": to_date
            }
            
            # Make REST request
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            print(f"[get_candles] HTTP Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Response is directly the OHLCV arrays
                # {"open": [...], "high": [...], "low": [...], "close": [...], "volume": [...], "timestamp": [...]}
                
                if 'timestamp' in data and 'open' in data:
                    # Convert to list of candles
                    candles = []
                    timestamps = data.get('timestamp', [])
                    opens = data.get('open', [])
                    highs = data.get('high', [])
                    lows = data.get('low', [])
                    closes = data.get('close', [])
                    volumes = data.get('volume', [])
                    
                    for i in range(len(timestamps)):
                        candles.append({
                            'timestamp': timestamps[i],
                            'open': opens[i],
                            'high': highs[i],
                            'low': lows[i],
                            'close': closes[i],
                            'volume': volumes[i]
                        })
                    
                    print(f"[get_candles] ✅ Got {len(candles)} candles")
                    return candles
                else:
                    print(f"[get_candles] ❌ Unexpected response format: {list(data.keys())}")
                    return None
            else:
                print(f"[get_candles] ❌ HTTP error: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"[get_candles] ❌ Exception: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None

# ==================== CONSTANTS ====================
DHAN_NIFTY_50_SECURITY_ID = 13
DHAN_NIFTY_50_SYMBOL = "NIFTY"

# Create global instances
print("\n[GLOBAL] Creating clients...")
coindcx = CoinDCXClient()
dhan = DhanClient()
print(f"[GLOBAL] Ready! Dhan connected: {dhan.connected}\n")

