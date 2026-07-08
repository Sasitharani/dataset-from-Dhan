import os
from dotenv import load_dotenv
import streamlit as st
import requests
from coindcx import Client
from datetime import datetime
import pandas as pd

load_dotenv()

API_KEY = os.getenv('COINDCX_API_KEY')
API_SECRET = os.getenv('COINDCX_API_SECRET')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT = os.getenv('TELEGRAM_CHAT_ID')

st.set_page_config(page_title="Futures Simulator", page_icon="💰", layout="wide")

if 'trades' not in st.session_state:
    st.session_state.trades = []
if 'simulated_balance' not in st.session_state:
    st.session_state.simulated_balance = 1000  # Start with simulated ₹1000
if 'real_balance' not in st.session_state:
    st.session_state.real_balance = 0.572487

def send_alert(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT, "text": msg, "parse_mode": "HTML"}
        requests.post(url, data=data, timeout=5)
        return True
    except:
        return False

def get_real_balance():
    try:
        client = Client(api_key=API_KEY, api_secret=API_SECRET)
        balances = client.get_balances()
        for b in balances:
            if b['currency'] == 'USDT':
                return float(b['balance'])
        return 0
    except:
        return 0

def get_price(pair):
    try:
        client = Client(api_key=API_KEY, api_secret=API_SECRET)
        candles = client.get_candles(pair=pair, interval="1m", limit=1)
        if candles:
            return True, candles[0]['close']
        return False, "No data"
    except Exception as e:
        return False, str(e)

# UI
st.title("💰 CoinDCX Futures Simulator")
st.markdown("**Simulate trading while you add funds to your account**")
st.markdown("---")

# Sidebar
st.sidebar.header("🔐 Account Status")

st.sidebar.warning("⚠️ INSUFFICIENT BALANCE")
st.sidebar.write(f"Real Balance: 0.572487 USDT (₹47.52)")
st.sidebar.write(f"Minimum needed: 10 USDT (₹830)")
st.sidebar.write(f"Shortfall: ₹750")

if st.sidebar.button("🔄 Check Real Balance"):
    real = get_real_balance()
    st.session_state.real_balance = real
    if real >= 10:
        st.sidebar.success(f"✅ NOW CAN TRADE! {real:.6f} USDT")
        send_alert(f"💰 Balance sufficient! {real:.6f} USDT")
    else:
        st.sidebar.error(f"❌ Still low: {real:.6f} USDT")

st.sidebar.markdown("---")
st.sidebar.header("💼 Simulator Wallet")

st.sidebar.metric("Simulated Balance", f"₹{st.session_state.simulated_balance:.2f}")
st.sidebar.info("Practice trading with simulated ₹1000")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Trade Settings")

pair = st.sidebar.selectbox("Pair", ["BTC_USDT", "ETH_USDT"])
side = st.sidebar.radio("Side", ["BUY", "SELL"])
leverage = st.sidebar.slider("Leverage", 1, 10, 5)

success, price = get_price(f"KC-{pair}")
if success:
    current_price = price
    st.sidebar.info(f"Price: ₹{current_price * 83:.2f} (~{current_price:.2f} USDT)")
else:
    current_price = st.sidebar.number_input("Price (USDT)", value=63219)

# In INR for easier understanding
price_inr = current_price * 83

qty = st.sidebar.number_input("Qty", value=0.001, step=0.0001, format="%.6f")
margin_required = (qty * price_inr) / leverage

st.sidebar.markdown("---")
st.sidebar.header("📊 Order Details")

st.sidebar.write(f"Price: ₹{price_inr:.2f}")
st.sidebar.write(f"Qty: {qty}")
st.sidebar.write(f"Leverage: {leverage}x")
st.sidebar.write(f"Margin: ₹{margin_required:.2f}")

if margin_required <= st.session_state.simulated_balance:
    st.sidebar.success("✅ Can trade in simulator")
    can_trade = True
else:
    st.sidebar.error(f"❌ Need ₹{margin_required - st.session_state.simulated_balance:.2f} more")
    can_trade = False

st.sidebar.markdown("---")

# Main
col1, col2, col3 = st.columns(3)
with col1:
    st.info(f"Pair\n{pair}")
with col2:
    st.info(f"Side\n{side}")
with col3:
    st.warning(f"Price\n₹{price_inr:.2f}")

st.markdown("---")

# Status
st.header("📊 Account Status")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Real Balance", f"{st.session_state.real_balance:.6f} USDT")
with col2:
    st.metric("Status", "⚠️ TOO LOW")
with col3:
    st.metric("Action", "📱 Add Funds")

st.markdown("---")

# Simulator
st.header("🧪 Futures Simulator (Practice Mode)")

st.info("Practice trading with simulated balance. Once you add ₹750+ to reach 10 USDT, you can trade live!")

tcol1, tcol2 = st.columns(2)

with tcol1:
    if st.button("📊 Simulate Entry", use_container_width=True):
        if can_trade:
            trade = {
                'Time': datetime.now().strftime('%d-%m-%Y %H:%M:%S'),
                'Pair': f'B-{pair}',
                'Side': side,
                'Price': price_inr,
                'Qty': qty,
                'Leverage': leverage,
                'Margin': margin_required,
                'Entry Price': price_inr,
                'Status': 'OPEN'
            }
            st.session_state.trades.append(trade)
            st.session_state.simulated_balance -= margin_required
            
            msg = f"📊 <b>SIMULATOR ENTRY</b>\n"
            msg += f"Pair: {pair}\n"
            msg += f"Side: {side}\n"
            msg += f"Qty: {qty}\n"
            msg += f"Entry: ₹{price_inr:.2f}\n"
            msg += f"Leverage: {leverage}x"
            
            send_alert(msg)
            st.success(f"✅ Entered {side}")
            st.rerun()
        else:
            st.error("❌ Can't afford")

with tcol2:
    if st.button("📈 Simulate Exit", use_container_width=True):
        if st.session_state.trades:
            last = st.session_state.trades[-1]
            if last['Status'] == 'OPEN':
                entry = last['Entry Price']
                q = last['Qty']
                l = last['Leverage']
                
                if side == "BUY":
                    pnl = (price_inr - entry) * q * l
                else:
                    pnl = (entry - price_inr) * q * l
                
                last['Exit Price'] = price_inr
                last['P&L'] = pnl
                last['Status'] = 'CLOSED'
                
                st.session_state.simulated_balance += margin_required + pnl
                
                msg = f"📊 <b>SIMULATOR EXIT</b>\n"
                msg += f"Exit: ₹{price_inr:.2f}\n"
                msg += f"P&L: ₹{pnl:.2f}\n"
                msg += f"Status: {'✅ WIN' if pnl > 0 else '❌ LOSS'}"
                
                send_alert(msg)
                st.success(f"✅ P&L: ₹{pnl:.2f}")
                st.rerun()

st.markdown("---")

# History
st.header("📋 Simulation History")

if st.session_state.trades:
    df = pd.DataFrame(st.session_state.trades)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    closed = [t for t in st.session_state.trades if t['Status'] == 'CLOSED']
    if closed:
        total_pnl = sum([t['P&L'] for t in closed])
        wins = len([t for t in closed if t['P&L'] > 0])
        losses = len([t for t in closed if t['P&L'] < 0])
        
        st.markdown("---")
        st.subheader("📊 Simulator Summary")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Trades", len(closed))
        with col2:
            st.metric("Wins", wins)
        with col3:
            st.metric("Losses", losses)
        with col4:
            wr = (wins / len(closed) * 100) if closed else 0
            st.metric("Win Rate", f"{wr:.1f}%")
        with col5:
            st.metric("Total P&L", f"₹{total_pnl:.2f}")
else:
    st.info("No trades yet. Start practicing!")

st.markdown("---")

# Instructions
st.header("📱 How to Add Funds")

st.markdown("""
### Steps to add USDT:

1. **Open CoinDCX App** (Mobile or Web)
2. **Tap Wallet** (bottom navigation)
3. **Tap Deposit**
4. **Select USDT** or **INR** (INR easier)
5. **Enter amount: ₹800-1000**
6. **Choose payment:**
   - UPI (fastest - 1 min)
   - Bank transfer
   - Net banking
7. **Complete payment**
8. **Fund will appear in 5-30 mins**

### Check balance:
- Once you add, you'll have ~10 USDT minimum
- Come back here and click "Check Real Balance"
- Once it shows ≥ 10 USDT, live trading is enabled!

### Benefits:
- ✅ Practice in simulator now
- ✅ Trade live once funds added
- ✅ Your API key is ready
- ✅ All configuration done
""")

