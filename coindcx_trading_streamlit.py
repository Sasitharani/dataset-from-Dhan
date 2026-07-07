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

st.set_page_config(page_title="CoinDCX LIC-LOC Trading Bot", page_icon="🤖", layout="wide")

TELEGRAM_BOT_TOKEN = "8680315519:AAE4q_UA-CmXJGFlD4loge15zZgmceGzSQA"
TELEGRAM_CHAT_ID = "6312479033"
ENABLE_ALERTS = True

COINDCX_API_KEY = "a75a34d3a4dd5c8a53922c2564d90fa1466f62301c51efb8"
COINDCX_API_SECRET = "acdb5ecc637e0b1af09f189137b7a3543f1e28e1ea4890c8fb4958ac4177e25c"

api_key = COINDCX_API_KEY
api_secret = COINDCX_API_SECRET

if 'running' not in st.session_state:
    st.session_state.running = False

def convert_to_ist(timestamp_ms):
    try:
        if timestamp_ms > 10000000000:
            timestamp_s = timestamp_ms / 1000
        else:
            timestamp_s = timestamp_ms
        utc_dt = datetime.utcfromtimestamp(timestamp_s)
        ist = pytz.timezone('Asia/Kolkata')
        ist_dt = utc_dt.replace(tzinfo=pytz.UTC).astimezone(ist)
        return ist_dt.strftime('%d-%m-%Y %H:%M:%S')
    except:
        return str(timestamp_ms)

def send_telegram_alert(message):
    if not ENABLE_ALERTS:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        response = requests.post(url, data=data, timeout=5)
        return response.status_code == 200
    except:
        return False

def is_bot_running():
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

def start_24_7_bot(pair, interval, threshold, check_interval, show_all_colors, alert_on_lic):
    try:
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
SHOW_ALL_COLORS = {show_all_colors}
ALERT_ON_LIC = {alert_on_lic}

processed_candle_times = set()
processed_lic_times = set()

def send_telegram_alert(message):
    try:
        url = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendMessage"
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
        
        if c1_body == 0:
            return
        
        c1_open = candle['open']
        c1_close = candle['close']
        c1_color = "RED" if c1_close < c1_open else "GREEN"
        c1_color_dot = "🔴" if c1_close < c1_open else "🟢"
        time_ist = convert_to_ist(candle['time'])
        
        older_candle1 = candles[idx + 1]
        older_candle2 = candles[idx + 2]
        
        older_color1_dot = "🔴" if older_candle1['close'] < older_candle1['open'] else "🟢"
        older_color2_dot = "🔴" if older_candle2['close'] < older_candle2['open'] else "🟢"
        
        older_color1 = "RED" if older_candle1['close'] < older_candle1['open'] else "GREEN"
        older_color2 = "RED" if older_candle2['close'] < older_candle2['open'] else "GREEN"
        
        older_time1 = convert_to_ist(older_candle1['time'])
        older_time2 = convert_to_ist(older_candle2['time'])
        
        if ALERT_ON_LIC and c1_body >= LIC_THRESHOLD and candle['time'] not in processed_lic_times:
            msg = "🎯 <b>LIC DETECTED!</b>\\n"
            msg += "📊 " + TRADING_PAIR + " | " + INTERVAL + "\\n"
            msg += "⏰ " + time_ist + "\\n\\n"
            msg += "🎨 <b>Pattern:</b>\\n"
            msg += older_color2_dot + " " + older_time2 + "\\n"
            msg += older_color1_dot + " " + older_time1 + "\\n"
            msg += c1_color_dot + " " + time_ist + " ← LIC " + c1_color + "\\n\\n"
            msg += "💰 Price: ₹" + str(round(c1_open, 2)) + "\\n"
            msg += "🎯 <b>Body: ₹" + str(round(c1_body, 2)) + "</b>\\n\\n"
            msg += "⏳ Waiting for trend..."
            
            send_telegram_alert(msg)
            processed_lic_times.add(candle['time'])
        
        if SHOW_ALL_COLORS and candle['time'] not in processed_candle_times and not ALERT_ON_LIC:
            msg = "📊 <b>CANDLE COLORS - " + TRADING_PAIR + " | " + INTERVAL + "</b>\\n\\n"
            msg += "🎨 <b>Pattern:</b>\\n"
            msg += older_color2_dot + " " + older_time2 + "\\n"
            msg += older_color1_dot + " " + older_time1 + "\\n"
            msg += c1_color_dot + " " + time_ist + " ← Current\\n\\n"
            msg += "💰 Price: ₹" + str(round(c1_open, 2)) + "\\n"
            msg += "🎯 Body: ₹" + str(round(c1_body, 2)) + "\\n"
            
            if c1_body >= LIC_THRESHOLD:
                msg += "✅ <b>LIC!</b>"
            else:
                msg += "❌ Not LIC (need ₹" + str(LIC_THRESHOLD) + ")"
            
            send_telegram_alert(msg)
            processed_candle_times.add(candle['time'])
        
        if c1_body >= LIC_THRESHOLD and idx + 2 < len(candles):
            if idx - 1 >= 0:
                next_candle = candles[idx - 1]
                c2_open = next_candle['open']
                c2_close = next_candle['close']
                
                if c1_color == "GREEN" and older_color1 == "GREEN" and older_color2 == "GREEN":
                    profit_val = c2_open - c2_close
                    msg = "🟢 <b>SHORT - TRADE!</b>\\n\\n"
                    msg += "📊 " + TRADING_PAIR + " | " + INTERVAL + "\\n"
                    msg += "⏰ " + time_ist + "\\n\\n"
                    msg += "🎨 <b>Pattern (3 GREEN):</b>\\n"
                    msg += older_color2_dot + " " + older_time2 + "\\n"
                    msg += older_color1_dot + " " + older_time1 + "\\n"
                    msg += c1_color_dot + " " + time_ist + " ← LIC\\n\\n"
                    msg += "💰 Entry: ₹" + str(round(c2_open, 2)) + "\\n"
                    msg += "📉 Exit: ₹" + str(round(c2_close, 2)) + "\\n"
                    msg += "📈 P&L: +₹" + str(round(profit_val, 2)) + "\\n"
                    msg += "🎯 Body: ₹" + str(round(c1_body, 2)) + "\\n\\n"
                    msg += "✅ <b>READY!</b>"
                    
                    send_telegram_alert(msg)
                    processed_candle_times.add(candle['time'])
                
                elif c1_color == "RED" and older_color1 == "RED" and older_color2 == "RED":
                    profit_val = c2_close - c2_open
                    msg = "🔴 <b>LONG - TRADE!</b>\\n\\n"
                    msg += "📊 " + TRADING_PAIR + " | " + INTERVAL + "\\n"
                    msg += "⏰ " + time_ist + "\\n\\n"
                    msg += "🎨 <b>Pattern (3 RED):</b>\\n"
                    msg += older_color2_dot + " " + older_time2 + "\\n"
                    msg += older_color1_dot + " " + older_time1 + "\\n"
                    msg += c1_color_dot + " " + time_ist + " ← LIC\\n\\n"
                    msg += "💰 Entry: ₹" + str(round(c2_open, 2)) + "\\n"
                    msg += "📈 Exit: ₹" + str(round(c2_close, 2)) + "\\n"
                    msg += "📈 P&L: +₹" + str(round(profit_val, 2)) + "\\n"
                    msg += "🎯 Body: ₹" + str(round(c1_body, 2)) + "\\n\\n"
                    msg += "✅ <b>READY!</b>"
                    
                    send_telegram_alert(msg)
                    processed_candle_times.add(candle['time'])
    except Exception as e:
        pass

startup_msg = "🟢 <b>24/7 BOT STARTED!</b>\\n📊 " + TRADING_PAIR + " | " + INTERVAL + "\\n⏰ " + datetime.now().strftime('%d-%m-%Y %H:%M:%S IST')
send_telegram_alert(startup_msg)

while True:
    try:
        check_signals()
        time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        break
    except:
        time.sleep(5)
"""
        
        script_path = "/workspaces/dataset-from-Dhan/temp_24_7_bot.py"
        with open(script_path, 'w') as f:
            f.write(bot_script)
        
        subprocess.Popen(
            ['python', script_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        return True
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False

def stop_24_7_bot():
    try:
        os.system("pkill -f temp_24_7_bot.py")
        os.system("pkill -f coindcx_24_7_bot.py")
        return True
    except:
        return False

st.title("🤖 CoinDCX LIC-LOC Trading Bot")
st.markdown("---")

st.sidebar.header("🔐 API Credentials")
if api_key != "YOUR_API_KEY_HERE":
    st.sidebar.success("✅ Loaded")
else:
    st.sidebar.error("❌ NOT SET - Edit code!")

st.sidebar.markdown("---")
st.sidebar.header("🔔 Telegram")
st.sidebar.success("✅ ENABLED")

if st.sidebar.button("📢 Test Alert"):
    send_telegram_alert("🟢 TEST\n⏰ " + datetime.now().strftime('%d-%m-%Y %H:%M:%S IST'))
    st.sidebar.success("✅ Sent!")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Settings")

pair_display = st.sidebar.selectbox("Pair", ["BTC/INR", "ETH/INR", "BTC/USDT"])
pair_map = {"BTC/INR": "KC-BTC_INR", "ETH/INR": "KC-ETH_INR", "BTC/USDT": "KC-BTC_USDT"}
pair = pair_map[pair_display]

interval = st.sidebar.selectbox("Interval", ["1m", "5m", "15m", "1h", "4h"])
lic_threshold = st.sidebar.slider("LIC Threshold", 100, 1000, 300, 50)
check_interval = st.sidebar.slider("Check Interval (sec)", 30, 300, 60, 10)

st.sidebar.markdown("---")
st.sidebar.header("📢 Alerts")
alert_on_lic = st.sidebar.checkbox("🎯 LIC Formation", value=True)
show_all_colors = st.sidebar.checkbox("🎨 All Colors", value=False)

st.sidebar.markdown("---")
st.sidebar.header("🤖 Control")

col1, col2 = st.sidebar.columns(2)

with col1:
    if st.button("▶️ START", use_container_width=True):
        if start_24_7_bot(pair, interval, lic_threshold, check_interval, show_all_colors, alert_on_lic):
            st.sidebar.success("✅ Started!")
            send_telegram_alert(f"🟢 BOT STARTED\n📊 {pair_display}\n⏱️ {interval}")
        else:
            st.sidebar.error("❌ Error!")

with col2:
    if st.button("⏹️ STOP", use_container_width=True):
        if stop_24_7_bot():
            st.sidebar.success("✅ Stopped!")
            send_telegram_alert("🔴 BOT STOPPED")
        else:
            st.sidebar.error("❌ Error!")

st.sidebar.markdown("---")
st.sidebar.header("📅 Backtest Analysis")

today = datetime.now().date()
default_start = today - timedelta(days=7)

start_date = st.sidebar.date_input("Start Date", value=default_start, max_value=today)
end_date = st.sidebar.date_input("End Date", value=today, min_value=start_date, max_value=today)

st.markdown("---")
st.header("🤖 LIVE BOT STATUS")

if is_bot_running():
    st.success(f"🟢 RUNNING - {pair_display} | {interval}")
    st.write(f"Check every {check_interval}s | LIC: ₹{lic_threshold}")
    st.write(f"LIC Alerts: {'ON' if alert_on_lic else 'OFF'} | Color Alerts: {'ON' if show_all_colors else 'OFF'}")
else:
    st.error("🔴 STOPPED - Click START")

st.markdown("---")
st.header("📊 BACKTEST ANALYSIS")
st.write(f"Pair: **{pair_display}** | Interval: **{interval}** | LIC Threshold: **₹{lic_threshold}**")
st.write(f"Date Range: **{start_date}** to **{end_date}**")

if st.button("🔍 Analyze Date Range", use_container_width=True):
    if api_key == "YOUR_API_KEY_HERE":
        st.error("❌ Add API credentials first!")
    else:
        try:
            client = Client(api_key=api_key, api_secret=api_secret)
            
            with st.spinner(f"Fetching data for {pair_display}..."):
                candles = client.get_candles(pair=pair, interval=interval, limit=500)
            
            if candles and len(candles) > 0:
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
                    date_stats = {'total_trades': 0, 'wins': 0, 'losses': 0, 'total_pnl': 0.0, 'lic_count': 0}
                    
                    for idx, candle in enumerate(filtered_candles):
                        c1_body = abs(candle['close'] - candle['open'])
                        
                        if c1_body == 0:
                            continue
                        
                        c1_open = candle['open']
                        c1_close = candle['close']
                        c1_color = "🔴 RED" if c1_close < c1_open else "🟢 GREEN"
                        
                        lic_detected = "✅ YES" if c1_body >= lic_threshold else "❌ NO"
                        time_ist = convert_to_ist(candle['time'])
                        
                        if c1_body >= lic_threshold:
                            date_stats['lic_count'] += 1
                        
                        colors_pattern = f"{c1_color}"
                        if idx + 1 < len(filtered_candles):
                            older_candle1 = filtered_candles[idx + 1]
                            older_color1 = "🔴" if older_candle1['close'] < older_candle1['open'] else "🟢"
                            colors_pattern = f"{older_color1} {colors_pattern}"
                        if idx + 2 < len(filtered_candles):
                            older_candle2 = filtered_candles[idx + 2]
                            older_color2 = "🔴" if older_candle2['close'] < older_candle2['open'] else "🟢"
                            colors_pattern = f"{older_color2} {colors_pattern}"
                        
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
                        
                        candles_data.append({
                            'Time': time_ist,
                            'Open': f"₹{c1_open:.2f}",
                            'Close': f"₹{c1_close:.2f}",
                            'Body': f"₹{c1_body:.2f}",
                            'Color': c1_color,
                            'Pattern': colors_pattern,
                            'LIC': lic_detected,
                            'Trend': trend_check,
                            'Signal': trade_signal,
                            'Entry': entry_price,
                            'Exit': exit_price,
                            'Qty': quantity,
                            'P&L': profit_loss
                        })
                    
                    df_data = pd.DataFrame(candles_data)
                    
                    st.subheader("📈 Statistics")
                    
                    stat_col1, stat_col2, stat_col3, stat_col4, stat_col5, stat_col6 = st.columns(6)
                    
                    with stat_col1:
                        st.metric("LICs", date_stats['lic_count'])
                    
                    with stat_col2:
                        st.metric("Trades", date_stats['total_trades'])
                    
                    with stat_col3:
                        st.metric("Wins", date_stats['wins'])
                    
                    with stat_col4:
                        total = date_stats['total_trades']
                        wins = date_stats['wins']
                        win_rate = (wins / total * 100) if total > 0 else 0
                        st.metric("Win %", f"{win_rate:.1f}%")
                    
                    with stat_col5:
                        st.metric("Total P&L", f"₹{date_stats['total_pnl']:.2f}")
                    
                    with stat_col6:
                        st.metric("Avg P&L", f"₹{date_stats['total_pnl']/date_stats['total_trades']:.2f}" if date_stats['total_trades'] > 0 else "₹0")
                    
                    st.markdown("---")
                    st.subheader("📋 All Candles")
                    st.dataframe(df_data, use_container_width=True, hide_index=True)
                    
                    st.markdown("---")
                    
                    csv = df_data.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"{pair_display.replace('/', '_')}_{start_date}_{end_date}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
        
        except Exception as e:
            st.error(f"Error: {str(e)}")

