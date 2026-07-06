import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

st.set_page_config(page_title="Dhan Data Extractor DEBUG", layout="wide")

st.title("🔧 Dhan Data Extractor (DEBUG MODE)")
st.markdown("**DEBUG MODE:** Shows full API response to diagnose extraction issue")

st.header("🔑 Step 1: Enter API Token")

api_token = st.text_input(
    "Paste your Dhan API token",
    type="password",
    help="Your API token from Dhan settings"
)

st.header("📅 Step 2: Select Date")

test_date = st.date_input(
    "Select ONE date to debug",
    value=datetime(2026, 6, 29),
    help="Test with single date first"
)

st.header("⚙️ Step 3: Extract & Debug")

if st.button("🔍 Extract & Show Full API Response", use_container_width=True):
    if not api_token:
        st.error("❌ Please enter your API token first")
    else:
        try:
            st.write("📡 Calling Dhan API...")
            
            url = "https://api.dhan.co/v2/charts/intraday"
            headers = {
                "Content-Type": "application/json",
                "access-token": api_token
            }
            
            payload = {
                "securityId": "13",
                "exchangeSegment": "IDX_I",
                "instrument": "INDEX",
                "interval": "15",
                "oi": False,
                "fromDate": "2026-06-29 09:15:00",  # ✅ WITH TIME!
                "toDate": "2026-06-29 15:30:00",    # ✅ WITH TIME!
            }
            
            st.write("📤 Request Payload:")
            st.json(payload)
            
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            
            st.write(f"✅ HTTP Status: {resp.status_code}")
            
            if resp.status_code != 200:
                st.error(f"❌ API Error: {resp.status_code}")
                st.error(f"Message: {resp.text}")
            else:
                data = resp.json()
                
                st.write("📥 FULL API Response:")
                st.json(data)
                
                st.write("---")
                st.write("🔍 ANALYSIS:")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if "timestamp" in data:
                        st.metric("Records in Response", len(data["timestamp"]))
                    else:
                        st.metric("Records", "N/A")
                
                with col2:
                    if "timestamp" in data and len(data["timestamp"]) > 0:
                        first_time = pd.Timestamp(data["timestamp"][0], unit="s")
                        st.metric("First Time", first_time.strftime("%H:%M"))
                    else:
                        st.metric("First Time", "N/A")
                
                with col3:
                    if "timestamp" in data and len(data["timestamp"]) > 0:
                        last_time = pd.Timestamp(data["timestamp"][-1], unit="s")
                        st.metric("Last Time", last_time.strftime("%H:%M"))
                    else:
                        st.metric("Last Time", "N/A")
                
                with col4:
                    st.metric("Response Keys", str(list(data.keys())))
                
                st.write("---")
                st.write("📄 PAGINATION INFO:")
                
                if "pageNumber" in data:
                    st.write(f"**pageNumber:** {data['pageNumber']}")
                else:
                    st.write("❌ **pageNumber:** NOT in response")
                
                if "pageSize" in data:
                    st.write(f"**pageSize:** {data['pageSize']}")
                else:
                    st.write("❌ **pageSize:** NOT in response")
                
                if "totalPages" in data:
                    st.write(f"**totalPages:** {data['totalPages']}")
                else:
                    st.write("❌ **totalPages:** NOT in response")
                
                if "totalRecords" in data:
                    st.write(f"**totalRecords:** {data['totalRecords']}")
                else:
                    st.write("❌ **totalRecords:** NOT in response")
                
                st.write("---")
                st.write("💡 INTERPRETATION:")
                
                if "timestamp" in data:
                    num_records = len(data["timestamp"])
                    
                    if num_records == 3:
                        st.warning("⚠️ Only 3 records = API default limit might be 3")
                        st.info("💡 Solution: Check if there's a 'limit' parameter we missed OR if totalPages > 1")
                    elif num_records > 20:
                        st.success("✅ Good! Got full day data (20+ candles)")
                    else:
                        st.warning(f"⚠️ Got {num_records} records - missing data")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

st.write("---")
st.write("📝 **DEBUG INSTRUCTIONS:**")
st.markdown("""
1. Run this and look at the **Full API Response** (JSON)
2. Check **ANALYSIS** section - how many records?
3. Check **PAGINATION INFO** - what fields exist?
4. If totalPages > 1, we need to fetch other pages
5. Take a SCREENSHOT of the full response
6. Share with me
""")
