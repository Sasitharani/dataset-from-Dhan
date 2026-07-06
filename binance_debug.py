import streamlit as st
import requests
import json
import hmac
import hashlib
import time

st.set_page_config(page_title="Binance API Debug", layout="wide")
st.title("🔍 Binance API Keys - Debug Dashboard")

st.markdown("""
**Troubleshoot your API credentials here:**
- ✅ Auto-clean spaces and newlines
- ✅ Test both TESTNET and LIVE
- ✅ See exact error messages
- ✅ Diagnose the issue
""")

# ============================================================
# SIDEBAR - INPUT
# ============================================================

st.sidebar.header("🔑 Your Credentials")
st.sidebar.warning("⚠️ NOT saved or logged - just for testing")

api_key_raw = st.sidebar.text_area("📌 API Key", height=3, help="Paste exactly as copied (spaces will be auto-cleaned)")
secret_key_raw = st.sidebar.text_area("🔑 Secret Key", height=3, help="Paste exactly as copied (spaces will be auto-cleaned)")

# ============================================================
# AUTO-CLEAN KEYS
# ============================================================

api_key = api_key_raw.strip() if api_key_raw else ""
secret_key = secret_key_raw.strip() if secret_key_raw else ""

# Show if cleaning happened
if api_key_raw and api_key != api_key_raw:
    st.sidebar.warning(f"🧹 Auto-cleaned API Key (removed {len(api_key_raw) - len(api_key)} spaces)")

if secret_key_raw and secret_key != secret_key_raw:
    st.sidebar.warning(f"🧹 Auto-cleaned Secret Key (removed {len(secret_key_raw) - len(secret_key)} spaces)")

# ============================================================
# MAIN CONTENT
# ============================================================

if not api_key or not secret_key:
    st.warning("👈 Enter API Key and Secret Key in sidebar first!")
    st.stop()

# ============================================================
# TAB 1: CHECK FOR ISSUES
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "🔎 Check Keys",
    "🧪 Test TESTNET",
    "🧪 Test LIVE",
    "📊 Summary"
])

with tab1:
    st.header("🔎 Checking Your API Keys for Issues")
    
    if st.button("🔍 ANALYZE KEYS", key="check_keys"):
        st.markdown("---")
        
        # ============================================================
        # CHECK 1: LENGTH
        # ============================================================
        
        st.subheader("1️⃣ Key Length Check")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**API Key Length:**")
            st.write(f"{len(api_key)} characters")
            if len(api_key) < 50:
                st.error("❌ API Key too short! (should be ~64-65 chars)")
            elif len(api_key) > 100:
                st.error("❌ API Key too long! (should be ~64-65 chars)")
            else:
                st.success("✅ Length looks good!")
        
        with col2:
            st.write("**Secret Key Length:**")
            st.write(f"{len(secret_key)} characters")
            if len(secret_key) < 80:
                st.error("❌ Secret Key too short! (should be ~88-90 chars)")
            elif len(secret_key) > 120:
                st.error("❌ Secret Key too long! (should be ~88-90 chars)")
            else:
                st.success("✅ Length looks good!")
        
        # ============================================================
        # CHECK 2: SPACES (already cleaned, but show what was cleaned)
        # ============================================================
        
        st.markdown("---")
        st.subheader("2️⃣ Spaces Check")
        
        if api_key_raw != api_key:
            st.warning(f"🧹 Cleaned API Key: removed {len(api_key_raw) - len(api_key)} leading/trailing spaces")
        else:
            st.success("✅ No leading/trailing spaces in API Key!")
        
        if secret_key_raw != secret_key:
            st.warning(f"🧹 Cleaned Secret Key: removed {len(secret_key_raw) - len(secret_key)} leading/trailing spaces")
        else:
            st.success("✅ No leading/trailing spaces in Secret Key!")
        
        # ============================================================
        # CHECK 3: NEWLINES
        # ============================================================
        
        st.markdown("---")
        st.subheader("3️⃣ Newlines/Tab Check")
        
        has_newline_api = "\n" in api_key or "\t" in api_key
        has_newline_secret = "\n" in secret_key or "\t" in secret_key
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**API Key Newlines:**")
            if has_newline_api:
                st.error("❌ Found newline/tab character!")
            else:
                st.success("✅ No newlines/tabs!")
        
        with col2:
            st.write("**Secret Key Newlines:**")
            if has_newline_secret:
                st.error("❌ Found newline/tab character!")
            else:
                st.success("✅ No newlines/tabs!")
        
        # ============================================================
        # CHECK 4: DISPLAY
        # ============================================================
        
        st.markdown("---")
        st.subheader("4️⃣ Key Preview (Cleaned)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**API Key (first 30 chars):**")
            st.code(api_key[:30] + "...")
        
        with col2:
            st.write("**Secret Key (first 30 chars):**")
            st.code(secret_key[:30] + "...")
        
        # ============================================================
        # SUMMARY
        # ============================================================
        
        st.markdown("---")
        st.subheader("✅ Summary")
        
        issues = []
        if len(api_key) < 50 or len(api_key) > 100:
            issues.append(f"API Key length wrong ({len(api_key)} chars, should be ~65)")
        if len(secret_key) < 80 or len(secret_key) > 120:
            issues.append(f"Secret Key length wrong ({len(secret_key)} chars, should be ~90)")
        if has_newline_api or has_newline_secret:
            issues.append("Keys have newlines/tabs")
        
        if not issues:
            st.success("✅ Keys look GOOD! No format issues detected!")
            st.success("✅ Ready to test connection!")
            st.info("➡️ Proceed to 'Test TESTNET' or 'Test LIVE' tabs")
        else:
            st.error("❌ Found issues:")
            for issue in issues:
                st.write(f"- {issue}")
            st.error("⚠️ Go back to Binance and create a NEW API key")

# ============================================================
# TAB 2: TEST TESTNET
# ============================================================

with tab2:
    st.header("🧪 Test TESTNET Connection")
    st.info("TESTNET = Paper trading (safe, no real money!)")
    
    if st.button("🚀 TEST TESTNET", key="test_testnet"):
        with st.spinner("Testing TESTNET connection..."):
            
            try:
                timestamp = int(time.time() * 1000)
                query_string = f"timestamp={timestamp}"
                
                signature = hmac.new(
                    bytes(secret_key, 'utf-8'),
                    bytes(query_string, 'utf-8'),
                    hashlib.sha256
                ).hexdigest()
                
                headers = {"X-MBX-APIKEY": api_key}
                url = f"https://testnet.binancefuture.com/fapi/v2/account?{query_string}&signature={signature}"
                
                st.write("**Request Details:**")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"Host: `testnet.binancefuture.com`")
                with col2:
                    st.write(f"Timestamp: `{timestamp}`")
                
                st.write("**Status: Sending request...**")
                response = requests.get(url, headers=headers, timeout=10)
                
                st.markdown("---")
                st.write(f"## Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    st.success("✅ SUCCESS! TESTNET CONNECTION WORKS!")
                    try:
                        data = response.json()
                        st.success("✅ API Key is VALID!")
                        st.success("✅ TESTNET access is ENABLED!")
                        
                        st.subheader("✅ Account Verified!")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("User ID", data.get('userId', 'N/A'))
                            st.metric("Can Trade", "✅ Yes" if data.get('canTrade') else "❌ No")
                        with col2:
                            st.metric("Total Balance", f"${data.get('totalWalletBalance', 0):.2f}")
                            st.metric("Unrealized PnL", f"${data.get('totalUnrealizedProfit', 0):.2f}")
                        
                    except:
                        st.write(response.text)
                
                elif response.status_code == 401:
                    st.error("❌ STATUS 401 - UNAUTHORIZED")
                    st.error("""
                    **This means your API Key or Secret Key is WRONG!**
                    
                    Possible causes:
                    1. ❌ Secret Key is incomplete (should be ~90 chars)
                    2. ❌ You copied the wrong key
                    3. ❌ Keys are not from same API creation
                    4. ❌ API key not activated yet (wait 1-2 min)
                    
                    **Solution:**
                    1. Go to https://www.binance.com/
                    2. Login
                    3. Profile → API Management
                    4. **DELETE** your current API key
                    5. Wait 10 seconds
                    6. **CREATE** new API key
                    7. **Name it:** AlgoTradingBot
                    8. **Copy FULL Secret Key** (entire 90 chars!)
                    9. Make sure "Enable Futures" is checked
                    10. Wait 1-2 minutes for activation
                    11. Come back here and test again
                    """)
                    try:
                        st.json(json.loads(response.text))
                    except:
                        pass
                
                elif response.status_code == 403:
                    st.error("❌ STATUS 403 - FORBIDDEN")
                    st.error("""
                    **Your API key doesn't have futures permission!**
                    
                    **Solution:**
                    1. Go to Binance → API Management
                    2. Find your API key
                    3. Click **Edit** button
                    4. **Enable:** "Enable Futures Trading"
                    5. **Enable:** "Enable Spot & Margin Trading"
                    6. Click **Save**
                    7. Try again
                    """)
                    try:
                        st.json(json.loads(response.text))
                    except:
                        pass
                
                else:
                    st.warning(f"⚠️ STATUS {response.status_code}")
                    st.write("**Response:**")
                    try:
                        st.json(json.loads(response.text))
                    except:
                        st.write(response.text)
            
            except Exception as e:
                st.error(f"❌ ERROR: {e}")

# ============================================================
# TAB 3: TEST LIVE
# ============================================================

with tab3:
    st.header("🧪 Test LIVE Connection")
    st.warning("⚠️ LIVE = Real money at risk!")
    
    if st.button("🚀 TEST LIVE", key="test_live"):
        with st.spinner("Testing LIVE connection..."):
            
            try:
                timestamp = int(time.time() * 1000)
                query_string = f"timestamp={timestamp}"
                
                signature = hmac.new(
                    bytes(secret_key, 'utf-8'),
                    bytes(query_string, 'utf-8'),
                    hashlib.sha256
                ).hexdigest()
                
                headers = {"X-MBX-APIKEY": api_key}
                url = f"https://fapi.binance.com/fapi/v2/account?{query_string}&signature={signature}"
                
                st.write("**Request Details:**")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"Host: `fapi.binance.com`")
                with col2:
                    st.write(f"Timestamp: `{timestamp}`")
                
                st.write("**Status: Sending request...**")
                response = requests.get(url, headers=headers, timeout=10)
                
                st.markdown("---")
                st.write(f"## Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    st.success("✅ SUCCESS! LIVE CONNECTION WORKS!")
                    try:
                        data = response.json()
                        st.success("✅ API Key is VALID!")
                        st.success("✅ LIVE access is ENABLED!")
                        
                        st.subheader("✅ Account Verified!")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("User ID", data.get('userId', 'N/A'))
                            st.metric("Can Trade", "✅ Yes" if data.get('canTrade') else "❌ No")
                        with col2:
                            st.metric("Total Balance", f"${data.get('totalWalletBalance', 0):.2f}")
                            st.metric("Unrealized PnL", f"${data.get('totalUnrealizedProfit', 0):.2f}")
                        
                    except:
                        st.write(response.text)
                
                elif response.status_code == 401:
                    st.error("❌ STATUS 401 - UNAUTHORIZED")
                    st.error("""
                    **Same issue as TESTNET:**
                    Your API Key or Secret Key is WRONG!
                    
                    See the "Test TESTNET" tab for solutions.
                    """)
                    try:
                        st.json(json.loads(response.text))
                    except:
                        pass
                
                else:
                    st.warning(f"⚠️ STATUS {response.status_code}")
                    st.write("**Response:**")
                    try:
                        st.json(json.loads(response.text))
                    except:
                        st.write(response.text)
            
            except Exception as e:
                st.error(f"❌ ERROR: {e}")

# ============================================================
# TAB 4: SUMMARY & NEXT STEPS
# ============================================================

with tab4:
    st.header("📊 Summary & Troubleshooting")
    
    st.markdown("""
    ## If All Tests Show ✅ Status 200:
    **Your API Keys are CORRECT!** 🎉
    
    Next steps:
    1. ✅ Go back to main Streamlit app
    2. ✅ Use your keys
    3. ✅ Start building trading bot!
    
    ---
    
    ## If Tests Show ❌ Status 401:
    **Your API Keys need to be recreated!**
    
    The most common issue:
    - Secret Key is too short (less than 88 chars)
    - This means you didn't copy the FULL Secret Key
    
    **Fix it:**
    1. ✅ Go to https://www.binance.com/
    2. ✅ Login
    3. ✅ Profile → API Management
    4. ✅ DELETE old API key (trash icon)
    5. ✅ Click "Create API"
    6. ✅ Choose "System Generated"
    7. ✅ Name: "AlgoTradingBot"
    8. ✅ Click "Create"
    9. ✅ **IMPORTANT:** Copy the FULL Secret Key (all 90 chars!)
    10. ✅ Click "Edit"
    11. ✅ Enable: Spot Trading + Futures
    12. ✅ Save
    13. ✅ Wait 1-2 minutes
    14. ✅ Come back here and test
    
    ---
    
    ## Good News:
    The app now **auto-cleans spaces!**
    - No need to manually strip spaces
    - Just paste and it works
    - Focus on getting the FULL keys!
    """)

st.markdown("---")
st.info("""
**Status Code Legend:**
- 200 = ✅ Keys are CORRECT!
- 401 = ❌ Secret Key too short or wrong
- 403 = ❌ API doesn't have futures permission
- Other = ⚠️ Different network issue
""")
