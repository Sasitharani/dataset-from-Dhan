import streamlit as st
import time
from coindcx import Client
from datetime import datetime, timedelta
import pandas as pd
import pytz
import requests
import subprocess
import os
import psutil

# Page config
st.set_page_config(
    page_title="CoinDCX LIC-LOC Trading Bot",
    page_icon="🤖",
    layout="wide"
)

# ✅ HARDCODED ALL CREDENTIALS
TELEGRAM_BOT_TOKEN = "8680315519:AAE4q_UA-CmXJGFlD4loge15zZgmceGzSQA"
TELEGRAM_CHAT_ID = "6312479033"
ENABLE_ALERTS = True

# ✅ ADD YOUR COINDCX CREDENTIALS HERE
COINDCX_API_KEY = "a75a34d3a4dd5c8a53922c2564d90fa1466f62301c51efb8"
COINDCX_API_SECRET = "acdb5ecc637e0b1af09f189137b7a3543f1e28e1ea4890c8fb4958ac4177e25c"

# Use hardcoded credentials
api_key = "a75a34d3a4dd5c8a53922c2564d90fa1466f62301c51efb8"
api_secret = "acdb5ecc637e0b1af09f189137b7a3543f1e28e1ea4890c8fb4958ac4177e25c"

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
if 'bot_24_7_running' not in st.session_state:
    st.session_state.bot_24_7_running = False

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

# ✅ TELEGRAM ALERT FUNCTION
def send_telegram_alert(message):
    """Send alert message via Telegram"""
    if not ENABLE_ALERTS:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=data, timeout=5)
        return response.status_code == 200
    except Exception as e:
        return False

# ✅ CHECK IF 24/7 BOT IS RUNNING
def is_bot_running():
    """Check if 24/7 bot process is running"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'coindcx_24_7_bot.py' in ' '.join(proc.info['cmdline']):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False
    except:
        return False

# ✅ START 24/7 BOT
def start_24_7_bot(pair, interval, threshold, check_interval):
    """Start the 24/7 bot in background"""
    try:
        # Create dynamic 24/7 bot script
        bot_script = f"""
import requests
import time
from coindcx import Client
from datetime import datetime
import pytz

COINDCX_API_KEY = "{api_key}"
COINDCX_API_SECRET = "{api_secret}"
TELEGRAM_BOT_TOKEN = "{TELEGRAM_BOT_TOKEN}"
TELEGRAM_CHAT_ID = "{TELEGRAM_CHAT_ID}"
TRADING_PAIR = "{pair}"
INTERVAL = "{interval}"
LIC_THRESHOLD = {threshold}
CHECK_INTERVAL = {check_interval}

processed_candle_times = set()

def send_telegram_alert(message):
    try:
        url = f"https://api.telegram.org/bot{{TELEGRAM_BOT_TOKEN}}/sendMessage"
        data = {{"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}}
        requests.post(url, data=data, timeout=5)
    except:
        pass

def convert_to_ist(timestamp_ms):
    try:
        if timestamp_ms > 10000000000:
            timestamp_s = timestamp_ms / 1000
        else:
            timestamp_s = timestamp_ms
        from datetime import datetime
        utc_dt = datetime.utcfromtimestamp(timestamp_s)
        ist = pytz.timezone('Asia/Kolkata')
        ist_dt = utc_dt.replace(tzinfo=pytz.UTC).astimezone(ist)
        return ist_dt.strftime('%d-%m-%Y %H:%M:%S')
    except:
        return str(timestamp_ms)

def check_signals():
    try:
        client = Client(api_key=COINDCX_API_KEY, api_secret=COINDCX_API_SECRET)
        candles = client.get_candles(pair=TRADING_PAIR, interval=INTERVAL, limit=10)
        
        if not candles or len(candles) < 4:
            return
        
        idx = 0
        candle = candles[idx]
        c1_body = abs(candle['close'] - candle['open'])
        
        if c1_body == 0 or candle['time'] in processed_candle_times:
            return
        
        c1_open, c1_close = candle['open'], candle['close']
        c1_color = "🔴 RED" if c1_close < c1_open else "🟢 GREEN"
        time_ist = convert_to_ist(candle['time'])
        
        if c1_body >= LIC_THRESHOLD and idx + 2 < len(candles):
            older_candle1 = candles[idx + 1]
            older_candle2 = candles[idx + 2]
            older_color1 = "🔴 RED" if older_candle1['close'] < older_candle1['open'] else "🟢 GREEN"
            older_color2 = "🔴 RED" if older_candle2['close'] < older_candle2['open'] else "🟢 GREEN"
            
            if idx - 1 >= 0:
                next_candle = candles[idx - 1]
                c2_open, c2_close = next_candle['open'], next_candle['close']
                
                if c1_color == "🟢 GREEN" and older_color1 == "🟢 GREEN" and older_color2 == "🟢 GREEN":
                    profit_val = c2_open - c2_close
                    send_telegram_alert(f"🟢 <b>SHORT SIGNAL!</b>\\n📊 {{TRADING_PAIR}} | {{INTERVAL}}\\n⏰ {{time_ist}}\\n💰 Entry: ₹{{c2_open:.2f}}\\n📉 Exit: ₹{{c2_close:.2f}}\\n📈 P&L: +₹{{profit_val:.2f}}\\n🎯 Body: ₹{{c1_body:.2f}}")
                    processed_candle_times.add(candle['time'])
                
                elif c1_color == "🔴 RED" and older_color1 == "🔴 RED" and older_color2 == "🔴 RED":
                    profit_val = c2_close - c2_open
                    send_telegram_alert(f"🔴 <b>LONG SIGNAL!</b>\\n📊 {{TRADING_PAIR}} | {{INTERVAL}}\\n⏰ {{time_ist}}\\n💰 Entry: ₹{{c2_open:.2f}}\\n📈 Exit: ₹{{c2_close:.2f}}\\n📈 P&L: +₹{{profit_val:.2f}}\\n🎯 Body: ₹{{c1_body:.2f}}")
                    processed_candle_times.add(candle['time'])
    except:
        pass

send_telegram_alert(f"🟢 <b>24/7 BOT STARTED!</b>\\n📊 {{TRADING_PAIR}} | {{INTERVAL}}\\n⏰ {{datetime.now().strftime('%d-%m-%Y %H:%M:%S IST')}}")

while True:
    try:
        check_signals()
        time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        break
    except:
        time.sleep(5)
"""
        
        # Write script
        script_path = "/workspaces/dataset-from-Dhan/temp_24_7_bot.py"
        with open(script_path, 'w') as f:
            f.write(bot_script)
        
        # Start process
        subprocess.Popen(
            ['python', script_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        return True
    except Exception as e:
        st.error(f"❌ Error starting bot: {str(e)}")
        return False

# ✅ STOP 24/7 BOT
def stop_24_7_bot():
    """Stop the 24/7 bot"""
    try:
        os.system("pkill -f temp_24_7_bot.py")
        os.system("pkill -f coindcx_24_7_bot.py")
        return True
    except:
        return False

st.title("🤖 CoinDCX LIC-LOC Trading Bot (FULLY HARDCODED)")
st.markdown("---")

# ✅ API CREDENTIALS STATUS
st.sidebar.header("🔐 CoinDCX API Credentials")

if api_key != "YOUR_API_KEY_HERE" and api_secret != "YOUR_API_SECRET_HERE":
    st.sidebar.success("✅ API Credentials Loaded (Hardcoded)")
    st.sidebar.info(f"Key: {api_key[:10]}...***\nSecret: {api_secret[:10]}...***")
else:
    st.sidebar.error("❌ API Credentials NOT Set!\nEdit the code and add your credentials!")

st.sidebar.markdown("---")

# ✅ TELEGRAM STATUS
st.sidebar.header("🔔 TELEGRAM ALERTS")
if ENABLE_ALERTS:
    st.sidebar.success("✅ ALERTS ENABLED & HARDCODED\n🤖 All signals go to Telegram!")
    
    if st.sidebar.button("📢 Test Alert Now"):
        with st.spinner("Sending test message..."):
            success = send_telegram_alert(
                "🟢 <b>TEST ALERT - BOT WORKING!</b>\n⏰ " + datetime.now().strftime('%d-%m-%Y %H:%M:%S IST')
            )
            if success:
                st.sidebar.success("✅ Test alert sent to Telegram!")
            else:
                st.sidebar.error("❌ Failed to send alert")

st.sidebar.markdown("---")

# Test Connection
if st.sidebar.button("🔗 Test CoinDCX Connection", key="test_conn"):
    if api_key == "YOUR_API_KEY_HERE":
        st.sidebar.error("❌ Update API Key in code first!")
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

check_interval = st.sidebar.number_input(
    "Check Interval (seconds)",
    value=60,
    step=10,
    help="How often to check for signals"
)

st.sidebar.markdown("---")

# ✅ 24/7 BOT CONTROLS
st.sidebar.header("🤖 24/7 BOT MODE")

bot_status = is_bot_running()

if bot_status:
    st.sidebar.success("🟢 24/7 BOT RUNNING")
else:
    st.sidebar.info("🔴 24/7 BOT STOPPED")

col1, col2 = st.sidebar.columns(2)

with col1:
    if st.button("▶️ START 24/7 BOT", use_container_width=True):
        if api_key == "YOUR_API_KEY_HERE":
            st.sidebar.error("❌ Add API credentials first!")
        else:
            with st.spinner("Starting 24/7 bot..."):
                if start_24_7_bot(pair, interval, lic_threshold, check_interval):
                    st.sidebar.success("✅ 24/7 bot started!")
                    send_telegram_alert(
                        f"🟢 <b>24/7 BOT STARTED!</b>\n📊 {pair_display}\n⏱️ {interval}\n⏰ {datetime.now().strftime('%d-%m-%Y %H:%M:%S IST')}"
                    )
                    time.sleep(2)
                    st.rerun()
                else:
                    st.sidebar.error("❌ Failed to start bot")

with col2:
    if st.button("⏹️ STOP 24/7 BOT", use_container_width=True):
        if stop_24_7_bot():
            st.sidebar.success("✅ 24/7 bot stopped!")
            send_telegram_alert(
                f"🔴 <b>24/7 BOT STOPPED</b>\n⏰ {datetime.now().strftime('%d-%m-%Y %H:%M:%S IST')}"
            )
            time.sleep(2)
            st.rerun()
        else:
            st.sidebar.error("❌ Failed to stop bot")

st.sidebar.markdown("---")

# ✅ DATE RANGE FILTER
st.sidebar.header("📅 Date Range Filter (BACKTEST)")

today = datetime.now().date()
default_start = today - timedelta(days=7)

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
        if api_key == "YOUR_API_KEY_HERE":
            st.error("❌ Add API credentials first!")
        else:
            st.session_state.running = True
            st.success("✅ Bot started!")
            send_telegram_alert(
                f"🟢 <b>LIVE BOT STARTED</b>\n📊 {pair_display}\n⏱️ {interval}\n⏰ {datetime.now().strftime('%d-%m-%Y %H:%M:%S IST')}"
            )

with col2:
    if st.button("⏹️ STOP BOT", key="stop_bot", use_container_width=True):
        st.session_state.running = False
        st.info("⏸️ Bot stopped")
        send_telegram_alert(
            f"🔴 <b>LIVE BOT STOPPED</b>\n⏰ {datetime.now().strftime('%d-%m-%Y %H:%M:%S IST')}"
        )

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

# Display Status
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

# ✅ 24/7 BOT STATUS DISPLAY
st.header("🤖 24/7 BOT STATUS")

bot_is_running = is_bot_running()

col1, col2, col3 = st.columns(3)

with col1:
    if bot_is_running:
        st.success("🟢 24/7 BOT RUNNING")
    else:
        st.error("🔴 24/7 BOT STOPPED")

with col2:
    st.info(f"📊 Pair: {pair_display}")

with col3:
    st.info(f"⏱️ Interval: {interval}")

if bot_is_running:
    st.success(f"""
    ✅ **24/7 Bot is ACTIVE**
    
    🔍 Checking every {check_interval} seconds
    📊 Trading: {pair_display}
    ⏱️ Timeframe: {interval}
    🎯 LIC Threshold: ₹{lic_threshold}
    📱 Alerts: Telegram enabled
    
    **It will run continuously and send alerts for every signal!**
    """)
else:
    st.info("""
    🔴 24/7 Bot is STOPPED
    
    Click "▶️ START 24/7 BOT" in the sidebar to start
    """)

st.markdown("---")

# HISTORICAL ANALYSIS - DATE RANGE
st.header("📊 Historical Analysis - Date Range (BACKTEST)")
st.write(f"Pair: **{pair_display}** | Interval: **{interval}** | LIC Threshold: **₹{lic_threshold}**")
st.write(date_range_display)
st.write("**Trading Logic:** BUY at opening of next candle to LIC | SELL at closing of next candle to LIC")

if st.button("🔍 Analyze Date Range", key="analyze_range", use_container_width=True):
    if api_key == "YOUR_API_KEY_HERE":
        st.error("❌ Add API credentials first!")
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
                    limit=500
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
                        c1_body = abs(candle['close'] - candle['open'])
                        
                        if c1_body == 0:
                            continue
                        
                        c1_open = candle['open']
                        c1_close = candle['close']
                        c1_color = "🔴 RED" if c1_close < c1_open else "🟢 GREEN"
                        
                        lic_detected = "✅ YES" if c1_body >= lic_threshold else "❌ NO"
                        time_ist = convert_to_ist(candle['time'])
                        
                        trade_signal = "❌ NO"
                        entry_price = "-"
                        exit_price = "-"
                        quantity = "-"
                        profit_loss = "-"
                        trend_check = "-"
                        
                        if idx - 1 >= 0:
                            next_candle = filtered_candles[idx - 1]
                            c2_open = next_candle['open']
                            c2_close = next_candle['close']
                            
                            if c1_body >= lic_threshold and idx + 2 < len(filtered_candles):
                                older_candle1 = filtered_candles[idx + 1]
                                older_candle2 = filtered_candles[idx + 2]
                                
                                older_color1 = "🔴 RED" if older_candle1['close'] < older_candle1['open'] else "🟢 GREEN"
                                older_color2 = "🔴 RED" if older_candle2['close'] < older_candle2['open'] else "🟢 GREEN"
                                
                                all_colors = [older_color2, older_color1, c1_color]
                                
                                if c1_color == "🟢 GREEN":
                                    if all(color == "🟢 GREEN" for color in all_colors):
                                        trend_check = "✅ VALID (3 GREEN)"
                                        entry_price = f"₹{c2_open:.2f}"
                                        exit_price = f"₹{c2_close:.2f}"
                                        profit_val = c2_open - c2_close
                                        quantity = "1"
                                        profit_loss = f"+₹{profit_val:.2f}" if profit_val > 0 else f"-₹{abs(profit_val):.2f}"
                                        trade_signal = "✅ SHORT"
                                        
                                        date_stats['total_trades'] += 1
                                        if profit_val > 0:
                                            date_stats['wins'] += 1
                                        else:
                                            date_stats['losses'] += 1
                                        date_stats['total_pnl'] += profit_val
                                        
                                        send_telegram_alert(f"🟢 <b>SHORT SIGNAL!</b>\n📊 {pair_display} | {interval}\n⏰ {time_ist}\n💰 Entry: {entry_price}\n📉 Exit: {exit_price}\n📈 P&L: {profit_loss}\n🎯 Body: ₹{c1_body:.2f}")
                                
                                elif c1_color == "🔴 RED":
                                    if all(color == "🔴 RED" for color in all_colors):
                                        trend_check = "✅ VALID (3 RED)"
                                        entry_price = f"₹{c2_open:.2f}"
                                        exit_price = f"₹{c2_close:.2f}"
                                        profit_val = c2_close - c2_open
                                        quantity = "1"
                                        profit_loss = f"+₹{profit_val:.2f}" if profit_val > 0 else f"-₹{abs(profit_val):.2f}"
                                        trade_signal = "✅ LONG"
                                        
                                        date_stats['total_trades'] += 1
                                        if profit_val > 0:
                                            date_stats['wins'] += 1
                                        else:
                                            date_stats['losses'] += 1
                                        date_stats['total_pnl'] += profit_val
                                        
                                        send_telegram_alert(f"🔴 <b>LONG SIGNAL!</b>\n📊 {pair_display} | {interval}\n⏰ {time_ist}\n💰 Entry: {entry_price}\n📈 Exit: {exit_price}\n📈 P&L: {profit_loss}\n🎯 Body: ₹{c1_body:.2f}")
                        
                        candles_data.append({
                            'Time (IST)': time_ist,
                            'Open': f"₹{c1_open:.2f}",
                            'Close': f"₹{c1_close:.2f}",
                            'C1 Body': f"₹{c1_body:.2f}",
                            'C1 Color': c1_color,
                            'LIC': lic_detected,
                            'Trend': trend_check,
                            'Trade': trade_signal,
                            'Entry': entry_price,
                            'Exit': exit_price,
                            'Qty': quantity,
                            'Profit/Loss': profit_loss
                        })
                    
                    df_data = pd.DataFrame(candles_data)
                    
                    st.subheader("📈 Trading Statistics (Date Range)")
                    
                    stat_col1, stat_col2, stat_col3, stat_col4, stat_col5 = st.columns(5)
                    
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
                    
                    with stat_col5:
                        st.metric("Avg P&L/Trade", f"₹{date_stats['total_pnl']/date_stats['total_trades']:.2f}" if date_stats['total_trades'] > 0 else "₹0")
                    
                    st.markdown("---")
                    st.subheader("📋 Detailed Trade Analysis")
                    st.dataframe(df_data, use_container_width=True, hide_index=True)
                    
                    st.markdown("---")
                    
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
st.markdown("""
### ✅ ALL HARDCODED - NO INPUTS NEEDED!
- ✅ Telegram credentials hardcoded
- ✅ CoinDCX credentials hardcoded
- ✅ 24/7 bot ready to run
- ✅ Just select pair/interval and START!
""")

