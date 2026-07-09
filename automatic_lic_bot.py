"""
AUTOMATIC LIC TRADING BOT - DOGE Futures
Real-time DOGE monitoring with automatic LIC signal detection
"""

import os
import sys
sys.path.insert(0, '/workspaces/dataset-from-Dhan')
os.chdir('/workspaces/dataset-from-Dhan')

from coindcx import Client
from coindcx.enums import OrderSide, FuturesOrderType
from dotenv import load_dotenv
from pathlib import Path
import json
from datetime import datetime, timedelta
import time
import requests

# ==================== CONFIG ====================
load_dotenv(Path('/workspaces/dataset-from-Dhan/.env'), override=True)

COINDCX_API_KEY = os.getenv('COINDCX_API_KEY')
COINDCX_API_SECRET = os.getenv('COINDCX_API_SECRET')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

CONFIG = {
    'pair': 'B-DOGE_USDT',
    'interval_minutes': 15,
    'position_size': 100.0,  # ← FIXED: MINIMUM 1.0 DOGE
    'max_positions': 1,
    'stop_loss_percent': 2.5,
    'margin_currency': 'INR'
}

# ==================== BOT STATE ====================
class BotState:
    def __init__(self):
        self.state_file = Path('/workspaces/dataset-from-Dhan/bot_state.json')
        self.trades_file = Path('/workspaces/dataset-from-Dhan/bot_trades.json')
        self.position = None
        self.entry_price = None
        self.entry_time = None
        self.load_state()
    
    def load_state(self):
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    data = json.load(f)
                    self.position = data.get('position')
                    self.entry_price = data.get('entry_price')
                    self.entry_time = data.get('entry_time')
                print(f"[STATE] Loaded: {self.position}")
            except Exception as e:
                print(f"[STATE] Error loading: {e}")
    
    def save_state(self):
        try:
            with open(self.state_file, 'w') as f:
                json.dump({
                    'position': self.position,
                    'entry_price': self.entry_price,
                    'entry_time': self.entry_time,
                    'updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"[STATE] Error saving: {e}")
    
    def save_trade(self, trade_data):
        try:
            trades = []
            if self.trades_file.exists():
                with open(self.trades_file) as f:
                    trades = json.load(f)
            
            trades.append(trade_data)
            
            with open(self.trades_file, 'w') as f:
                json.dump(trades, f, indent=2)
        except Exception as e:
            print(f"[TRADE] Error saving: {e}")

# ==================== LIC BOT ====================
class LICTradingBot:
    def __init__(self):
        print("\n[BOT] Initializing LIC Trading Bot - DOGE...")
        self.client = Client(api_key=COINDCX_API_KEY, api_secret=COINDCX_API_SECRET)
        self.state = BotState()
        print("[BOT] ✅ Ready!\n")
    
    def get_candles(self, limit=50):
        """Get DOGE candles (15m)"""
        try:
            now = int(datetime.now().timestamp())
            past = int((datetime.now() - timedelta(minutes=15*limit)).timestamp())
            
            candles = self.client.get_futures_candles(
                pair=CONFIG['pair'],
                from_time=past,
                to_time=now,
                resolution='15'
            )
            
            if candles and isinstance(candles, dict) and 'data' in candles:
                data = candles['data']
                if data:
                    data = list(reversed(data))
                    return data
            return None
        except Exception as e:
            print(f"[CANDLES] ❌ {e}")
            return None
    
    def calculate_dynamic_threshold(self, candles):
        """Calculate LIC threshold dynamically"""
        if not candles or len(candles) < 10:
            return 0.001
        
        recent = candles[-10:]
        bodies = []
        
        for candle in recent:
            body = abs(candle.get('close', 0) - candle.get('open', 0))
            bodies.append(body)
        
        avg_body = sum(bodies) / len(bodies)
        threshold = avg_body * 1.5
        
        print(f"[THRESHOLD] Avg body: ${avg_body:.6f}, Dynamic threshold: ${threshold:.6f}")
        return threshold
    
    def detect_lic(self, candles):
        """Detect LIC signal"""
        if not candles or len(candles) < 3:
            return None
        
        threshold = self.calculate_dynamic_threshold(candles)
        
        latest = candles[-1]
        body = abs(latest.get('close', 0) - latest.get('open', 0))
        color = 'GREEN' if latest.get('close', 0) > latest.get('open', 0) else 'RED'
        
        trend_colors = []
        for i in range(-3, 0):
            c = candles[i]
            trend_colors.append('GREEN' if c.get('close', 0) > c.get('open', 0) else 'RED')
        
        trend_valid = all(tc == trend_colors[0] for tc in trend_colors)
        
        if body >= threshold and trend_valid and color == trend_colors[0]:
            signal = {
                'type': 'SHORT' if color == 'GREEN' else 'LONG',
                'body': body,
                'threshold': threshold,
                'price': latest.get('close', 0),
                'time': datetime.fromtimestamp(latest.get('time', 0) / 1000)
            }
            return signal
        
        return None
    
    def send_telegram(self, message):
        """Send Telegram alert"""
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': message})
            print(f"[TELEGRAM] ✅ Sent")
        except Exception as e:
            print(f"[TELEGRAM] ❌ {e}")
    
    def place_buy_order(self):
        """Place BUY order"""
        try:
            print(f"[ORDER] Placing BUY {CONFIG['position_size']} DOGE...")
            
            order = self.client.create_futures_order(
                pair=CONFIG['pair'],
                side=OrderSide.BUY,
                order_type=FuturesOrderType.MARKET,
                total_quantity=CONFIG['position_size'],
                margin_currency_short_name=CONFIG['margin_currency']
            )
            
            if order:
                print(f"[ORDER] ✅ BUY SUCCESS!")
                self.state.position = 'LONG'
                self.state.entry_price = order.get('price', 0)
                self.state.entry_time = datetime.now().isoformat()
                self.state.save_state()
                
                msg = f"🟢 BUY DOGE\nPrice: ${order.get('price', 0):.6f}\nSize: {CONFIG['position_size']} DOGE"
                self.send_telegram(msg)
                
                return order
            else:
                print(f"[ORDER] ❌ BUY FAILED")
                return None
        except Exception as e:
            print(f"[ORDER] ❌ {e}")
            self.send_telegram(f"❌ BUY ERROR: {e}")
            return None
    
    def place_sell_order(self):
        """Place SELL order"""
        try:
            print(f"[ORDER] Placing SELL {CONFIG['position_size']} DOGE...")
            
            order = self.client.create_futures_order(
                pair=CONFIG['pair'],
                side=OrderSide.SELL,
                order_type=FuturesOrderType.MARKET,
                total_quantity=CONFIG['position_size'],
                margin_currency_short_name=CONFIG['margin_currency']
            )
            
            if order:
                print(f"[ORDER] ✅ SELL SUCCESS!")
                
                exit_price = order.get('price', 0)
                pnl = (exit_price - self.state.entry_price) * CONFIG['position_size']
                pnl_percent = ((exit_price - self.state.entry_price) / self.state.entry_price) * 100
                
                self.state.save_trade({
                    'timestamp': datetime.now().isoformat(),
                    'entry': self.state.entry_price,
                    'exit': exit_price,
                    'size': CONFIG['position_size'],
                    'pnl': pnl,
                    'pnl_percent': pnl_percent
                })
                
                self.state.position = None
                self.state.entry_price = None
                self.state.save_state()
                
                emoji = "✅" if pnl > 0 else "❌"
                msg = f"{emoji} SELL DOGE\nEntry: ${self.state.entry_price:.6f}\nExit: ${exit_price:.6f}\nP&L: ${pnl:.6f} ({pnl_percent:.2f}%)"
                self.send_telegram(msg)
                
                return order
            else:
                print(f"[ORDER] ❌ SELL FAILED")
                return None
        except Exception as e:
            print(f"[ORDER] ❌ {e}")
            return None
    
    def check_stop_loss(self, current_price):
        """Check if stop loss triggered"""
        if not self.state.position or not self.state.entry_price:
            return False
        
        loss_percent = ((self.state.entry_price - current_price) / self.state.entry_price) * 100
        
        if loss_percent >= CONFIG['stop_loss_percent']:
            print(f"[STOPLOSS] ⚠️ Triggered! Loss: {loss_percent:.2f}%")
            self.send_telegram(f"⚠️ STOP LOSS TRIGGERED\nLoss: {loss_percent:.2f}%")
            return True
        
        return False
    
    def run(self):
        """Main bot loop"""
        print("[BOT] Starting automatic DOGE trading...\n")
        
        iteration = 0
        
        while True:
            iteration += 1
            now = datetime.now()
            print(f"\n[{iteration}] {now.strftime('%H:%M:%S')} - Checking signals...")
            
            try:
                candles = self.get_candles()
                if not candles:
                    print("[BOT] No candles, retrying...")
                    time.sleep(30)
                    continue
                
                latest = candles[-1]
                current_price = latest.get('close', 0)
                
                if self.state.position:
                    if self.check_stop_loss(current_price):
                        self.place_sell_order()
                    else:
                        pnl = (current_price - self.state.entry_price) * CONFIG['position_size']
                        print(f"[POSITION] Open at ${self.state.entry_price:.6f}, Current: ${current_price:.6f}, P&L: ${pnl:.6f}")
                
                if not self.state.position:
                    signal = self.detect_lic(candles)
                    
                    if signal:
                        print(f"[SIGNAL] ✅ LIC Signal detected!")
                        print(f"  Type: {signal['type']}")
                        print(f"  Body: ${signal['body']:.6f}")
                        print(f"  Price: ${signal['price']:.6f}")
                        
                        self.place_buy_order()
                
                time.sleep(60)
                
            except KeyboardInterrupt:
                print("\n[BOT] Stopped by user")
                break
            except Exception as e:
                print(f"[BOT] ❌ Error: {e}")
                time.sleep(60)

# ==================== MAIN ====================
if __name__ == '__main__':
    bot = LICTradingBot()
    bot.run()

