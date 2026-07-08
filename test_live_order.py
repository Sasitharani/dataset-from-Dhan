import requests
from coindcx import Client
from datetime import datetime

# Your credentials
COINDCX_API_KEY = "a75a34d3a4dd5c8a53922c2564d90fa1466f62301c51efb8"
COINDCX_API_SECRET = "acdb5ecc637e0b1af09f189137b7a3543f1e28e1ea4890c8fb4958ac4177e25c"

print("=" * 80)
print("🔍 COINDCX LIVE ORDER TEST")
print("=" * 80)

# Test 1: Connection
print("\n✅ TEST 1: API Connection")
try:
    client = Client(api_key=COINDCX_API_KEY, api_secret=COINDCX_API_SECRET)
    print("✓ Client initialized")
except Exception as e:
    print(f"✗ Failed: {e}")
    exit()

# Test 2: Get markets
print("\n✅ TEST 2: Get Markets")
try:
    markets = client.get_markets()
    print(f"✓ Found {len(markets)} markets")
except Exception as e:
    print(f"✗ Failed: {e}")
    exit()

# Test 3: Get balance
print("\n✅ TEST 3: Get Account Balance")
try:
    balance = client.get_balances()
    print(f"✓ Balance retrieved: {balance}")
except Exception as e:
    print(f"✗ Failed: {e}")
    exit()

# Test 4: Get current price
print("\n✅ TEST 4: Get Current Price (BTC/INR)")
try:
    candles = client.get_candles(pair="KC-BTC_INR", interval="1m", limit=1)
    if candles:
        current_price = candles[0]['close']
        print(f"✓ Current BTC/INR price: ₹{current_price:.2f}")
    else:
        print("✗ No candle data")
        exit()
except Exception as e:
    print(f"✗ Failed: {e}")
    exit()

# Test 5: Check API key permissions
print("\n✅ TEST 5: Check API Key Permissions")
try:
    # Try to get open orders (requires trading permission)
    orders = client.get_open_orders("KC-BTC_INR")
    print(f"✓ Can access open orders (trading permission OK)")
except Exception as e:
    print(f"✗ Trading permission issue: {e}")

# Test 6: Place limit order
print("\n✅ TEST 6: Place LIMIT ORDER (TEST)")

pair = "KC-BTC_INR"
side = "BUY"
qty = 0.0001  # Very small quantity
price = current_price * 0.95  # Buy at 5% below market

print(f"\nOrder Details:")
print(f"  Pair: {pair}")
print(f"  Side: {side}")
print(f"  Qty: {qty}")
print(f"  Price: ₹{price:.2f} (5% below market)")
print(f"\n⚠️  This will place a REAL order!")
confirm = input("\nConfirm (YES/NO): ").strip().upper()

if confirm != "YES":
    print("❌ Cancelled")
    exit()

try:
    order = client.place_order(side=side, pair=pair, qty=qty, price=price)
    print(f"\n✓ Order placed successfully!")
    print(f"  Order ID: {order.get('id', 'N/A')}")
    print(f"  Status: {order.get('status', 'N/A')}")
    print(f"  Response: {order}")
    
    print("\n" + "=" * 80)
    print("✅ LIVE ORDER TEST SUCCESSFUL!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n✗ Order failed: {str(e)}")
    print(f"\nPossible issues:")
    print(f"  - API key not authorized for trading")
    print(f"  - Insufficient balance")
    print(f"  - Invalid pair")
    print(f"  - Price/quantity out of bounds")
    print(f"  - Rate limit exceeded")

