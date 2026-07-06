import streamlit as st
import requests
import pandas as pd
from datetime import datetime


st.set_page_config(page_title="Dhan Data Extractor - ETF", layout="wide")

st.title("📊 Dhan Data Extractor - NIFTYBEES ETF")

st.header("🔑 Step 1: Enter API Token")

api_token = st.text_input("Paste your Dhan API token", type="password")

st.header("📅 Step 2: Select Mode")

mode = st.radio("Choose data mode", ["📍 Today (Real-time)", "📆 Date Range (Historical)"], horizontal=True)

if mode == "📍 Today (Real-time)":
    today = datetime.now().date()
    current_time = datetime.now().strftime("%H:%M:%S")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"📅 Date: {today}")
    with col2:
        st.write(f"⏰ Current time: {current_time}")
    
    from_date = today
    to_date = today
    
else:
    col1, col2 = st.columns(2)
    with col1:
        from_date = st.date_input("From Date", value=datetime(2026, 6, 29))
    with col2:
        to_date = st.date_input("To Date", value=datetime(2026, 6, 29))

st.header("⚙️ Step 3: Extract Data")

if st.button("🚀 Extract NIFTYBEES Data", use_container_width=True):
    if not api_token:
        st.error("❌ Please enter your API token first")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("🔄 Connecting to Dhan API...")
            progress_bar.progress(25)
            
            url = "https://api.dhan.co/v2/charts/intraday"
            headers = {
                "Content-Type": "application/json",
                "access-token": api_token
            }
            
            # ✅ CORRECT PAYLOAD FORMAT
            payload = {
                "securityId": "590103",
                "exchangeSegment": "BSE_EQ",
                "instrument": "EQUITY",
                "interval": "15",
                "oi": "false",
                "fromDate": from_date.strftime('%Y-%m-%d'),
                "toDate": to_date.strftime('%Y-%m-%d')
            }
            
            st.write(f"**Request: {payload['fromDate']} to {payload['toDate']}**")
            
            status_text.text("📡 Fetching data from Dhan...")
            progress_bar.progress(50)
            
            resp = requests.post(url, headers=headers, json=payload, timeout=30)

            if resp.status_code != 200:
                st.error(f"❌ API Error: {resp.status_code}")
                st.error(f"Message: {resp.text}")
                st.write("**Payload:**")
                st.json(payload)
            else:
                status_text.text("📊 Processing data...")
                progress_bar.progress(70)
                
                data = resp.json()
                
                df = pd.DataFrame({
                    "datetime": pd.to_datetime(data["timestamp"], unit="s", utc=True).tz_convert('Asia/Kolkata'),
                    "open": data["open"],
                    "high": data["high"],
                    "low": data["low"],
                    "close": data["close"],
                    "volume": data["volume"]
                }).set_index("datetime")
                
                status_text.text("🕐 Filtering to market hours...")
                progress_bar.progress(80)
                
                market_start = df.index.time >= pd.Timestamp("09:15:00").time()
                market_end = df.index.time <= pd.Timestamp("15:30:00").time()
                df_filtered = df[market_start & market_end]
                
                df_filtered = df_filtered[df_filtered['volume'] > 0]
                
                df_filtered["candle_color"] = "DOJI"
                df_filtered.loc[df_filtered["close"] > df_filtered["open"], "candle_color"] = "GREEN"
                df_filtered.loc[df_filtered["close"] < df_filtered["open"], "candle_color"] = "RED"
                
                status_text.text("💾 Saving to CSV...")
                progress_bar.progress(90)
                
                csv_name = f"niftybees_15min_{from_date.strftime('%Y-%m-%d')}_to_{to_date.strftime('%Y-%m-%d')}.csv"
                df_filtered.to_csv(csv_name)
                
                status_text.text("✅ Success!")
                progress_bar.progress(100)
                
                st.success(f"✅ Saved: {csv_name}")
                st.write(f"**Total candles:** {len(df_filtered)}")
                
                if len(df_filtered) > 0:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Green", len(df_filtered[df_filtered['candle_color'] == 'GREEN']))
                    with col2:
                        st.metric("Red", len(df_filtered[df_filtered['candle_color'] == 'RED']))
                    with col3:
                        st.metric("Price Range", f"₹{df_filtered['low'].min():.2f} - ₹{df_filtered['high'].max():.2f}")
                    with col4:
                        st.metric("Volume", f"{df_filtered['volume'].sum()/1e6:.1f}M")
                    
                    with st.expander("📋 Data Preview"):
                        st.dataframe(df_filtered.head(20), use_container_width=True)
                    
                    st.download_button(
                        label="📥 Download CSV",
                        data=df_filtered.to_csv(),
                        file_name=csv_name,
                        mime="text/csv",
                        use_container_width=True
                    )
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

