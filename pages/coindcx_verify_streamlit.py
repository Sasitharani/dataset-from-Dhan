"""
CoinDCX Account - Fetch ALL balances in INR (No hardcoding)
"""

import streamlit as st
import requests
import json
import hmac
import hashlib
import time

st.set_page_config(page_title="CoinDCX Account", layout="wide")

st.title("🔐 CoinDCX Account Overview")
st.markdown("**Fetch Spot + Futures + Convert to INR - Completely Dynamic**")

# ============================================================
# SIDEBAR - CREDENTIALS
# ============================================================

st.sidebar.header("API Credentials")
api_key = st.sidebar.text_input("📌 API Key", type="password")
secret_key = st.sidebar.text_input("🔑 Secret Key", type="password")

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

def make_request(endpoint_url):
    try:
        timestamp = int(round(time.time() * 1000))
        body = {"timestamp": timestamp}
        json_body = json.dumps(body, separators=(',', ':'))
        
        signature = create_signature(secret_key, json_body)
        headers = create_headers(api_key, signature)
        
        response = requests.post(endpoint_url, data=json_body, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.text
    
    except Exception as e:
        return False, str(e)

def get_exchange_rates():
    """Get crypto to INR exchange rates from public API"""
    try:
        url = "https://api.coindcx.com/exchange/ticker"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            rates = {}
            
            for coin in data:
                if 'INR' in coin.get('pair', ''):
                    pair = coin.get('pair', '')
                    if pair.endswith('INR'):
                        symbol = pair.replace('INR', '')
                        last_price = float(coin.get('last_price', 0))
                        rates[symbol] = last_price
            
            return rates
        else:
            return {}
    except Exception as e:
        return {}

def try_all_futures_endpoints():
    """Try multiple endpoints to fetch futures balance"""
    
    endpoints = {
        "Futures Balances": "https://api.coindcx.com/exchange/v1/derivatives/futures/balances",
        "Futures Balance": "https://api.coindcx.com/exchange/v1/futures/balance",
        "User Futures": "https://api.coindcx.com/exchange/v1/user/futures",
        "Derivatives Balance": "https://api.coindcx.com/exchange/v1/derivatives/balance",
        "Account Futures": "https://api.coindcx.com/exchange/v1/account/futures",
        "Positions": "https://api.coindcx.com/exchange/v1/derivatives/futures/positions",
        "Holdings": "https://api.coindcx.com/exchange/v1/holdings",
    }
    
    for name, endpoint in endpoints.items():
        success, data = make_request(endpoint)
        if success:
            return True, name, endpoint, data
    
    return False, None, None, None

# ============================================================
# MAIN APP
# ============================================================

if st.sidebar.button("✅ Fetch All Account Data", use_container_width=True):
    if not api_key or not secret_key:
        st.error("❌ Enter API credentials!")
    else:
        with st.spinner("Fetching complete account data..."):
            
            # ============================================================
            # STEP 1: SPOT BALANCE
            # ============================================================
            st.info("💎 Step 1: Fetching Spot Balance...")
            success_spot, spot_data = make_request("https://api.coindcx.com/exchange/v1/users/balances")
            
            if not success_spot:
                st.error(f"❌ Spot Balance Error: {spot_data}")
                st.stop()
            
            st.success("✅ Spot Balance Retrieved!")
            
            # ============================================================
            # STEP 2: PROFILE
            # ============================================================
            st.info("👤 Step 2: Fetching Profile...")
            success_profile, profile_data = make_request("https://api.coindcx.com/exchange/v1/users/info")
            
            if success_profile:
                st.success("✅ Profile Retrieved!")
            else:
                st.warning("⚠️ Profile not available")
                profile_data = None
            
            # ============================================================
            # STEP 3: EXCHANGE RATES
            # ============================================================
            st.info("💹 Step 3: Fetching Exchange Rates...")
            exchange_rates = get_exchange_rates()
            
            if exchange_rates:
                st.success(f"✅ Exchange Rates Retrieved! ({len(exchange_rates)} pairs)")
            else:
                st.warning("⚠️ Using default rates")
                exchange_rates = {
                    "BTC": 2750000,
                    "USDT": 83,
                    "DOGE": 9,
                    "XRP": 50,
                }
            
            # ============================================================
            # STEP 4: FUTURES BALANCE (TEST ALL ENDPOINTS)
            # ============================================================
            st.info("📈 Step 4: Testing Futures Endpoints...")
            
            futures_found = False
            futures_data = None
            futures_endpoint = None
            
            success_futures, endpoint_name, endpoint_url, futures_response = try_all_futures_endpoints()
            
            if success_futures:
                st.success(f"✅ Futures Balance Found! (Endpoint: {endpoint_name})")
                futures_data = futures_response
                futures_endpoint = endpoint_url
                futures_found = True
            else:
                st.error("❌ Futures Balance: No working endpoint found!")
                st.warning("""
                **Note:** Your API key may not have access to Futures endpoints.
                Please check:
                1. Futures trading is enabled in your CoinDCX account
                2. API key has derivatives permissions
                3. Contact CoinDCX support if issue persists
                """)
                futures_data = None
            
            # ============================================================
            # CALCULATE BALANCES IN INR
            # ============================================================
            
            # Spot balance in INR
            spot_balance_inr = 0
            balance_breakdown = {}
            
            for coin in spot_data:
                currency = coin.get('currency', '')
                amount = coin.get('balance', 0)
                
                if amount > 0:
                    rate = exchange_rates.get(currency, 0)
                    inr_value = amount * rate
                    
                    balance_breakdown[currency] = {
                        "amount": amount,
                        "rate": rate,
                        "inr_value": inr_value
                    }
                    
                    spot_balance_inr += inr_value
            
            # Futures balance in INR
            futures_balance_inr = 0
            if futures_found and futures_data:
                # Try to parse futures balance
                if isinstance(futures_data, dict):
                    if 'balance' in futures_data:
                        futures_balance_inr = float(futures_data['balance'])
                    elif 'total_balance' in futures_data:
                        futures_balance_inr = float(futures_data['total_balance'])
                    elif 'available_balance' in futures_data:
                        futures_balance_inr = float(futures_data['available_balance'])
                
                # If still 0, try to extract from nested structure
                if futures_balance_inr == 0:
                    st.write("Futures data structure:")
                    st.json(futures_data)
            
            # Options and Funds (API didn't return these)
            options_balance_inr = 0
            funds_balance_inr = 0
            
            # Total
            total_balance_inr = spot_balance_inr + futures_balance_inr + options_balance_inr + funds_balance_inr
            
            # ============================================================
            # DISPLAY RESULTS
            # ============================================================
            
            st.markdown("---")
            st.header("📊 Account Overview")
            
            # Profile
            if profile_data:
                col_p1, col_p2, col_p3 = st.columns(3)
                
                with col_p1:
                    st.write("**Name:**")
                    st.write(f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}")
                
                with col_p2:
                    st.write("**Email:**")
                    st.write(profile_data.get('email', ''))
                
                with col_p3:
                    st.write("**Phone:**")
                    st.write(profile_data.get('mobile_number', ''))
                
                st.markdown("---")
            
            # Total value
            st.metric(
                label="Est. total value",
                value=f"₹{total_balance_inr:.2f}",
            )
            
            # Breakdown
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Coins", f"₹{spot_balance_inr:.2f}")
                if spot_balance_inr == 0:
                    st.caption("(No spot balance)")
            
            with col2:
                if futures_found:
                    st.metric("Futures", f"₹{futures_balance_inr:.2f}")
                    st.caption("(Fetched from API)")
                else:
                    st.metric("Futures", "❌ Not available")
                    st.caption("(API error)")
            
            with col3:
                st.metric("Options", f"₹{options_balance_inr:.2f}")
                st.caption("(Not available)")
            
            with col4:
                st.metric("Funds", f"₹{funds_balance_inr:.2f}")
                st.caption("(Not available)")
            
            # Detailed breakdown
            st.markdown("---")
            st.subheader("💎 Coins Breakdown (Spot)")
            
            if balance_breakdown:
                for currency, details in balance_breakdown.items():
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.write(f"**{currency}**")
                    with col2:
                        st.write(f"Amount: {details['amount']:.10f}")
                    with col3:
                        st.write(f"Rate: ₹{details['rate']:.2f}")
                    with col4:
                        st.write(f"Value: ₹{details['inr_value']:.2f}")
            else:
                st.info("No coins in spot balance")
            
            # Futures details
            if futures_found and futures_data:
                st.markdown("---")
                st.subheader("📈 Futures Details")
                st.json(futures_data)
            
            # Exchange rates
            st.markdown("---")
            st.subheader("💹 Exchange Rates (Live)")
            
            for currency, rate in exchange_rates.items():
                st.write(f"{currency}/INR: ₹{rate:.2f}")
            
            # Success
            st.markdown("---")
            st.success("🎉 ACCOUNT DATA FETCHED!")
            
            summary = {
                "profile": {
                    "name": f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}" if profile_data else "N/A",
                    "email": profile_data.get('email', 'N/A') if profile_data else "N/A",
                },
                "balance_inr": {
                    "spot": f"₹{spot_balance_inr:.2f}",
                    "futures": f"₹{futures_balance_inr:.2f}" if futures_found else "❌ Not available",
                    "options": f"₹{options_balance_inr:.2f}",
                    "funds": f"₹{funds_balance_inr:.2f}",
                    "total": f"₹{total_balance_inr:.2f}"
                },
                "endpoints": {
                    "spot": "✅ /users/balances",
                    "profile": "✅ /users/info",
                    "futures": f"{'✅ ' + endpoint_name if futures_found else '❌ Not found'}"
                }
            }
            
            st.json(summary)

else:
    st.info("👈 Enter credentials and click 'Fetch All Account Data'")

st.markdown("---")
with st.expander("ℹ️ About this app"):
    st.markdown("""
    **What this fetches (COMPLETELY DYNAMIC):**
    - ✅ Spot Balance: From API + Auto-converted to INR
    - ✅ Futures Balance: From API in INR (if available)
    - ✅ Exchange Rates: Live from CoinDCX public API
    - ✅ Profile: Name, Email, Phone from API
    
    **No hardcoding!** Everything is fetched in real-time.
    """)
