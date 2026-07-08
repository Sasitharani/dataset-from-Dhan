import streamlit as st
import requests
from coindcx import Client
from datetime import datetime
import pandas as pd
import json

st.set_page_config(page_title="Futures Trading", page_icon="💰", layout="wide")

COINDCX_API_KEY = "a75a34d3a4dd5c8a53922c2564d90fa1466f62301c51efb8"
COINDCX_API_SECRET = "acdb5ecc637e0b1af09f189137b7a3543f1e28e1ea4890c8fb4958ac4177e25c"
TELEGRAM_BOT_TOKEN = "8680315519:AAE4q_UA-CmXJGFlD4loge15zZgmceGzSQA"
TELEGRAM_CHAT_ID = "6312479033"

if 'trades' not in st.session_state:
    st.session_state.trades = []
if 'usdt_balance' not in st.session_state:
    st.session_state.usdt_balance = 0

def send_alert(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}
        requests.post(url, data=data, timeout=5)
        return True
    except:
        return False

def get_usdt_balance():
    """Get USDT balance for futures trading"""
    try:
        client = Client(api_key=COINDCX_API_KEY, api_secret=COINDCX_API_SECRET)
        balances = client.get_balances()
        
        # Find USDT balance
        for b in balances:
            if b['currency'] == 'USDT':
                return True, float(b['balance'])
        
        return False, "No USDT balance found"
    except Exception as e:
        return False, str(e)

def get_price(pair):
    try:
        client = Client(api_key=COINDCX_API_KEY, api_secret=COINDCX_API_SECRET)
        candles = client.get_candles(pair=pair, interval="1m", limit=1)
        if candles:
            return True, candles[0]['close']
        return False, "No data"
    except Exception as e:
        return False, str(e)

def place_futures_order(pair, side, qty, leverage):
    """Place futures order using futures endpoint"""
    try:
        client = Client(api_key=COINDCX_API_KEY, api_secret=COINDCX_API_SECRET)
        
        # Use futures endpoint
        order = client.futures.create_order(
            pair=pair,
            side=side,
            quantity=qty,
            leverage=leverage,
            order_type="market"
        )
        return True, order
    except Exception as e:
        return False, str(e)

def get_futures_orders(side):
    """Get open futures orders"""
    try:
        client = Client(api_key=COINDCX_API_KEY, api_secret=COINDCX_API_SECRET)
        orders = client.list_futures_orders(side=side)
        return True, orders
    except Exception as e:
        return False, str(e)

# UI
st.title("💰 CoinDCX Futures Trading")
st.markdown("Using USDT Wallet for Futures")
st.markdown("---")

# Sidebar
st.sidebar.header("🔐 Connection")

if COINDCX_API_KEY != "YOUR_API_KEY_HERE":
    st.sidebar.success("✅ Credentials Loaded")
else:
    st.sidebar.error("❌ Update credentials!")

if st.sidebar.button("🔄 Fetch USDT Balance"):
    success, balance = get_usdt_balance()
    if success:
        st.session_state.usdt_balance = balance
        st.sidebar.success(f"✅ Balance: {balance:.6f} USDT")
        
        # Convert to INR for reference (approx)
        usdt_to_inr = balance * 83  # Approximate conversion
        st.sidebar.info(f"≈ ₹{usdt_to_inr:.2f} INR")
        
        send_alert(f"💰 <b>USDT Balance Fetched</b>\n{balance:.6f} USDT\n≈ ₹{usdt_to_inr:.2f} INR")
    else:
        st.sidebar.error(f"Error: {balance}")

st.sidebar.markdown("---")
st.sidebar.header("💼 Futures Wallet")

st.sidebar.metric("USDT Balance", f"{st.session_state.usdt_balance:.6f}")

if st.session_state.usdt_balance > 0:
    st.sidebar.success("✅ Ready to trade")
else:
    st.sidebar.warning("⚠️ Fetch balance first")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Trade Settings")

pair = st.sidebar.selectbox("Pair", ["BTC_USDT", "ETH_USDT"])
side = st.sidebar.radio("Side", ["BUY", "SELL"])
leverage = st.sidebar.slider("Leverage", 1, 10, 5)
qty = st.sidebar.number_input("Qty", value=0.001, step=0.0001, format="%.4f")

success, price = get_price(f"KC-{pair}")
if success:
    current_price = price
    st.sidebar.info(f"Current Price: {current_price:.2f}")
else:
    current_price = st.sidebar.number_input("Price (USDT)", value=67000)

st.sidebar.markdown("---")
st.sidebar.header("📊 Position")

margin_required = (qty * current_price) / leverage
pnl_per_1dollar = qty * leverage

st.sidebar.write(f"Entry: {current_price:.2f}")
st.sidebar.write(f"Margin Required: {margin_required:.6f} USDT")
st.sidebar.write(f"Position Value: {qty * current_price:.6f} USDT")
st.sidebar.write(f"P&L per $1 move: {pnl_per_1dollar:.6f} USDT")

if margin_required > st.session_state.usdt_balance:
    st.sidebar.error(f"❌ Need {margin_required:.6f} USDT")
    can_trade = False
else:
    st.sidebar.success("✅ Sufficient margin")
    can_trade = True

st.sidebar.markdown("---")

# Main
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.info(f"📊 Pair\n{pair}")
with col2:
    st.info(f"📈 Side\n{side}")
with col3:
    st.info(f"🔧 Leverage\n{leverage}x")
with col4:
    st.info(f"💹 Price\n{current_price:.2f}")

st.markdown("---")

# Test Mode
st.header("🧪 TEST MODE - Simulate Trades")

tcol1, tcol2 = st.columns(2)

with tcol1:
    if st.button("📊 Simulate Entry", use_container_width=True):
        trade = {
            'Time': datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
            'Pair': pair,
            'Side': side,
            'Entry': current_price,
            'Qty': qty,
            'Leverage': leverage,
            'Margin': margin_required,
            'Status': 'OPEN'
        }
        st.session_state.trades.append(trade)
        st.session_state.usdt_balance -= margin_required
        
        msg = f"📊 <b>SIMULATED ENTRY</b>\n"
        msg += f"Pair: {pair}\n"
        msg += f"Side: {side}\n"
        msg += f"Entry: {current_price:.2f}\n"
        msg += f"Qty: {qty:.4f}\n"
        msg += f"Leverage: {leverage}x\n"
        msg += f"Margin: {margin_required:.6f} USDT"
        
        send_alert(msg)
        st.success(f"✅ Simulated {side} entry")
        st.rerun()

with tcol2:
    if st.button("📈 Simulate Exit", use_container_width=True):
        exit_price = current_price
        if st.session_state.trades:
            last = st.session_state.trades[-1]
            if last['Status'] == 'OPEN':
                entry = last['Entry']
                q = last['Qty']
                
                if side == "BUY":
                    pnl = (exit_price - entry) * q * leverage
                else:
                    pnl = (entry - exit_price) * q * leverage
                
                last['Exit'] = exit_price
                last['P&L'] = pnl
                last['Status'] = 'CLOSED'
                
                st.session_state.usdt_balance += margin_required + pnl
                
                msg = f"📊 <b>SIMULATED EXIT</b>\n"
                msg += f"Exit: {exit_price:.2f}\n"
                msg += f"P&L: {pnl:.6f} USDT\n"
                msg += f"Status: {'✅ WIN' if pnl > 0 else '❌ LOSS'}\n"
                msg += f"Balance: {st.session_state.usdt_balance:.6f} USDT"
                
                send_alert(msg)
                st.success(f"✅ Exit | P&L: {pnl:.6f} USDT")
                st.rerun()
        else:
            st.error("❌ No open position")

st.markdown("---")

# Live Trading
st.header("🔴 LIVE FUTURES TRADING")

if not can_trade:
    st.error("❌ Insufficient margin!")
else:
    if st.button("🟢 Place REAL Futures Order", use_container_width=True):
        if COINDCX_API_KEY == "YOUR_API_KEY_HERE":
            st.error("❌ Update credentials first!")
        else:
            with st.spinner("Placing futures order..."):
                success, result = place_futures_order(pair, side, qty, leverage)
                if success:
                    st.success("✅ Futures order placed!")
                    
                    trade = {
                        'Time': datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
                        'Pair': pair,
                        'Side': side,
                        'Entry': current_price,
                        'Qty': qty,
                        'Leverage': leverage,
                        'Order ID': result.get('id', 'N/A'),
                        'Status': 'LIVE'
                    }
                    
                    st.session_state.trades.append(trade)
                    st.session_state.usdt_balance -= margin_required
                    
                    msg = f"🔴 <b>LIVE FUTURES ORDER</b>\n"
                    msg += f"Pair: {pair}\n"
                    msg += f"Side: {side}\n"
                    msg += f"Entry: {current_price:.2f}\n"
                    msg += f"Qty: {qty:.4f}\n"
                    msg += f"Leverage: {leverage}x\n"
                    msg += f"Order ID: {result.get('id', 'N/A')}"
                    
                    send_alert(msg)
                    
                    st.json(result)
                else:
                    st.error(f"❌ Error: {result}")

st.markdown("---")

# Trade History
st.header("📋 Trade History")

if st.session_state.trades:
    df = pd.DataFrame(st.session_state.trades)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Summary
    closed = [t for t in st.session_state.trades if t['Status'] == 'CLOSED']
    if closed:
        total_pnl = sum([t['P&L'] for t in closed])
        wins = len([t for t in closed if t['P&L'] > 0])
        losses = len([t for t in closed if t['P&L'] < 0])
        
        st.markdown("---")
        st.subheader("📊 Summary")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Closed Trades", len(closed))
        with col2:
            st.metric("Wins", wins)
        with col3:
            st.metric("Losses", losses)
        with col4:
            win_rate = (wins / len(closed) * 100) if closed else 0
            st.metric("Win Rate", f"{win_rate:.1f}%")
        with col5:
            st.metric("Total P&L", f"{total_pnl:.6f} USDT")
else:
    st.info("No trades yet. Start with test mode!")

