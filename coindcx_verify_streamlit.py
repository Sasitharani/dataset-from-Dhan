"""
CoinDCX Account Verification - Streamlit App
Verify connection and extract: Balance, Name, Email
"""

import streamlit as st
import requests
import json
import hmac
import hashlib
import time

st.set_page_config(page_title="CoinDCX Verification", layout="wide")

st.title("🔐 CoinDCX Account Verification")
st.markdown("Verify your connection and get account details (Balance, Name, Email)")

# ============================================================
# SIDEBAR - CREDENTIALS INPUT
# ============================================================

st.sidebar.header("API Credentials")
st.sidebar.warning("⚠️ Credentials are NOT saved or logged!")

api_key = st.sidebar.text_input("📌 API Key", type="password", help="Your CoinDCX API Key")
secret_key = st.sidebar.text_input("🔑 Secret Key", type="password", help="Your CoinDCX Secret Key")

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def create_signature(secret_key, json_body):
    """Create HMAC SHA256 signature"""
    secret_bytes = bytes(secret_key, encoding='utf-8')
    signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()
    return signature

def create_headers(api_key, signature):
    """Create request headers"""
    return {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': api_key,
        'X-AUTH-SIGNATURE': signature
    }

def make_request(endpoint_url):
    """Make authenticated request to endpoint"""
    try:
        # Create timestamp
        timestamp = int(round(time.time() * 1000))
        
        # Create body
        body = {"timestamp": timestamp}
        json_body = json.dumps(body, separators=(',', ':'))
        
        # Create signature
        signature = create_signature(secret_key, json_body)
        
        # Create headers
        headers = create_headers(api_key, signature)
        
        # Make request
        response = requests.post(endpoint_url, data=json_body, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.text
    
    except Exception as e:
        return False, str(e)

# ============================================================
# MAIN APP
# ============================================================

if st.sidebar.button("🔍 Verify Connection", use_container_width=True):
    if not api_key or not secret_key:
        st.error("❌ Please enter both API Key and Secret Key!")
    else:
        with st.spinner("Testing connection..."):
            
            # Test Balance Endpoint
            st.info("📊 Step 1: Testing Balance Endpoint...")
            success, balance_data = make_request("https://api.coindcx.com/exchange/v1/users/balances")
            
            if not success:
                st.error(f"❌ Connection Failed!\n\n{balance_data}")
                st.stop()
            
            st.success("✅ Balance Endpoint Connected!")
            
            # Test Profile Endpoint
            st.info("👤 Step 2: Testing Profile Endpoint...")
            success, profile_data = make_request("https://api.coindcx.com/exchange/v1/users/profile")
            
            if not success:
                st.warning(f"⚠️ Profile Endpoint Failed: {profile_data}")
                profile_data = None
            else:
                st.success("✅ Profile Endpoint Connected!")
            
            # ============================================================
            # DISPLAY RESULTS
            # ============================================================
            
            st.markdown("---")
            st.header("📊 Account Details")
            
            # Balance
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("💰 Balance Information")
                st.json(balance_data)
            
            # Profile
            with col2:
                st.subheader("👤 Profile Information")
                if profile_data:
                    st.json(profile_data)
                    
                    # Extract key details
                    st.markdown("---")
                    st.subheader("✨ Your Details")
                    
                    details = []
                    if 'name' in profile_data:
                        details.append(f"**Name:** {profile_data['name']}")
                    if 'email' in profile_data:
                        details.append(f"**Email:** {profile_data['email']}")
                    if 'username' in profile_data:
                        details.append(f"**Username:** {profile_data['username']}")
                    if 'user_id' in profile_data:
                        details.append(f"**User ID:** {profile_data['user_id']}")
                    
                    for detail in details:
                        st.markdown(detail)
                else:
                    st.warning("Profile data not available")
            
            # ============================================================
            # SUCCESS MESSAGE
            # ============================================================
            
            st.markdown("---")
            st.success("🎉 VERIFICATION COMPLETE!")
            st.info("""
            ✅ Connected to CoinDCX API
            ✅ Balance retrieved
            ✅ Profile information retrieved
            
            **Next Step:** Share the details above with me, then we'll build BUY/SELL trading functions! 🚀
            """)

else:
    st.info("👈 Enter your API credentials in the sidebar and click 'Verify Connection'")

# ============================================================
# INFO SECTION
# ============================================================

st.markdown("---")
with st.expander("ℹ️ How to use this app"):
    st.markdown("""
    1. **Enter API Credentials** in the left sidebar
    2. Click **"Verify Connection"** button
    3. App will test your connection to CoinDCX
    4. View your balance and profile details
    5. Copy the details and share with your assistant
    
    **Security:**
    - ✅ Credentials are NOT saved anywhere
    - ✅ Credentials are NOT logged
    - ✅ Only read-only endpoints are called
    - ✅ No trades are placed
    """)
