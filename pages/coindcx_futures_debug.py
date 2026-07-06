"""
CoinDCX Futures Balance - Comprehensive Debug
Find the CORRECT way to fetch futures balance
"""

import streamlit as st
import requests
import json
import hmac
import hashlib
import time

st.set_page_config(page_title="CoinDCX Futures Debug", layout="wide")

st.title("🔍 CoinDCX Futures Balance - Debug")
st.markdown("**Find the CORRECT endpoint and value for futures trading**")

# ============================================================
# SIDEBAR - CREDENTIALS
# ============================================================

st.sidebar.header("API Credentials")
api_key = st.sidebar.text_input("📌 API Key", type="password")
secret_key = st.sidebar.text_input("🔑 Secret Key", type="password")

st.sidebar.markdown("---")
st.sidebar.header("Expected Values (From Dashboard)")
st.sidebar.info("These are what we SHOULD see:")
expected_spot = st.sidebar.number_input("Expected Spot (₹)", value=59.72)
expected_futures = st.sidebar.number_input("Expected Futures (₹)", value=810.78)
expected_total = st.sidebar.number_input("Expected Total (₹)", value=870.51)

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def create_signature(secret_key, json_body):
    secret_bytes = bytes(secret_key, encoding='utf-8')
    signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()
    return signature

def create_headers(api_key, signature):
    return {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': api_key,
        'X-AUTH-SIGNATURE': signature
    }

def test_endpoint(endpoint_url, endpoint_name):
    """Test endpoint and return full response"""
    try:
        timestamp = int(round(time.time() * 1000))
        body = {"timestamp": timestamp}
        json_body = json.dumps(body, separators=(',', ':'))
        
        signature = create_signature(secret_key, json_body)
        headers = create_headers(api_key, signature)
        
        response = requests.post(endpoint_url, data=json_body, headers=headers, timeout=10)
        
        return response.status_code, response.json() if response.status_code == 200 else response.text
    
    except Exception as e:
        return None, str(e)

# ============================================================
# MAIN APP
# ============================================================

if st.sidebar.button("🔍 Debug All Endpoints", use_container_width=True):
    if not api_key or not secret_key:
        st.error("❌ Enter credentials!")
    else:
        with st.spinner("Testing ALL endpoints..."):
            
            # ============================================================
            # TEST SPOT BALANCE
            # ============================================================
            
            st.header("💎 SPOT BALANCE TEST")
            st.info("Testing: /users/balances")
            
            status, spot_data = test_endpoint(
                "https://api.coindcx.com/exchange/v1/users/balances",
                "Spot Balance"
            )
            
            if status == 200:
                st.success(f"✅ Status: {status}")
                st.json(spot_data)
                
                # Calculate spot value
                exchange_rates = {
                    "BTC": 2750000,
                    "USDT": 83,
                    "INR": 1,
                    "DOGE": 9,
                    "XRP": 50,
                }
                
                spot_inr = 0
                st.write("**Spot Balance Calculation:**")
                for coin in spot_data:
                    curr = coin.get('currency')
                    amt = coin.get('balance', 0)
                    rate = exchange_rates.get(curr, 0)
                    value = amt * rate
                    spot_inr += value
                    st.write(f"{curr}: {amt} × {rate} = ₹{value:.2f}")
                
                st.metric("Total Spot (Calculated)", f"₹{spot_inr:.2f}")
                st.metric("Expected Spot", f"₹{expected_spot:.2f}")
                
                if abs(spot_inr - expected_spot) > 1:
                    st.warning(f"⚠️ MISMATCH! Got ₹{spot_inr:.2f}, expected ₹{expected_spot:.2f}")
                    st.error("**EXCHANGE RATES ARE WRONG!**")
                    st.write("We need to fetch LIVE exchange rates, not hardcoded ones!")
            else:
                st.error(f"❌ Status: {status} - {spot_data}")
            
            # ============================================================
            # TEST FUTURES ENDPOINTS
            # ============================================================
            
            st.markdown("---")
            st.header("📈 FUTURES BALANCE TEST")
            
            futures_endpoints = {
                "/derivatives/futures/balances": "https://api.coindcx.com/exchange/v1/derivatives/futures/balances",
                "/futures/balance": "https://api.coindcx.com/exchange/v1/futures/balance",
                "/user/futures/balance": "https://api.coindcx.com/exchange/v1/user/futures/balance",
                "/account/futures": "https://api.coindcx.com/exchange/v1/account/futures",
                "/derivatives/balance": "https://api.coindcx.com/exchange/v1/derivatives/balance",
                "/holdings": "https://api.coindcx.com/exchange/v1/holdings",
                "/portfolio": "https://api.coindcx.com/exchange/v1/portfolio",
                "/user/portfolio": "https://api.coindcx.com/exchange/v1/user/portfolio",
                "/account/balances": "https://api.coindcx.com/exchange/v1/account/balances",
                "/balances/all": "https://api.coindcx.com/exchange/v1/balances/all",
                "/balance": "https://api.coindcx.com/exchange/v1/balance",
                "/user/balance": "https://api.coindcx.com/exchange/v1/user/balance",
            }
            
            futures_found = []
            
            for endpoint_name, endpoint_url in futures_endpoints.items():
                status, data = test_endpoint(endpoint_url, endpoint_name)
                
                if status == 200:
                    st.success(f"✅ {endpoint_name} (Status: {status})")
                    st.json(data)
                    futures_found.append((endpoint_name, endpoint_url, data))
                else:
                    st.write(f"⚠️ {endpoint_name} (Status: {status})")
            
            # ============================================================
            # ANALYZE RESULTS
            # ============================================================
            
            st.markdown("---")
            st.header("📊 ANALYSIS")
            
            if futures_found:
                st.success(f"✅ Found {len(futures_found)} working futures endpoint(s)!")
                
                for name, url, data in futures_found:
                    st.subheader(f"Endpoint: {name}")
                    st.write(f"URL: {url}")
                    st.json(data)
                    
                    # Try to extract futures value
                    st.write("**Trying to extract futures value...**")
                    if isinstance(data, dict):
                        st.write("Structure:")
                        for key in data.keys():
                            st.write(f"- {key}: {data[key]}")
                    elif isinstance(data, list):
                        st.write(f"List with {len(data)} items")
                        if len(data) > 0:
                            st.write("First item:")
                            st.json(data[0])
            else:
                st.error("❌ NO working futures endpoints found!")
                st.error("**YOUR API KEY MAY NOT HAVE FUTURES ACCESS!**")
                st.warning("""
                **CRITICAL ISSUE FOR ALGORITHMIC TRADING!**
                
                Your API key cannot access futures balance.
                
                Solutions:
                1. ✅ Check if futures trading is ENABLED in CoinDCX account
                2. ✅ Regenerate API key with DERIVATIVES permissions
                3. ✅ Contact CoinDCX support to enable API futures access
                
                **Without this, algorithmic trading is NOT POSSIBLE!**
                """)
            
            # ============================================================
            # SUMMARY
            # ============================================================
            
            st.markdown("---")
            st.header("🎯 SUMMARY")
            
            summary = {
                "spot_balance": {
                    "fetched": spot_inr if status == 200 else "ERROR",
                    "expected": expected_spot,
                    "status": "✅ OK" if status == 200 else "❌ ERROR"
                },
                "futures_endpoints_working": len(futures_found),
                "futures_data_found": "✅ YES" if futures_found else "❌ NO",
                "ready_for_trading": "✅ YES" if futures_found and status == 200 else "❌ NO"
            }
            
            st.json(summary)

else:
    st.info("👈 Enter credentials and click button")

st.markdown("---")
with st.expander("⚠️ IMPORTANT FOR FUTURES TRADING"):
    st.markdown("""
    **For algorithmic trading on futures you MUST have:**
    
    1. ✅ Futures balance endpoint working
    2. ✅ Ability to place futures orders
    3. ✅ Real-time balance updates
    4. ✅ Correct API key with derivatives permissions
    
    **If futures endpoints show 404, you CANNOT trade futures!**
    
    **Next steps if this works:**
    - Build place_order function for futures
    - Build cancel_order function
    - Build position monitoring
    - Build algo trading strategy
    """)
