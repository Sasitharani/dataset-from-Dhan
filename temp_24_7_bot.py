
import requests
import time
from coindcx import Client
from datetime import datetime
import pytz

COINDCX_API_KEY = "a75a34d3a4dd5c8a53922c2564d90fa1466f62301c51efb8"
COINDCX_API_SECRET = "acdb5ecc637e0b1af09f189137b7a3543f1e28e1ea4890c8fb4958ac4177e25c"
TELEGRAM_BOT_TOKEN = "8680315519:AAE4q_UA-CmXJGFlD4loge15zZgmceGzSQA"
TELEGRAM_CHAT_ID = "6312479033"
TRADING_PAIR = "KC-BTC_USDT"
INTERVAL = "15m"
LIC_THRESHOLD = 150
CHECK_INTERVAL = 780

processed_candle_times = set()

def send_telegram_alert(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
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
                    send_telegram_alert(f"🟢 <b>SHORT SIGNAL!</b>\n📊 {TRADING_PAIR} | {INTERVAL}\n⏰ {time_ist}\n💰 Entry: ₹{c2_open:.2f}\n📉 Exit: ₹{c2_close:.2f}\n📈 P&L: +₹{profit_val:.2f}\n🎯 Body: ₹{c1_body:.2f}")
                    processed_candle_times.add(candle['time'])
                
                elif c1_color == "🔴 RED" and older_color1 == "🔴 RED" and older_color2 == "🔴 RED":
                    profit_val = c2_close - c2_open
                    send_telegram_alert(f"🔴 <b>LONG SIGNAL!</b>\n📊 {TRADING_PAIR} | {INTERVAL}\n⏰ {time_ist}\n💰 Entry: ₹{c2_open:.2f}\n📈 Exit: ₹{c2_close:.2f}\n📈 P&L: +₹{profit_val:.2f}\n🎯 Body: ₹{c1_body:.2f}")
                    processed_candle_times.add(candle['time'])
    except:
        pass

send_telegram_alert(f"🟢 <b>24/7 BOT STARTED!</b>\n📊 {TRADING_PAIR} | {INTERVAL}\n⏰ {datetime.now().strftime('%d-%m-%Y %H:%M:%S IST')}")

while True:
    try:
        check_signals()
        time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        break
    except:
        time.sleep(5)
