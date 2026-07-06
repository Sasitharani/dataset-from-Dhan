import requests
import json
import hashlib
import hmac
import time
from datetime import datetime

class CoinDCXBot:
    def __init__(self, api_key, secret_key):
        """Initialize CoinDCX connection"""
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://api.coindcx.com"
        self.headers = {
            "Content-Type": "application/json",
            "X-API-KEY": api_key
        }
    
    def _get_signature(self, message):
        """Generate HMAC signature for authentication"""
        return hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
    
    # ===== PUBLIC ENDPOINTS (No Auth) =====
    
    def get_market_ticker(self, pair="BTCINR"):
        """Get current price of trading pair"""
        url = f"{self.base_url}/v1/exchange/ticker?pair={pair}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"Error: {resp.status_code} - {resp.text}")
                return None
        except Exception as e:
            print(f"Error fetching ticker: {e}")
            return None
    
    def get_orderbook(self, pair="BTCINR"):
        """Get order book (bids and asks)"""
        url = f"{self.base_url}/v1/orderbook?pair={pair}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"Error: {resp.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching orderbook: {e}")
            return None
    
    def get_candles(self, pair="BTCINR", interval="1h"):
        """Get historical candle data"""
        url = f"{self.base_url}/v1/candles?pair={pair}&interval={interval}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"Error: {resp.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching candles: {e}")
            return None
    
    # ===== AUTHENTICATED ENDPOINTS =====
    
    def get_balance(self):
        """Get account balance"""
        url = f"{self.base_url}/v1/users/balances"
        timeStamp = int(time.time() * 1000)
        body = ""
        
        message = url + str(timeStamp) + body
        signature = self._get_signature(message)
        
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key,
            "X-AUTH-SIGNATURE": signature,
            "X-AUTH-TIMESTAMP": str(timeStamp)
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"Error: {resp.status_code} - {resp.text}")
                return None
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return None
    
    def place_order(self, pair, side, order_type, quantity, price=0):
        """
        Place an order
        
        Args:
            pair: Trading pair (e.g., "BTCINR")
            side: "BUY" or "SELL"
            order_type: "LIMIT" or "MARKET"
            quantity: Amount to trade
            price: Price (0 for market orders)
        """
        url = f"{self.base_url}/v1/orders"
        timeStamp = int(time.time() * 1000)
        
        body = {
            "pair": pair,
            "order_type": order_type,
            "side": side,
            "quantity": quantity,
            "price": price,
            "client_order_id": f"order_{timeStamp}"
        }
        
        body_json = json.dumps(body)
        message = url + str(timeStamp) + body_json
        signature = self._get_signature(message)
        
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key,
            "X-AUTH-SIGNATURE": signature,
            "X-AUTH-TIMESTAMP": str(timeStamp)
        }
        
        try:
            resp = requests.post(url, json=body, headers=headers, timeout=10)
            if resp.status_code in [200, 201]:
                return resp.json()
            else:
                print(f"Error: {resp.status_code} - {resp.text}")
                return None
        except Exception as e:
            print(f"Error placing order: {e}")
            return None
    
    def get_orders(self):
        """Get all open orders"""
        url = f"{self.base_url}/v1/orders"
        timeStamp = int(time.time() * 1000)
        body = ""
        
        message = url + str(timeStamp) + body
        signature = self._get_signature(message)
        
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key,
            "X-AUTH-SIGNATURE": signature,
            "X-AUTH-TIMESTAMP": str(timeStamp)
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"Error: {resp.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching orders: {e}")
            return None
    
    def cancel_order(self, order_id):
        """Cancel an order"""
        url = f"{self.base_url}/v1/orders/{order_id}"
        timeStamp = int(time.time() * 1000)
        body = ""
        
        message = url + str(timeStamp) + body
        signature = self._get_signature(message)
        
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key,
            "X-AUTH-SIGNATURE": signature,
            "X-AUTH-TIMESTAMP": str(timeStamp)
        }
        
        try:
            resp = requests.delete(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"Error: {resp.status_code}")
                return None
        except Exception as e:
            print(f"Error canceling order: {e}")
            return None


# ===== USAGE EXAMPLE =====

if __name__ == "__main__":
    # REPLACE WITH YOUR ACTUAL API KEYS!
    API_KEY = "your_api_key_here"
    SECRET_KEY = "your_secret_key_here"
    
    # Initialize bot
    bot = CoinDCXBot(API_KEY, SECRET_KEY)
    
    print("=" * 50)
    print("🤖 CoinDCX Trading Bot")
    print("=" * 50)
    
    # Get current price
    print("\n📊 Fetching BTC/INR price...")
    ticker = bot.get_market_ticker("BTCINR")
    if ticker:
        print(f"Last Price: ₹{ticker.get('last_price')}")
        print(f"24h High: ₹{ticker.get('high')}")
        print(f"24h Low: ₹{ticker.get('low')}")
        print(f"24h Volume: {ticker.get('volume')}")
    
    # Get account balance
    print("\n💰 Fetching account balance...")
    balance = bot.get_balance()
    if balance:
        print(json.dumps(balance, indent=2))
    
    # Get order book
    print("\n📈 Fetching order book...")
    orderbook = bot.get_orderbook("BTCINR")
    if orderbook:
        print(f"Top Ask: ₹{orderbook['asks'][0][0] if orderbook['asks'] else 'N/A'}")
        print(f"Top Bid: ₹{orderbook['bids'][0][0] if orderbook['bids'] else 'N/A'}")
    
    # Get open orders
    print("\n📋 Fetching open orders...")
    orders = bot.get_orders()
    if orders:
        print(f"Open Orders: {len(orders)}")
        print(json.dumps(orders, indent=2))
    
    # EXAMPLE: Place a limit order (COMMENTED OUT - uncomment to use!)
    # print("\n📍 Placing test order...")
    # order = bot.place_order(
    #     pair="BTCINR",
    #     side="BUY",
    #     order_type="LIMIT",
    #     quantity=0.001,  # 0.001 BTC
    #     price=45000  # ₹45,000
    # )
    # if order:
    #     print(f"Order placed: {order}")

