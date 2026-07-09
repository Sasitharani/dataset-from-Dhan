"""
CoinDCX Crypto Futures Client - FIXED
Handles balances, market orders, scheduled orders
Uses correct API signatures for get_futures_candles and list_futures_orders
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from coindcx import Client
from coindcx.enums import OrderSide, FuturesOrderType
import json
from datetime import datetime, timedelta
import time
import threading

env_path = Path('/workspaces/dataset-from-Dhan/.env')
load_dotenv(env_path, override=True)

COINDCX_API_KEY = os.getenv('COINDCX_API_KEY')
COINDCX_API_SECRET = os.getenv('COINDCX_API_SECRET')

class CryptoFuturesClient:
    """CoinDCX Crypto Futures Handler - Fixed API"""
    
    def __init__(self):
        print("\n[CryptoFuturesClient] Initializing...")
        self.client = Client(api_key=COINDCX_API_KEY, api_secret=COINDCX_API_SECRET)
        self.trades_file = Path('/workspaces/dataset-from-Dhan/crypto_trades.json')
        self.scheduled_orders = {}
        print("[CryptoFuturesClient] ✅ Ready")
    
    def get_balances(self):
        """Get account balances"""
        try:
            balances = self.client.get_balances()
            print(f"[get_balances] ✅ Fetched")
            return balances
        except Exception as e:
            print(f"[get_balances] ❌ Error: {e}")
            return None
    
    def get_futures_candles(self, pair, interval_minutes=15, limit=50):
        """Get futures candles
        
        API signature: get_futures_candles(pair, from_time, to_time, resolution)
        resolution examples: "1minute", "5minute", "15minute", "1hour", "1day"
        """
        try:
            # Calculate time range (last N candles)
            to_time = int(datetime.now().timestamp())
            from_time = int((datetime.now() - timedelta(minutes=interval_minutes * limit)).timestamp())
            
            # Map minutes to resolution string
            resolution_map = {
                1: "1minute",
                5: "5minute",
                15: "15minute",
                25: "25minute",
                60: "1hour",
                1440: "1day"
            }
            resolution = resolution_map.get(interval_minutes, "15minute")
            
            print(f"[get_futures_candles] Fetching {pair} ({resolution})...")
            
            candles = self.client.get_futures_candles(
                pair=pair,
                from_time=from_time,
                to_time=to_time,
                resolution=resolution
            )
            
            if candles and isinstance(candles, dict) and 'data' in candles:
                data = candles['data']
                if data:
                    data = list(reversed(data))  # Oldest first
                    print(f"[get_futures_candles] ✅ Got {len(data)} candles")
                    return data
            
            print(f"[get_futures_candles] ❌ No data")
            return None
            
        except Exception as e:
            print(f"[get_futures_candles] ❌ Error: {e}")
            return None
    
    def get_next_candle_open_time(self, pair, interval_minutes=15):
        """Calculate when next candle opens"""
        candles = self.get_futures_candles(pair, interval_minutes, limit=1)
        
        if not candles:
            print("[get_next_candle_open_time] ❌ No candles")
            return None
        
        last_candle = candles[-1]
        last_time = datetime.fromtimestamp(last_candle.get('time', 0) / 1000)
        next_open = last_time + timedelta(minutes=interval_minutes)
        
        print(f"[get_next_candle_open_time] Next: {next_open}")
        return next_open
    
    def create_futures_order(self, pair, side, total_quantity, leverage=1):
        """Create market futures order (BUY or SELL)"""
        try:
            print(f"[create_futures_order] {side} {total_quantity} {pair} (leverage: {leverage}x)")
            
            side_enum = OrderSide.BUY if side.upper() == 'BUY' else OrderSide.SELL
            
            order = self.client.create_futures_order(
                pair=pair,
                side=side_enum,
                order_type=FuturesOrderType.MARKET,
                total_quantity=total_quantity,
                leverage=leverage
            )
            
            if order:
                print(f"[create_futures_order] ✅ Order created!")
                self._save_trade(pair, side, total_quantity, order)
                return order
            else:
                print(f"[create_futures_order] ❌ Order failed")
                return None
                
        except Exception as e:
            print(f"[create_futures_order] ❌ Error: {str(e)[:100]}")
            return None
    
    def schedule_sell_at_next_candle(self, pair, total_quantity, interval_minutes=15, leverage=1):
        """Schedule a SELL order at next candle open"""
        try:
            next_open = self.get_next_candle_open_time(pair, interval_minutes)
            
            if not next_open:
                print("[schedule_sell] ❌ Couldn't get next candle time")
                return None
            
            wait_seconds = (next_open - datetime.now()).total_seconds()
            
            if wait_seconds <= 0:
                print("[schedule_sell] ❌ Next candle already opened")
                return None
            
            order_id = f"scheduled_{int(datetime.now().timestamp())}"
            
            print(f"[schedule_sell] ⏰ Order scheduled!")
            print(f"  Will execute at: {next_open.strftime('%H:%M:%S')}")
            
            self.scheduled_orders[order_id] = {
                'time': next_open.isoformat(),
                'pair': pair,
                'side': 'SELL',
                'quantity': total_quantity,
                'leverage': leverage,
                'status': 'PENDING'
            }
            
            def execute_scheduled():
                time.sleep(wait_seconds)
                print(f"[scheduled_sell] Executing {order_id}...")
                result = self.create_futures_order(pair, 'SELL', total_quantity, leverage)
                if result:
                    self.scheduled_orders[order_id]['status'] = 'EXECUTED'
                else:
                    self.scheduled_orders[order_id]['status'] = 'FAILED'
            
            thread = threading.Thread(target=execute_scheduled, daemon=True)
            thread.start()
            
            return order_id
            
        except Exception as e:
            print(f"[schedule_sell] ❌ Error: {e}")
            return None
    
    def get_scheduled_orders(self):
        """Get all scheduled orders"""
        return self.scheduled_orders
    
    def cancel_scheduled_order(self, order_id):
        """Cancel a scheduled order"""
        if order_id in self.scheduled_orders:
            self.scheduled_orders[order_id]['status'] = 'CANCELLED'
            print(f"[cancel_scheduled] ✅ {order_id} cancelled")
            return True
        return False
    
    def get_futures_orders(self, side='BUY'):
        """Get active futures orders for a side"""
        try:
            side_enum = OrderSide.BUY if side.upper() == 'BUY' else OrderSide.SELL
            
            orders = self.client.list_futures_orders(side=side_enum, status='open')
            print(f"[get_futures_orders] ✅ Got {len(orders) if orders else 0} {side} orders")
            return orders
        except Exception as e:
            print(f"[get_futures_orders] ❌ Error: {e}")
            return []
    
    def get_futures_trade_history(self, pair=None):
        """Get futures trade history"""
        try:
            history = self.client.get_futures_trade_history(pair=pair)
            print(f"[get_futures_trade_history] ✅ Got {len(history) if history else 0} trades")
            return history
        except Exception as e:
            print(f"[get_futures_trade_history] ❌ Error: {e}")
            return []
    
    def _save_trade(self, pair, side, total_quantity, order_data):
        """Save trade to JSON"""
        try:
            trades = []
            if self.trades_file.exists():
                with open(self.trades_file) as f:
                    trades = json.load(f)
            
            trades.append({
                'timestamp': datetime.now().isoformat(),
                'pair': pair,
                'side': side,
                'quantity': total_quantity,
                'order': order_data
            })
            
            with open(self.trades_file, 'w') as f:
                json.dump(trades, f, indent=2)
            
            print(f"[_save_trade] ✅ Saved")
        except Exception as e:
            print(f"[_save_trade] ❌ Error: {e}")
    
    def get_trade_history(self):
        """Get all saved trades"""
        try:
            if self.trades_file.exists():
                with open(self.trades_file) as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"[get_trade_history] ❌ Error: {e}")
            return []

print("\n[GLOBAL] Creating CryptoFuturesClient...")
crypto_client = CryptoFuturesClient()
print(f"[GLOBAL] Crypto client ready\n")

