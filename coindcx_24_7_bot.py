import requests
import time
from coindcx import Client
from datetime import datetime, timedelta
import pytz

# ✅ HARDCODED CREDENTIALS
COINDCX_API_KEY = "a75a34d3a4dd5c8a53922c2564d90fa1466f62301c51efb8"  # Add your key
COINDCX_API_SECRET = "acdb5ecc637e0b1af09f189137b7a3543f1e28e1ea4890c8fb4958ac4177e25c"  # Add your secret
TELEGRAM_BOT_TOKEN = "8680315519:AAE4q_UA-CmXJGFlD4loge15zZgmceGzSQA"
TELEGRAM_CHAT_ID = "6312479033"

# ✅ BOT SETTINGS
TRADING_PAIR = "KC-BTC_INR"  # Change this to trade different pairs
INTERVAL = "5m"  # 1m, 5m, 15m, 1h, 4h
LIC_THRESHOLD = 300
CHECK_INTERVAL = 60  # Check every 60 seconds

# Track processed signals to avoid duplicates
processed_candle_times = set()

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

def send_telegram_alert(message):
    """Send alert message via Telegram"""
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
        print(f"❌ Telegram Error: {str(e)}")
        return False

def check_for_signals():
    """Check for LIC-LOC trading signals"""
    try:
        client = Client(
            api_key=COINDCX_API_KEY,
            api_secret=COINDCX_API_SECRET
        )
        
        # Fetch candles
        candles = client.get_candles(
            pair=TRADING_PAIR,
            interval=INTERVAL,
            limit=10
        )
        
        if not candles or len(candles) < 4:
            return False
        
        # Analyze current candle (C1)
        idx = 0
        candle = candles[idx]
        
        c1_body = abs(candle['close'] - candle['open'])
        
        # Skip doji candles
        if c1_body == 0:
            return False
        
        c1_open = candle['open']
        c1_close = candle['close']
        c1_color = "🔴 RED" if c1_close < c1_open else "🟢 GREEN"
        c1_high = candle['high']
        
        lic_detected = c1_body >= LIC_THRESHOLD
        time_ist = convert_to_ist(candle['time'])
        
        # Skip if already processed
        if candle['time'] in processed_candle_times:
            return False
        
        # Check trend confirmation (3 same color candles)
        if lic_detected and idx + 2 < len(candles):
            older_candle1 = candles[idx + 1]
            older_candle2 = candles[idx + 2]
            
            older_color1 = "🔴 RED" if older_candle1['close'] < older_candle1['open'] else "🟢 GREEN"
            older_color2 = "🔴 RED" if older_candle2['close'] < older_candle2['open'] else "🟢 GREEN"
            
            all_colors = [older_color2, older_color1, c1_color]
            
            # Check for next candle (C2)
            if idx - 1 >= 0:
                next_candle = candles[idx - 1]
                c2_open = next_candle['open']
                c2_close = next_candle['close']
                
                if c1_color == "🟢 GREEN":  # SHORT
                    if all(color == "🟢 GREEN" for color in all_colors):
                        profit_val = c2_open - c2_close
                        
                        # Send alert
                        alert_msg = f"""
🟢 <b>SHORT SIGNAL DETECTED!</b>
📊 {TRADING_PAIR} | {INTERVAL}
⏰ {time_ist}
💰 Entry: ₹{c2_open:.2f}
📉 Exit: ₹{c2_close:.2f}
📈 P&L: +₹{profit_val:.2f}
🎯 LIC Body: ₹{c1_body:.2f}
"""
                        send_telegram_alert(alert_msg)
                        processed_candle_times.add(candle['time'])
                        print(f"✅ SHORT SIGNAL SENT: {time_ist}")
                        return True
                
                elif c1_color == "🔴 RED":  # LONG
                    if all(color == "🔴 RED" for color in all_colors):
                        profit_val = c2_close - c2_open
                        
                        # Send alert
                        alert_msg = f"""
🔴 <b>LONG SIGNAL DETECTED!</b>
📊 {TRADING_PAIR} | {INTERVAL}
⏰ {time_ist}
💰 Entry: ₹{c2_open:.2f}
📈 Exit: ₹{c2_close:.2f}
📈 P&L: +₹{profit_val:.2f}
🎯 LIC Body: ₹{c1_body:.2f}
"""
                        send_telegram_alert(alert_msg)
                        processed_candle_times.add(candle['time'])
                        print(f"✅ LONG SIGNAL SENT: {time_ist}")
                        return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error checking signals: {str(e)}")
        return False

def main():
    """Main bot loop - runs 24/7"""
    print("=" * 80)
    print("🤖 COINDCX 24/7 TRADING BOT STARTED")
    print("=" * 80)
    print(f"Pair: {TRADING_PAIR}")
    print(f"Interval: {INTERVAL}")
    print(f"LIC Threshold: ₹{LIC_THRESHOLD}")
    print(f"Check Interval: {CHECK_INTERVAL} seconds")
    print(f"Telegram Alerts: ✅ ENABLED")
    print("=" * 80)
    print(f"⏰ Started at: {datetime.now().strftime('%d-%m-%Y %H:%M:%S IST')}")
    print("=" * 80)
    
    # Send startup alert
    send_telegram_alert(
        f"🟢 <b>24/7 BOT STARTED!</b>\n📊 {TRADING_PAIR} | {INTERVAL}\n⏰ {datetime.now().strftime('%d-%m-%Y %H:%M:%S IST')}"
    )
    
    # Main loop - runs forever
    while True:
        try:
            check_for_signals()
            
            # Wait before next check
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n🔴 BOT STOPPED BY USER")
            send_telegram_alert("🔴 <b>24/7 BOT STOPPED</b>\n⏰ " + datetime.now().strftime('%d-%m-%Y %H:%M:%S IST'))
            break
        except Exception as e:
            print(f"❌ Error in main loop: {str(e)}")
            time.sleep(5)  # Wait before retry

if __name__ == "__main__":
    main()

