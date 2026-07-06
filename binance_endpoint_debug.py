import streamlit as st
import requests
import json
import hmac
import hashlib
import time

st.set_page_config(page_title="Binance Endpoint Debug", layout="wide")
st.title("🔧 Binance API Endpoint Debugger")

st.markdown("""
**See exactly what's being sent to Binance:**
- Full URL
- Headers
- Signature
- Query string
- Raw response
""")

# ============================================================
# SIDEBAR - CREDENTIALS
# ============================================================

st.sidebar.header("🔑 Binance API Credentials")
api_key = st.sidebar.text_area("📌 API Key", height=2).strip()
secret_key = st.sidebar.text_area("🔑 Secret Key", height=2).strip()

st.sidebar.markdown("---")
st.sidebar.header("🌐 Mode")

mode = st.sidebar.radio(
    "Select Mode:",
    ["TESTNET", "LIVE"],
    help="TESTNET = Safe testing, LIVE = Real money"
)

if mode == "TESTNET":
    BASE_URL = "https://testnet.binancefuture.com"
    st.sidebar.success("✅ TESTNET - Safe testing")
else:
    BASE_URL = "https://fapi.binance.com"
    st.sidebar.error("⚠️ LIVE - Real money!")

if not api_key or not secret_key:
    st.warning("👈 Enter credentials in sidebar first!")
    st.stop()

# ============================================================
# HELPER FUNCTION
# ============================================================

def get_signature(secret_key, query_string):
    """Generate HMAC SHA256 signature"""
    return hmac.new(
        bytes(secret_key, 'utf-8'),
        bytes(query_string, 'utf-8'),
        hashlib.sha256
    ).hexdigest()

# ============================================================
# MAIN INTERFACE
# ============================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧪 Account (v2)",
    "🧪 Account (v1)",
    "💰 Balance",
    "📍 Positions",
    "🔍 Custom"
])

# ============================================================
# TAB 1: ACCOUNT V2
# ============================================================

with tab1:
    st.header("🧪 Test: Account (v2)")
    st.info("Endpoint: `/fapi/v2/account`")
    
    if st.button("🚀 TEST", key="test_account_v2"):
        with st.spinner("Testing..."):
            
            timestamp = int(time.time() * 1000)
            query_string = f"timestamp={timestamp}"
            signature = get_signature(secret_key, query_string)
            headers = {"X-MBX-APIKEY": api_key}
            url = f"{BASE_URL}/fapi/v2/account?{query_string}&signature={signature}"
            
            # Show what we're sending
            st.markdown("---")
            st.subheader("📤 Request Details")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Base URL:**")
                st.code(BASE_URL)
            with col2:
                st.write("**Endpoint:**")
                st.code("/fapi/v2/account")
            
            st.write("**Full URL:**")
            st.code(url)
            
            st.write("**Headers:**")
            st.json(headers)
            
            st.write("**Query String:**")
            st.code(query_string)
            
            st.write("**Signature:**")
            st.code(signature)
            
            # Make request
            st.markdown("---")
            st.subheader("📥 Response")
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                st.write(f"**Status Code:** {response.status_code}")
                
                if response.status_code == 200:
                    st.success("✅ SUCCESS!")
                    st.json(response.json())
                else:
                    st.error(f"❌ Status {response.status_code}")
                    st.write("**Response Text:**")
                    st.code(response.text)
            
            except Exception as e:
                st.error(f"❌ ERROR: {e}")

# ============================================================
# TAB 2: ACCOUNT V1
# ============================================================

with tab2:
    st.header("🧪 Test: Account (v1)")
    st.info("Endpoint: `/fapi/v1/account`")
    
    if st.button("🚀 TEST", key="test_account_v1"):
        with st.spinner("Testing..."):
            
            timestamp = int(time.time() * 1000)
            query_string = f"timestamp={timestamp}"
            signature = get_signature(secret_key, query_string)
            headers = {"X-MBX-APIKEY": api_key}
            url = f"{BASE_URL}/fapi/v1/account?{query_string}&signature={signature}"
            
            # Show what we're sending
            st.markdown("---")
            st.subheader("📤 Request Details")
            
            st.write("**Full URL:**")
            st.code(url)
            
            st.write("**Headers:**")
            st.json(headers)
            
            # Make request
            st.markdown("---")
            st.subheader("📥 Response")
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                st.write(f"**Status Code:** {response.status_code}")
                
                if response.status_code == 200:
                    st.success("✅ SUCCESS!")
                    st.json(response.json())
                else:
                    st.error(f"❌ Status {response.status_code}")
                    st.code(response.text)
            
            except Exception as e:
                st.error(f"❌ ERROR: {e}")

# ============================================================
# TAB 3: BALANCE
# ============================================================

with tab3:
    st.header("💰 Test: Balance")
    st.info("Endpoint: `/fapi/v2/balance`")
    
    if st.button("🚀 TEST", key="test_balance"):
        with st.spinner("Testing..."):
            
            timestamp = int(time.time() * 1000)
            query_string = f"timestamp={timestamp}"
            signature = get_signature(secret_key, query_string)
            headers = {"X-MBX-APIKEY": api_key}
            url = f"{BASE_URL}/fapi/v2/balance?{query_string}&signature={signature}"
            
            st.markdown("---")
            st.subheader("📤 Request Details")
            st.code(url)
            
            st.markdown("---")
            st.subheader("📥 Response")
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                st.write(f"**Status Code:** {response.status_code}")
                
                if response.status_code == 200:
                    st.success("✅ SUCCESS!")
                    st.json(response.json())
                else:
                    st.error(f"❌ Status {response.status_code}")
                    st.code(response.text)
            
            except Exception as e:
                st.error(f"❌ ERROR: {e}")

# ============================================================
# TAB 4: POSITIONS
# ============================================================

with tab4:
    st.header("📍 Test: Positions")
    st.info("Endpoint: `/fapi/v2/positionRisk`")
    
    if st.button("🚀 TEST", key="test_positions"):
        with st.spinner("Testing..."):
            
            timestamp = int(time.time() * 1000)
            query_string = f"timestamp={timestamp}"
            signature = get_signature(secret_key, query_string)
            headers = {"X-MBX-APIKEY": api_key}
            url = f"{BASE_URL}/fapi/v2/positionRisk?{query_string}&signature={signature}"
            
            st.markdown("---")
            st.subheader("📤 Request Details")
            st.code(url)
            
            st.markdown("---")
            st.subheader("📥 Response")
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                st.write(f"**Status Code:** {response.status_code}")
                
                if response.status_code == 200:
                    st.success("✅ SUCCESS!")
                    st.json(response.json())
                else:
                    st.error(f"❌ Status {response.status_code}")
                    st.code(response.text)
            
            except Exception as e:
                st.error(f"❌ ERROR: {e}")

# ============================================================
# TAB 5: CUSTOM ENDPOINT
# ============================================================

with tab5:
    st.header("🔍 Custom Endpoint Tester")
    st.info("Test any custom endpoint")
    
    custom_endpoint = st.text_input(
        "Endpoint path",
        value="/fapi/v2/account",
        help="e.g., /fapi/v2/account, /fapi/v1/balance, etc."
    )
    
    if st.button("🚀 TEST CUSTOM", key="test_custom"):
        with st.spinner("Testing..."):
            
            timestamp = int(time.time() * 1000)
            query_string = f"timestamp={timestamp}"
            signature = get_signature(secret_key, query_string)
            headers = {"X-MBX-APIKEY": api_key}
            url = f"{BASE_URL}{custom_endpoint}?{query_string}&signature={signature}"
            
            st.markdown("---")
            st.subheader("📤 Request Details")
            st.code(url)
            
            st.markdown("---")
            st.subheader("📥 Response")
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                st.write(f"**Status Code:** {response.status_code}")
                
                if response.status_code == 200:
                    st.success("✅ SUCCESS!")
                    try:
                        st.json(response.json())
                    except:
                        st.code(response.text)
                else:
                    st.error(f"❌ Status {response.status_code}")
                    st.code(response.text)
            
            except Exception as e:
                st.error(f"❌ ERROR: {e}")

st.markdown("---")
st.info(f"""
**Current Mode:** {mode}
**Base URL:** {BASE_URL}
**API Key:** {api_key[:20]}...
**Secret Key:** {secret_key[:20]}...
""")
