import streamlit as st
import requests
import json
import hmac
import hashlib
import time

st.set_page_config(page_title="Binance Complete Test", layout="wide")
st.title("🧪 Binance Complete Testing & Setup")

st.markdown("""
**We will test:**
1. ✅ Account connection
2. ✅ Balance check
3. ✅ Order placement (TESTNET = safe!)
4. ✅ Futures access
5. ✅ Ready for algo trading?
""")

st.sidebar.header("🔑 Binance API Credentials")
st.sidebar.warning("⚠️ Credentials are NOT saved or logged")

api_key = st.sidebar.text_input("📌 API Key", type="password", key="api_key")
secret_key = st.sidebar.text_input("🔑 Secret Key", type="password", key="secret_key")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Test Mode")

is_testnet = st.sidebar.checkbox(
    "📝 Use TESTNET (Paper Trading - Risk FREE!)",
    value=True,
    help="TESTNET = Simulated trading, ₹0 risk"
)

if is_testnet:
    BASE_URL = "https://testnet.binancefuture.com"
    st.sidebar.success("✅ TESTNET Mode - Safe for testing!")
else:
    BASE_URL = "https://fapi.binance.com"
    st.sidebar.error("❌ LIVE Mode - Real money at risk!")

def get_signature(secret_key, query_string):
    return hmac.new(bytes(secret_key, 'utf-8'), bytes(query_string, 'utf-8'), hashlib.sha256).hexdigest()

def test_account():
    try:
        timestamp = int(time.time() * 1000)
        query_string = f"timestamp={timestamp}"
        signature = get_signature(secret_key, query_string)
        headers = {"X-MBX-APIKEY": api_key}
        url = f"{BASE_URL}/fapi/v2/account?{query_string}&signature={signature}"
        response = requests.get(url, headers=headers, timeout=10)
        return response.status_code, response.text
    except Exception as e:
        return None, str(e)

def test_balance():
    try:
        timestamp = int(time.time() * 1000)
        query_string = f"timestamp={timestamp}"
        signature = get_signature(secret_key, query_string)
        headers = {"X-MBX-APIKEY": api_key}
        url = f"{BASE_URL}/fapi/v2/balance?{query_string}&signature={signature}"
        response = requests.get(url, headers=headers, timeout=10)
        return response.status_code, response.text
    except Exception as e:
        return None, str(e)

def place_test_order():
    try:
        timestamp = int(time.time() * 1000)
        params = {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "MARKET",
            "quantity": 0.001,
            "timestamp": timestamp
        }
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        signature = get_signature(secret_key, query_string)
        headers = {"X-MBX-APIKEY": api_key}
        url = f"{BASE_URL}/fapi/v1/order?{query_string}&signature={signature}"
        response = requests.post(url, headers=headers, timeout=10)
        return response.status_code, response.text
    except Exception as e:
        return None, str(e)

def get_open_orders():
    try:
        timestamp = int(time.time() * 1000)
        query_string = f"timestamp={timestamp}"
        signature = get_signature(secret_key, query_string)
        headers = {"X-MBX-APIKEY": api_key}
        url = f"{BASE_URL}/fapi/v1/openOrders?{query_string}&signature={signature}"
        response = requests.get(url, headers=headers, timeout=10)
        return response.status_code, response.text
    except Exception as e:
        return None, str(e)

def get_positions():
    try:
        timestamp = int(time.time() * 1000)
        query_string = f"timestamp={timestamp}"
        signature = get_signature(secret_key, query_string)
        headers = {"X-MBX-APIKEY": api_key}
        url = f"{BASE_URL}/fapi/v2/positionRisk?{query_string}&signature={signature}"
        response = requests.get(url, headers=headers, timeout=10)
        return response.status_code, response.text
    except Exception as e:
        return None, str(e)

if not api_key or not secret_key:
    st.warning("👈 Enter your API Key and Secret Key in sidebar first!")
    st.info("""
    How to get keys:
    1. Go to https://www.binance.com/
    2. Login
    3. Profile (top-right) → API Management
    4. Create API → System Generated
    5. Copy API Key and Secret Key
    """)
    st.stop()

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔌 Account",
    "💰 Balance",
    "🚀 Order Test",
    "📍 Positions",
    "📊 Orders",
    "✅ Summary"
])

with tab1:
    st.header("🔌 Account Connection Test")
    st.info("Tests if your API key works and has futures access")
    
    if st.button("🧪 Test Account Connection", key="test_account"):
        with st.spinner("Testing..."):
            status, response = test_account()
            st.write(f"**Status:** {status}")
            
            if status == 200:
                st.success("✅ SUCCESS! API Key is VALID!")
                try:
                    data = json.loads(response)
                    st.json(data)
                    st.success("✅ Your API Key Works!\n✅ You have futures access!\n✅ Ready to trade!")
                except:
                    st.write(response)
            elif status == 401:
                st.error("❌ FAILED! Status 401 - Unauthorized\nYour API Key or Secret Key is WRONG!")
            elif status == 403:
                st.error("❌ FAILED! Status 403 - Forbidden\nYour API Key doesn't have futures permission!")
            else:
                st.error(f"❌ FAILED! Status {status}\n{response}")

with tab2:
    st.header("💰 Account Balance Test")
    st.info("Fetch your USDT balance")
    
    if st.button("🧪 Fetch Balance", key="test_balance"):
        with st.spinner("Fetching..."):
            status, response = test_balance()
            st.write(f"**Status:** {status}")
            
            if status == 200:
                st.success("✅ SUCCESS!")
                try:
                    data = json.loads(response)
                    st.json(data)
                    st.subheader("💵 Your Balance:")
                    for asset in data:
                        if asset['asset'] == 'USDT':
                            free = float(asset['free'])
                            locked = float(asset['locked'])
                            total = free + locked
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Free USDT", f"${free:.2f}")
                            with col2:
                                st.metric("Locked USDT", f"${locked:.2f}")
                            with col3:
                                st.metric("Total USDT", f"${total:.2f}")
                            if is_testnet:
                                st.info("📝 TESTNET: This is paper trading balance")
                            else:
                                st.warning("❌ LIVE: This is REAL money!")
                except:
                    st.write(response)
            else:
                st.error(f"❌ FAILED! Status {status}\n{response}")

with tab3:
    st.header("🚀 Order Placement Test")
    
    if is_testnet:
        st.success("✅ TESTNET Mode - Orders are SIMULATED (safe!)")
    else:
        st.error("❌ LIVE Mode - Orders are REAL! (money at risk!)")
    
    st.warning("⚠️ This will place a TEST market order: BTCUSDT, BUY, 0.001 BTC, Market")
    
    if st.button("🧪 Place Test Market Order", key="test_order"):
        with st.spinner("Placing order..."):
            status, response = place_test_order()
            st.write(f"**Status:** {status}")
            
            if status == 200:
                st.success("✅ SUCCESS! Order placed!")
                try:
                    data = json.loads(response)
                    st.json(data)
                    st.success("🎉 Your API CAN place futures orders!\n✅ Algo trading is possible!")
                except:
                    st.write(response)
            else:
                st.error(f"❌ FAILED! Status {status}\n{response}")

with tab4:
    st.header("📍 Open Positions")
    
    if st.button("🧪 Get Positions", key="test_positions"):
        with st.spinner("Fetching..."):
            status, response = get_positions()
            st.write(f"**Status:** {status}")
            
            if status == 200:
                st.success("✅ SUCCESS!")
                try:
                    data = json.loads(response)
                    if not data or data == []:
                        st.info("ℹ️ No open positions")
                    else:
                        st.json(data)
                except:
                    st.write(response)
            else:
                st.error(f"❌ FAILED! Status {status}\n{response}")

with tab5:
    st.header("📊 Open Orders")
    
    if st.button("🧪 Get Open Orders", key="test_orders"):
        with st.spinner("Fetching..."):
            status, response = get_open_orders()
            st.write(f"**Status:** {status}")
            
            if status == 200:
                st.success("✅ SUCCESS!")
                try:
                    data = json.loads(response)
                    if not data or data == []:
                        st.info("ℹ️ No open orders")
                    else:
                        st.json(data)
                except:
                    st.write(response)
            else:
                st.error(f"❌ FAILED! Status {status}\n{response}")

with tab6:
    st.header("✅ Test Summary")
    st.info("Run all tests at once to verify everything works")
    
    if st.button("🚀 RUN ALL TESTS", key="run_all"):
        with st.spinner("Running all tests..."):
            results = {}
            
            st.subheader("1️⃣ Account Connection")
            status, _ = test_account()
            if status == 200:
                st.success("✅ Account works")
                results['account'] = True
            else:
                st.error(f"❌ Status {status}")
                results['account'] = False
            
            st.subheader("2️⃣ Balance Fetch")
            status, _ = test_balance()
            if status == 200:
                st.success("✅ Balance fetch works")
                results['balance'] = True
            else:
                st.error(f"❌ Status {status}")
                results['balance'] = False
            
            st.subheader("3️⃣ Order Placement")
            status, _ = place_test_order()
            if status == 200:
                st.success("✅ Order placement works")
                results['order'] = True
            else:
                st.error(f"❌ Status {status}")
                results['order'] = False
            
            st.subheader("4️⃣ Positions")
            status, _ = get_positions()
            if status == 200:
                st.success("✅ Position tracking works")
                results['positions'] = True
            else:
                st.error(f"❌ Status {status}")
                results['positions'] = False
            
            st.subheader("5️⃣ Open Orders")
            status, _ = get_open_orders()
            if status == 200:
                st.success("✅ Order tracking works")
                results['orders'] = True
            else:
                st.error(f"❌ Status {status}")
                results['orders'] = False
            
            st.markdown("---")
            st.header("🎯 FINAL VERDICT")
            
            if all(results.values()):
                st.success("✅ ALL TESTS PASSED!\n🎉 YOUR BINANCE API IS FULLY FUNCTIONAL!\nReady to build trading bot!")
            else:
                st.warning("⚠️ Some tests failed! Check individual tabs for details")

st.markdown("---")
st.markdown(f"""
**Current Settings:**
- Mode: {'📝 TESTNET (Paper Trading)' if is_testnet else '❌ LIVE TRADING (Real Money!)'}
- Base URL: {BASE_URL}
""")
