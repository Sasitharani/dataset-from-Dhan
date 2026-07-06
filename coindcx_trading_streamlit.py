import streamlit as st
import time
from coindcx import Client
from datetime import datetime, timedelta
import pandas as pd
import pytz

# Page config
st.set_page_config(
    page_title="CoinDCX LIC-LOC Trading Bot",
    page_icon="🤖",
    layout="wide"
)

# ⭐ INITIALIZE ALL SESSION STATE
if 'running' not in st.session_state:
    st.session_state.running = False
if 'signals' not in st.session_state:
    st.session_state.signals = []
if 'stats' not in st.session_state:
    st.session_state.stats = {
        'total_trades': 0,
        'wins': 0,
        'losses': 0,
        'total_pnl': 0.0
    }

# Function to convert to IST
def convert_to_ist(timestamp_ms):
    """Convert millisecond timestamp to IST format"""
    try:
        if timestamp_ms > 10000000000:
            timestamp_s = timestamp_ms / 1000
        else:
            timestamp_s = timestamp_ms
        
        utc_dt = datetime.utcfromtimestamp(timestamp_s)
        ist = pytz.timezone('Asia/Kolkata')
        ist_dt = utc_dt.replace(tzinfo=pytz.UTC).astimezone(ist)
        return ist_dt.strftime('%d-%m-%Y %H:%M:%S')
    except Exception as e:
        return str(timestamp_ms)

st.title("🤖 CoinDCX LIC-LOC Trading Bot")
st.markdown("---")

# Sidebar - API Credentials
st.sidebar.header("🔐 CoinDCX API Credentials")
api_key = st.sidebar.text_input(
    "API Key",
    type="password",
    placeholder="Paste your CoinDCX API Key"
)

api_secret = st.sidebar.text_input(
    "API Secret",
    type="password",
    placeholder="Paste your CoinDCX API Secret"
)

st.sidebar.markdown("---")

# Test Connection
if st.sidebar.button("🔗 Test Connection", key="test_conn"):
    if not api_key or not api_secret:
        st.sidebar.error("❌ Please enter API Key and Secret!")
    else:
        try:
            with st.spinner("Testing connection..."):
                client = Client(
                    api_key=api_key,
                    api_secret=api_secret
                )
                markets = client.get_markets()
                balance = client.get_balances()
                
            st.sidebar.success(f"✅ Connected! {len(markets)} markets available")
            st.sidebar.info(f"📊 Balance: {balance}")
        except Exception as e:
            st.sidebar.error(f"❌ Connection failed: {str(e)}")

st.sidebar.markdown("---")

# Bot Settings
st.sidebar.header("⚙️ Bot Settings")

available_pairs = {
    "BTC/INR": "KC-BTC_INR",
    "ETH/INR": "KC-ETH_INR",
    "BTC/USDT": "KC-BTC_USDT",
    "ETH/USDT": "KC-ETH_USDT",
    "LTC/INR": "KC-LTC_INR",
    "XRP/INR": "KC-XRP_INR"
}

pair_display = st.sidebar.selectbox(
    "Trading Pair",
    list(available_pairs.keys())
)

pair = available_pairs[pair_display]

interval = st.sidebar.selectbox(
    "Candle Interval",
    ["1m", "5m", "15m", "1h", "4h"]
)

lic_threshold = st.sidebar.number_input(
    "LIC Threshold (Body Size in ₹)",
    value=300,
    step=50
)

st.sidebar.markdown("---")

# ✅ DATE RANGE FILTER
st.sidebar.header("📅 Date Range Filter")

today = datetime.now().date()
default_start = today - timedelta(days=7)  # Last 7 days

start_date = st.sidebar.date_input(
    "Start Date",
    value=default_start,
    max_value=today
)

end_date = st.sidebar.date_input(
    "End Date",
    value=today,
    min_value=start_date,
    max_value=today
)

date_range_display = f"📍 Selected: **{start_date}** to **{end_date}**"
st.sidebar.info(date_range_display)

st.sidebar.markdown("---")

# Main Controls
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("▶️ START LIVE BOT", key="start_bot", use_container_width=True):
        if not api_key or not api_secret:
            st.error("❌ Please enter API credentials first!")
        else:
            st.session_state.running = True
            st.success("✅ Bot started!")

with col2:
    if st.button("⏹️ STOP BOT", key="stop_bot", use_container_width=True):
        st.session_state.running = False
        st.info("⏸️ Bot stopped")

with col3:
    if st.button("🔄 RESET", key="reset_stats", use_container_width=True):
        st.session_state.signals = []
        st.session_state.stats = {
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'total_pnl': 0.0
        }
        st.success("✅ Stats reset!")

st.markdown("---")

# Display Status - LIVE BOT STATS (only for running bot)
if st.session_state.running:
    st.subheader("🟢 Live Bot Status")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Bot Status", "🟢 RUNNING")

    with col2:
        st.metric("Total Trades", st.session_state.stats['total_trades'])

    with col3:
        wins = st.session_state.stats['wins']
        total = st.session_state.stats['total_trades']
        win_rate = (wins / total * 100) if total > 0 else 0
        st.metric("Win Rate", f"{win_rate:.1f}%")

    with col4:
        st.metric("Total P&L", f"₹{st.session_state.stats['total_pnl']:.2f}")
    
    st.markdown("---")

st.markdown("---")

# HISTORICAL ANALYSIS - DATE RANGE
st.header("📊 Historical Analysis - Date Range")
st.write(f"Pair: **{pair_display}** | Interval: **{interval}** | LIC Threshold: **₹{lic_threshold}**")
st.write(date_range_display)

if st.button("🔍 Analyze Date Range", key="analyze_range", use_container_width=True):
    if not api_key or not api_secret:
        st.error("❌ API credentials missing!")
    else:
        try:
            client = Client(
                api_key=api_key,
                api_secret=api_secret
            )
            
            with st.spinner(f"Fetching data for {pair_display} from {start_date} to {end_date}..."):
                candles = client.get_candles(
                    pair=pair,
                    interval=interval,
                    limit=500  # Increased limit for date range filtering
                )
            
            if candles and len(candles) > 0:
                # ✅ FILTER BY DATE RANGE
                ist = pytz.timezone('Asia/Kolkata')
                filtered_candles = []
                
                for candle in candles:
                    candle_time_ms = candle['time']
                    if candle_time_ms > 10000000000:
                        candle_time_s = candle_time_ms / 1000
                    else:
                        candle_time_s = candle_time_ms
                    
                    utc_dt = datetime.utcfromtimestamp(candle_time_s)
                    ist_dt = utc_dt.replace(tzinfo=pytz.UTC).astimezone(ist)
                    candle_date = ist_dt.date()
                    
                    # Include if within date range
                    if start_date <= candle_date <= end_date:
                        filtered_candles.append(candle)
                
                if not filtered_candles:
                    st.warning(f"⏳ No data available for {start_date} to {end_date}")
                else:
                    candles_data = []
                    date_stats = {
                        'total_trades': 0,
                        'wins': 0,
                        'losses': 0,
                        'total_pnl': 0.0
                    }
                    
                    for idx, candle in enumerate(filtered_candles):
                        # C1 calculations
                        c1_body = abs(candle['close'] - candle['open'])
                        
                        # Skip doji candles (body = 0)
                        if c1_body == 0:
                            continue
                        
                        c1_open = candle['open']
                        c1_close = candle['close']
                        c1_color = "🔴 RED" if c1_close < c1_open else "🟢 GREEN"
                        c1_high = candle['high']
                        c1_low = candle['low']
                        
                        lic_detected = "✅ YES" if c1_body >= lic_threshold else "❌ NO"
                        time_ist = convert_to_ist(candle['time'])
                        
                        # Initialize trade variables
                        trade_signal = "❌ NO"
                        entry_price = "-"
                        exit_price = "-"
                        quantity = "-"
                        profit_loss = "-"
                        trend_check = "-"
                        
                        # ✅ C2 = NEXT candle in FORWARD time = candles[idx - 1] (NEWER)
                        if idx - 1 >= 0:  # C2 exists (newer)
                            next_candle = filtered_candles[idx - 1]
                            c2_open = next_candle['open']  # ✅ Entry at C2 open
                            c2_body = abs(next_candle['close'] - next_candle['open'])
                            c2_color = "🔴 RED" if next_candle['close'] < next_candle['open'] else "🟢 GREEN"
                            
                            is_retracement = "✅ YES" if c1_color != c2_color else "❌ NO"
                            
                            if c1_color != c2_color:
                                c2_body_display = f"₹{c2_body:.2f} 🔵"
                            else:
                                c2_body_display = f"₹{c2_body:.2f}"
                            
                            # ✅ TREND CONFIRMATION: Need 3 SAME COLOR (2 older + C1 LIC)
                            if c1_body >= lic_threshold:  # LIC detected
                                if idx + 2 < len(filtered_candles):  # Need 2 older candles
                                    # Get 2 previous candles (OLDER in time = higher indices)
                                    older_candle1 = filtered_candles[idx + 1]  # 1 older
                                    older_candle2 = filtered_candles[idx + 2]  # 2 older
                                    
                                    older_color1 = "🔴 RED" if older_candle1['close'] < older_candle1['open'] else "🟢 GREEN"
                                    older_color2 = "🔴 RED" if older_candle2['close'] < older_candle2['open'] else "🟢 GREEN"
                                    
                                    # ✅ Check if all 3 are same color
                                    all_colors = [older_color2, older_color1, c1_color]
                                    
                                    if c1_color == "🟢 GREEN":  # GREEN LIC → SHORT
                                        # All 3 must be GREEN
                                        if all(color == "🟢 GREEN" for color in all_colors):
                                            trend_check = "✅ VALID (3 GREEN)"
                                            # ✅ Exit = Entry - (Body/2)
                                            exit_level = c2_open - (c1_body / 2)
                                            entry_price = f"₹{c2_open:.2f}"
                                            exit_price = f"₹{exit_level:.2f}"
                                            profit_val = c2_open - exit_level
                                            quantity = "1"
                                            
                                            profit_loss = f"+₹{profit_val:.2f}" if profit_val > 0 else f"-₹{abs(profit_val):.2f}"
                                            trade_signal = "✅ SHORT"
                                            
                                            date_stats['total_trades'] += 1
                                            if profit_val > 0:
                                                date_stats['wins'] += 1
                                            else:
                                                date_stats['losses'] += 1
                                            date_stats['total_pnl'] += profit_val
                                        else:
                                            trend_check = f"❌ INVALID ({older_color2}→{older_color1}→{c1_color})"
                                    
                                    elif c1_color == "🔴 RED":  # RED LIC → LONG
                                        # All 3 must be RED
                                        if all(color == "🔴 RED" for color in all_colors):
                                            trend_check = "✅ VALID (3 RED)"
                                            # ✅ Exit = Entry + (Body/2)
                                            exit_level = c2_open + (c1_body / 2)
                                            entry_price = f"₹{c2_open:.2f}"
                                            exit_price = f"₹{exit_level:.2f}"
                                            profit_val = exit_level - c2_open
                                            quantity = "1"
                                            
                                            profit_loss = f"+₹{profit_val:.2f}" if profit_val > 0 else f"-₹{abs(profit_val):.2f}"
                                            trade_signal = "✅ LONG"
                                            
                                            date_stats['total_trades'] += 1
                                            if profit_val > 0:
                                                date_stats['wins'] += 1
                                            else:
                                                date_stats['losses'] += 1
                                            date_stats['total_pnl'] += profit_val
                                        else:
                                            trend_check = f"❌ INVALID ({older_color2}→{older_color1}→{c1_color})"
                                else:
                                    trend_check = "⏳ Not enough history"
                        else:
                            c2_body_display = "-"
                            c2_color = "-"
                            is_retracement = "-"
                        
                        candles_data.append({
                            'Time (IST)': time_ist,
                            'Open': f"₹{c1_open:.2f}",
                            'Close': f"₹{c1_close:.2f}",
                            'C1 Body': f"₹{c1_body:.2f}",
                            'C1 Color': c1_color,
                            'C2 Body': c2_body_display,
                            'C2 Color': c2_color,
                            'LIC': lic_detected,
                            'Trend': trend_check,
                            'Trade': trade_signal,
                            'Entry': entry_price,
                            'Exit': exit_price,
                            'Qty': quantity,
                            'Profit/Loss': profit_loss
                        })
                    
                    df_data = pd.DataFrame(candles_data)
                    
                    # ✅ DISPLAY STATISTICS FOR THIS DATE RANGE
                    st.subheader("📈 Trading Statistics (Date Range)")
                    
                    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                    
                    with stat_col1:
                        st.metric("Total Trades", date_stats['total_trades'])
                    
                    with stat_col2:
                        st.metric("Winners ✅", date_stats['wins'])
                    
                    with stat_col3:
                        total = date_stats['total_trades']
                        wins = date_stats['wins']
                        win_rate = (wins / total * 100) if total > 0 else 0
                        st.metric("Win Rate", f"{win_rate:.1f}%")
                    
                    with stat_col4:
                        st.metric("Total P&L", f"₹{date_stats['total_pnl']:.2f}")
                    
                    st.markdown("---")
                    
                    # Display table
                    st.subheader("📊 Detailed Trade Analysis")
                    st.info("**Entry = C2 Open | SHORT Exit = Entry - (Body/2) | LONG Exit = Entry + (Body/2)**")
                    st.dataframe(df_data, use_container_width=True, hide_index=True)
                    
                    st.markdown("---")
                    
                    # Download as CSV
                    csv = df_data.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name=f"{pair_display.replace('/', '_')}_{start_date}_{end_date}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

st.markdown("---")

# LIVE TRADING
if st.session_state.running:
    st.header("📊 Live Trading Signals")
    st.write(f"Pair: **{pair_display}** | Interval: **{interval}** | LIC Threshold: **₹{lic_threshold}**")
    st.write("**Strategy:** Entry = C2 Open | SHORT Exit = Entry - (Body/2) | LONG Exit = Entry + (Body/2)")
    
    if not api_key or not api_secret:
        st.error("❌ API credentials missing!")
    else:
        try:
            client = Client(
                api_key=api_key,
                api_secret=api_secret
            )
            
            balance = client.get_balances()
            st.sidebar.info(f"💰 Current Balance: {balance}")
            
            with st.spinner(f"Fetching {pair_display} candles..."):
                candles = client.get_candles(
                    pair=pair,
                    interval=interval,
                    limit=100
                )
            
            if len(candles) >= 4:  # Need C1 + 2 older + C2 newer
                c1 = candles[0]  # Most recent
                
                # C1 data
                c1_time_ist = convert_to_ist(c1['time'])
                c1_open = c1['open']
                c1_close = c1['close']
                c1_high = c1['high']
                c1_low = c1['low']
                c1_body = abs(c1_close - c1_open)
                
                # Skip if doji (body = 0)
                if c1_body == 0:
                    st.warning("⏳ Current candle is doji (no body). Waiting for next candle...")
                else:
                    c1_color = "🔴 RED" if c1_close < c1_open else "🟢 GREEN"
                    
                    lic_detected = "✅ YES" if c1_body >= lic_threshold else "❌ NO"
                    
                    # Display current candle with OPEN & CLOSE
                    st.subheader("📈 Current Candle Analysis")
                    
                    table_data = {
                        'Time (IST)': [c1_time_ist],
                        'Open': [f"₹{c1_open:.2f}"],
                        'Close': [f"₹{c1_close:.2f}"],
                        'C1 Body': [f"₹{c1_body:.2f}"],
                        'C1 Color': [c1_color],
                        'LIC': [lic_detected]
                    }
                    
                    df_table = pd.DataFrame(table_data)
                    st.dataframe(df_table, use_container_width=True, hide_index=True)
                    
                    st.markdown("---")
                    
                    # Trading Analysis with 3-candle trend confirmation
                    st.subheader("🎯 Trading Analysis (3 Same Color)")
                    st.write(f"**C1 Body: ₹{c1_body:.2f}** | **LIC Threshold: ₹{lic_threshold}** | **LIC Status: {lic_detected}**")
                    st.write(f"**C1 Open: ₹{c1_open:.2f}** | **C1 Close: ₹{c1_close:.2f}**")
                    
                    if c1_body >= lic_threshold:
                        # Get 2 older candles
                        older_candle1 = candles[1]  # 1 older
                        older_candle2 = candles[2]  # 2 older
                        
                        older_color1 = "🔴 RED" if older_candle1['close'] < older_candle1['open'] else "🟢 GREEN"
                        older_color2 = "🔴 RED" if older_candle2['close'] < older_candle2['open'] else "🟢 GREEN"
                        
                        st.success(f"✅ **LIC DETECTED!** Body: ₹{c1_body:.2f}")
                        st.write(f"**3-Candle Pattern:** {older_color2} → {older_color1} → {c1_color}")
                        st.write(f"**Older Candle 2:** {older_color2} (open: ₹{older_candle2['open']:.2f}, close: ₹{older_candle2['close']:.2f})")
                        st.write(f"**Older Candle 1:** {older_color1} (open: ₹{older_candle1['open']:.2f}, close: ₹{older_candle1['close']:.2f})")
                        
                        if c1_color == "🟢 GREEN":  # SHORT Setup
                            if older_color1 == "🟢 GREEN" and older_color2 == "🟢 GREEN":
                                st.success("✅ **TREND VALID - All 3 GREEN!**")
                                
                                exit_target = c1_body / 2
                                st.info(f"""
                                🟢 **GREEN LIC - SHORT SETUP DETECTED**
                                - **Entry Price (will be at C2 Opening):** Waiting for next candle
                                - **Exit Target:** Entry - ₹{exit_target:.2f}
                                - **Max Profit:** ₹{exit_target:.2f}
                                - **Setup is READY for trade**
                                """)
                            else:
                                st.error(f"❌ **TREND INVALID** - Need all 3 GREEN: {older_color2}→{older_color1}→{c1_color}")
                        
                        elif c1_color == "🔴 RED":  # LONG Setup
                            if older_color1 == "🔴 RED" and older_color2 == "🔴 RED":
                                st.success("✅ **TREND VALID - All 3 RED!**")
                                
                                exit_target = c1_body / 2
                                st.info(f"""
                                🔴 **RED LIC - LONG SETUP DETECTED**
                                - **Entry Price (will be at C2 Opening):** Waiting for next candle
                                - **Exit Target:** Entry + ₹{exit_target:.2f}
                                - **Max Profit:** ₹{exit_target:.2f}
                                - **Setup is READY for trade**
                                """)
                            else:
                                st.error(f"❌ **TREND INVALID** - Need all 3 RED: {older_color2}→{older_color1}→{c1_color}")
                    
                    else:
                        st.info(f"⏳ Waiting for LIC... Current Body: ₹{c1_body:.2f} (need ₹{lic_threshold})")
                    
                    st.markdown("---")
                    
                    st.info("🔄 Refreshing in 30 seconds...")
                    time.sleep(30)
                    st.rerun()
            
            else:
                st.warning("⏳ Need at least 4 candles. Please wait...")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

else:
    if not st.session_state.running:
        st.info("👉 Click '▶️ START LIVE BOT' or select a date range and click '🔍 Analyze Date Range' to view data")

st.markdown("---")
st.markdown("""
### 🎯 TRADING STRATEGY:

**GREEN LIC SETUP (SHORT):**
- 3 GREEN candles (2 older + 1 LIC)
- **Entry:** C2 Open | **Exit:** Entry - (Body/2) | **Profit = Body/2** ✅

**RED LIC SETUP (LONG):**
- 3 RED candles (2 older + 1 LIC)
- **Entry:** C2 Open | **Exit:** Entry + (Body/2) | **Profit = Body/2** ✅

### 📊 Features:
✅ Live trading signals (with persistent stats)
✅ Historical analysis with date range
✅ CSV export with all trade details
✅ Real-time P&L tracking

### ⚠️ Disclaimer:
For **backtesting & research only**. Not real trading advice!
""")
