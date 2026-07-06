import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Dhan Data Extractor", layout="wide")

st.title("📊 Dhan Data Extractor")
st.markdown("Extract Nifty 15-min OHLCV data from Dhan API")

# ═══════════════════════════════════════════════════════════════
# INPUT: API TOKEN
# ═══════════════════════════════════════════════════════════════

st.header("🔑 Step 1: Enter API Token")

api_token = st.text_input(
    "Paste your Dhan API token",
    type="password",
    help="Your API token from Dhan settings"
)

# ═══════════════════════════════════════════════════════════════
# INPUT: DATE RANGE
# ═══════════════════════════════════════════════════════════════

st.header("📅 Step 2: Select Date Range")

col1, col2 = st.columns(2)

with col1:
    from_date = st.date_input(
        "From Date",
        value=datetime(2026, 1, 1),
        help="Start date for data extraction"
    )

with col2:
    to_date = st.date_input(
        "To Date",
        value=datetime(2026, 4, 1),
        help="End date for data extraction"
    )

# ═══════════════════════════════════════════════════════════════
# EXTRACT DATA
# ═══════════════════════════════════════════════════════════════

st.header("⚙️ Step 3: Extract Data")

if st.button("🚀 Extract Nifty Data", use_container_width=True):
    if not api_token:
        st.error("❌ Please enter your API token first")
    else:
        # Show progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("🔄 Connecting to Dhan API...")
            progress_bar.progress(25)
            
            # Prepare request
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
                "fromDate": from_date.strftime("%Y-%m-%d"),
                "toDate": to_date.strftime("%Y-%m-%d")
            }
            
            status_text.text("📡 Fetching data from Dhan...")
            progress_bar.progress(50)
            
            # Make request
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if resp.status_code != 200:
                st.error(f"❌ API Error: {resp.status_code}")
                st.error(f"Message: {resp.text}")
            else:
                status_text.text("📊 Processing data...")
                progress_bar.progress(75)
                
                # Parse response
                data = resp.json()
                
                # Create DataFrame
                df = pd.DataFrame({
                    "datetime": pd.to_datetime(data["timestamp"], unit="s"),
                    "open": data["open"],
                    "high": data["high"],
                    "low": data["low"],
                    "close": data["close"],
                    "volume": data["volume"]
                }).set_index("datetime")
                
                # Add candle color
                df["candle_color"] = "DOJI"
                df.loc[df["close"] > df["open"], "candle_color"] = "GREEN"
                df.loc[df["close"] < df["open"], "candle_color"] = "RED"
                
                # Save to CSV
                from_str = from_date.strftime("%Y-%m-%d").replace("-", "")
                to_str = to_date.strftime("%Y-%m-%d").replace("-", "")
                csv_name = f"nifty_15min_{from_date.strftime('%Y-%m-%d')}_to_{to_date.strftime('%Y-%m-%d')}.csv"
                
                df.to_csv(csv_name)
                
                status_text.text("✅ Data extracted successfully!")
                progress_bar.progress(100)
                
                # Show results
                st.success(f"✅ Saved: {csv_name}")
                st.write(f"**Candles extracted:** {len(df)}")
                st.write(f"**Date range:** {df.index[0]} to {df.index[-1]}")
                
                # Preview
                with st.expander("📋 Data Preview"):
                    st.dataframe(df.head(10), use_container_width=True)
                
                st.info("👉 Now go to **Backtester** tab to analyze this data!")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            progress_bar.progress(0)
            status_text.text("Error occurred")

# ═══════════════════════════════════════════════════════════════
# INFO
# ═══════════════════════════════════════════════════════════════

st.header("ℹ️ How to get API Token")

st.markdown("""
1. Go to [Dhan.co](https://dhan.co)
2. Login to your account
3. Settings → API Management
4. Generate new token (or copy existing)
5. Paste token above
6. Select date range
7. Click "Extract Nifty Data"
8. CSV file created in your repo
9. Go to Backtester to analyze!
""")