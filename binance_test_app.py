import streamlit as st
import hmac
import hashlib
import time
import requests

st.set_page_config(page_title="Binance API Tester", layout="wide")
st.title("🚀 Binance API Test")

st.sidebar.header("📝 Binance API Keys")

api_key = st.sidebar.text_input("API Key", placeholder="Paste your API key (64 chars)", type="password")
secret_key = st.sidebar.text_input("Secret Key", placeholder="Paste your secret key (64 chars)", type="password")

if api_key:
    st.sidebar.metric("API Key Length", len(api_key), "Target: 64")
if secret_key:
    st.sidebar.metric("Secret Key Length", len(secret_key), "Target: 64")

st.markdown("---")

# Test button
if st.button("🔧 Test Binance Connection"):
    if not api_key or not secret_key:
        st.error("❌ Paste both keys in sidebar!")
    elif len(api_key) < 60 or len(api_key) > 70:
        st.error(f"❌ API Key seems wrong: {len(api_key)} chars")
    elif len(secret_key) < 60 or len(secret_key) > 70:
        st.error(f"❌ Secret Key seems wrong: {len(secret_key)} chars")
    else:
        st.info("🔄 Testing...")
        
        try:
            def get_signature(secret_key, query_string):
                return hmac.new(bytes(secret_key, 'utf-8'), bytes(query_string, 'utf-8'), hashlib.sha256).hexdigest()
            
            BASE_URL = "https://fapi.binance.com"
            timestamp = int(time.time() * 1000)
            query_string = f"timestamp={timestamp}"
            signature = get_signature(secret_key, query_string)
            
            headers = {"X-MBX-APIKEY": api_key}
            url = f"{BASE_URL}/fapi/v2/account?{query_string}&signature={signature}"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            st.markdown("---")
            st.subheader("📊 Results")
            
            if response.status_code == 200:
                st.success(f"✅ Status 200 - SUCCESS!")
                st.success("✅ **BINANCE API WORKING!**")
                data = response.json()
                with st.expander("Account Details"):
                    st.json(data)
            else:
                st.error(f"❌ Status {response.status_code}")
                st.error(response.text)
                
                # Try to parse error
                try:
                    error_data = response.json()
                    st.write("**Error Details:**")
                    st.json(error_data)
                except:
                    st.write(response.text)
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

st.markdown("---")
st.info("Testing connection... If you get Status 200, keys are working!")
