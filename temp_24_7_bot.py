
import requests
import time
from coindcx import Client
from datetime import datetime
import pytz

COINDCX_API_KEY = "a75a34d3a4dd5c8a53922c2564d90fa1466f62301c51efb8"
COINDCX_API_SECRET = "acdb5ecc637e0b1af09f189137b7a3543f1e28e1ea4890c8fb4958ac4177e25c"
TELEGRAM_BOT_TOKEN = "8680315519:AAE4q_UA-CmXJGFlD4loge15zZgmceGzSQA"
TELEGRAM_CHAT_ID = "6312479033"
TRADING_PAIR = "KC-BTC_INR"
INTERVAL = "15m"
LIC_THRESHOLD = 150
CHECK_INTERVAL = 290
SHOW_ALL_COLORS = True
ALERT_ON_LIC = True

processed_candle_times = set()
processed_lic_times = set()

def send_telegram_alert(message):
    try:
        url = "https://api.telegram.org/bot" + TELEGRAM_BOT_TOKEN + "/sendMessage"
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
            msg = "🎯 <b>LIC DETECTED!</b>\n"
            msg += "📊 " + TRADING_PAIR + " | " + INTERVAL + "\n"
            msg += "⏰ " + time_ist + "\n\n"
            msg += "🎨 <b>Pattern:</b>\n"
            msg += older_color2_dot + " " + older_time2 + "\n"
            msg += older_color1_dot + " " + older_time1 + "\n"
            msg += c1_color_dot + " " + time_ist + " ← LIC " + c1_color + "\n\n"
            msg += "💰 Price: ₹" + str(round(c1_open, 2)) + "\n"
            msg += "🎯 <b>Body: ₹" + str(round(c1_body, 2)) + "</b>\n\n"
            msg += "⏳ Waiting for trend..."
            
            send_telegram_alert(msg)
            processed_lic_times.add(candle['time'])
        
        if SHOW_ALL_COLORS and candle['time'] not in processed_candle_times and not ALERT_ON_LIC:
            msg = "📊 <b>CANDLE COLORS - " + TRADING_PAIR + " | " + INTERVAL + "</b>\n\n"
            msg += "🎨 <b>Pattern:</b>\n"
            msg += older_color2_dot + " " + older_time2 + "\n"
            msg += older_color1_dot + " " + older_time1 + "\n"
            msg += c1_color_dot + " " + time_ist + " ← Current\n\n"
            msg += "💰 Price: ₹" + str(round(c1_open, 2)) + "\n"
            msg += "🎯 Body: ₹" + str(round(c1_body, 2)) + "\n"
            
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
                    msg = "🟢 <b>SHORT - TRADE!</b>\n\n"
                    msg += "📊 " + TRADING_PAIR + " | " + INTERVAL + "\n"
                    msg += "⏰ " + time_ist + "\n\n"
                    msg += "🎨 <b>Pattern (3 GREEN):</b>\n"
                    msg += older_color2_dot + " " + older_time2 + "\n"
                    msg += older_color1_dot + " " + older_time1 + "\n"
                    msg += c1_color_dot + " " + time_ist + " ← LIC\n\n"
                    msg += "💰 Entry: ₹" + str(round(c2_open, 2)) + "\n"
                    msg += "📉 Exit: ₹" + str(round(c2_close, 2)) + "\n"
                    msg += "📈 P&L: +₹" + str(round(profit_val, 2)) + "\n"
                    msg += "🎯 Body: ₹" + str(round(c1_body, 2)) + "\n\n"
                    msg += "✅ <b>READY!</b>"
                    
                    send_telegram_alert(msg)
                    processed_candle_times.add(candle['time'])
                
                elif c1_color == "RED" and older_color1 == "RED" and older_color2 == "RED":
                    profit_val = c2_close - c2_open
                    msg = "🔴 <b>LONG - TRADE!</b>\n\n"
                    msg += "📊 " + TRADING_PAIR + " | " + INTERVAL + "\n"
                    msg += "⏰ " + time_ist + "\n\n"
                    msg += "🎨 <b>Pattern (3 RED):</b>\n"
                    msg += older_color2_dot + " " + older_time2 + "\n"
                    msg += older_color1_dot + " " + older_time1 + "\n"
                    msg += c1_color_dot + " " + time_ist + " ← LIC\n\n"
                    msg += "💰 Entry: ₹" + str(round(c2_open, 2)) + "\n"
                    msg += "📈 Exit: ₹" + str(round(c2_close, 2)) + "\n"
                    msg += "📈 P&L: +₹" + str(round(profit_val, 2)) + "\n"
                    msg += "🎯 Body: ₹" + str(round(c1_body, 2)) + "\n\n"
                    msg += "✅ <b>READY!</b>"
                    
                    send_telegram_alert(msg)
                    processed_candle_times.add(candle['time'])
    except Exception as e:
        pass

startup_msg = "🟢 <b>24/7 BOT STARTED!</b>\n📊 " + TRADING_PAIR + " | " + INTERVAL + "\n⏰ " + datetime.now().strftime('%d-%m-%Y %H:%M:%S IST')
send_telegram_alert(startup_msg)

while True:
    try:
        check_signals()
        time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        break
    except:
        time.sleep(5)
