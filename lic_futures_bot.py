import os
import json
from dotenv import load_dotenv
from coindcx import Client
from datetime import datetime
import requests
import time
from pathlib import Path

load_dotenv()

API_KEY = os.getenv('COINDCX_API_KEY')
API_SECRET = os.getenv('COINDCX_API_SECRET')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT = os.getenv('TELEGRAM_CHAT_ID')

CONFIG_FILE = '/workspaces/dataset-from-Dhan/bot_config.json'
TRADES_FILE = '/workspaces/dataset-from-Dhan/trades_data.json'
BOT_STATE_FILE = '/workspaces/dataset-from-Dhan/bot_state.json'
ANALYSIS_FILE = '/workspaces/dataset-from-Dhan/analysis_table.json'

def load_config():
    if Path(CONFIG_FILE).exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        'pairs': ['KC-BTC_USDT', 'KC-ETH_USDT'],
        'interval': '5m',
        'lic_threshold': 300,
        'check_interval': 60,
        'leverage': 5,
    }

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT, "text": msg, "parse_mode": "HTML"}
        requests.post(url, data=data, timeout=5)
    except:
        pass

def load_trades():
    if Path(TRADES_FILE).exists():
        with open(TRADES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_trades(trades):
    with open(TRADES_FILE, 'w') as f:
        json.dump(trades, f, indent=2)

def load_state():
    if Path(BOT_STATE_FILE).exists():
        with open(BOT_STATE_FILE, 'r') as f:
            return json.load(f)
    return {'balance': 1000}

def save_state(state):
    with open(BOT_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def load_analysis():
    if Path(ANALYSIS_FILE).exists():
        with open(ANALYSIS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_analysis(analysis):
    with open(ANALYSIS_FILE, 'w') as f:
        json.dump(analysis, f, indent=2)

def get_candles(pair, interval, limit=20):
    try:
        client = Client(api_key=API_KEY, api_secret=API_SECRET)
        return client.get_candles(pair=pair, interval=interval, limit=limit)
    except Exception as e:
        print(f"  Candle error: {e}")
        return None

def get_color(candle):
    """Get candle color"""
    return '🟢' if candle['close'] > candle['open'] else '🔴'

def get_body(candle):
    """Get candle body size"""
    return abs(candle['close'] - candle['open'])

def detect_lic(candles, threshold):
    """Detect LIC - checks if C1 has large body"""
    if not candles:
        return False, None, 0
    
    c1 = candles[0]
    body = get_body(c1)
    color = get_color(c1)
    
    if body >= threshold:
        return True, color, body
    return False, color, body

def check_trend(candles):
    """Check if last 3 candles are same color"""
    if len(candles) < 3:
        return False, None
    
    colors = [get_color(candles[0]), get_color(candles[1]), get_color(candles[2])]
    
    if colors[0] == colors[1] == colors[2]:
        return True, colors[0]
    return False, None

def create_analysis_row(pair, candles, threshold):
    """Create a row for the analysis table"""
    if not candles or len(candles) < 3:
        return None
    
    c1 = candles[0]  # Current candle
    c2 = candles[1]  # Previous
    c3 = candles[2]  # 2 candles back
    
    # Basic info
    timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    open_price = c1['open']
    close_price = c1['close']
    body = get_body(c1)
    color = get_color(c1)
    
    # Detect LIC
    is_lic, lic_color, lic_body = detect_lic(candles, threshold)
    lic_status = '✅' if is_lic else '❌'
    
    # Check trend
    trend_valid, trend_color = check_trend(candles)
    trend_status = '✅' if trend_valid else '❌'
    
    # Pattern (3 colors)
    c1_color = get_color(c1)
    c2_color = get_color(c2)
    c3_color = get_color(c3)
    pattern = f"{c1_color}{c2_color}{c3_color}"
    
    # Get signal
    signal = '❌'
    entry = '-'
    if is_lic and trend_valid and lic_color == trend_color:
        signal = 'SHORT' if lic_color == '🟢' else 'LONG'
        entry = f"{c2['open']:.2f}" if len(candles) > 1 else f"{c1['open']:.2f}"
    
    # Create row (matching original format)
    row = {
        'Time': timestamp,
        'Pair': pair,
        'Open': f"{open_price:.2f}",
        'Close': f"{close_price:.2f}",
        'Body': f"{body:.2f}",
        'Color': color,
        'Pattern': pattern,
        'LIC': lic_status,
        'Trend': trend_status,
        'Signal': signal,
        'Entry': entry,
        'Qty': '0.001' if signal != '❌' else '-',
    }
    
    return row

def execute_trade(pair, signal, candles, cfg):
    """Execute a simulated trade"""
    trades = load_trades()
    state = load_state()
    
    entry_price = candles[1]['open'] if len(candles) > 1 else candles[0]['open']
    qty = 0.001
    margin = (entry_price * qty * 83) / cfg['leverage']
    
    if margin > state['balance']:
        print(f"    ❌ Insufficient balance")
        return False
    
    trade = {
        'id': len(trades) + 1,
        'timestamp': datetime.now().isoformat(),
        'pair': pair,
        'side': signal,
        'entry_price': entry_price,
        'qty': qty,
        'leverage': cfg['leverage'],
        'sl_price': candles[0]['high'] + 10,
        'margin': margin,
        'status': 'OPEN'
    }
    
    trades.append(trade)
    state['balance'] -= margin
    
    save_trades(trades)
    save_state(state)
    
    msg = f"🟢 <b>{pair} {signal}</b>\nEntry: ₹{entry_price * 83:.2f}"
    send_telegram(msg)
    
    print(f"    ✅ Trade #{trade['id']}")
    return True

def main():
    print("=" * 80)
    print("🤖 LIC 24/7 FUTURES BOT")
    print("=" * 80)
    
    send_telegram("🤖 Bot Started")
    
    iteration = 0
    
    while True:
        try:
            cfg = load_config()
            iteration += 1
            
            timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
            print(f"\n[{timestamp}] Iteration {iteration}")
            print(f"Config: Threshold={cfg['lic_threshold']} Interval={cfg['interval']}")
            
            # Load analysis table
            table = load_analysis()
            
            # Check each pair
            for pair in cfg['pairs']:
                print(f"\n  [{pair}] Analyzing...")
                
                candles = get_candles(pair, cfg['interval'], limit=20)
                if not candles:
                    print(f"    ❌ No candles")
                    continue
                
                # Create analysis row
                row = create_analysis_row(pair, candles, cfg['lic_threshold'])
                if row:
                    table.append(row)
                    print(f"    ✅ Analysis added")
                
                # Check for signal
                is_lic, lic_color, body = detect_lic(candles, cfg['lic_threshold'])
                trend_valid, trend_color = check_trend(candles)
                
                if is_lic and trend_valid and lic_color == trend_color:
                    signal = 'SHORT' if lic_color == '🟢' else 'LONG'
                    print(f"    🟢 SIGNAL: {signal}")
                    execute_trade(pair, signal, candles, cfg)
                else:
                    print(f"    ⏳ No signal")
            
            # Save analysis table (keep last 200 rows)
            if len(table) > 200:
                table = table[-200:]
            save_analysis(table)
            
            # Show status
            state = load_state()
            trades = load_trades()
            open_count = len([t for t in trades if t['status'] == 'OPEN'])
            
            print(f"\nStatus: Balance=₹{state['balance']:.2f} Open={open_count} Rows={len(table)}")
            print(f"Waiting {cfg['check_interval']}s...")
            
            time.sleep(cfg['check_interval'])
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(60)

if __name__ == "__main__":
    main()
