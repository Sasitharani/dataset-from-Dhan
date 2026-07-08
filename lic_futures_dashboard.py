import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from coindcx import Client

st.set_page_config(page_title="LIC Bot Dashboard", page_icon="🤖", layout="wide")

load_dotenv()

API_KEY = os.getenv('COINDCX_API_KEY')
API_SECRET = os.getenv('COINDCX_API_SECRET')

TRADES_FILE = '/workspaces/dataset-from-Dhan/trades_data.json'
BOT_STATE_FILE = '/workspaces/dataset-from-Dhan/bot_state.json'
ANALYSIS_FILE = '/workspaces/dataset-from-Dhan/analysis_table.json'
CONFIG_FILE = '/workspaces/dataset-from-Dhan/bot_config.json'

def get_candles_from_api(pair, interval, limit=1000):
    """Fetch candles from CoinDCX API"""
    try:
        client = Client(api_key=API_KEY, api_secret=API_SECRET)
        candles = client.get_candles(pair=pair, interval=interval, limit=limit)
        return candles
    except Exception as e:
        st.error(f"Error fetching candles: {e}")
        return None

def get_color(candle):
    """Get candle color"""
    return '🟢' if candle['close'] > candle['open'] else '🔴'

def get_body(candle):
    """Get candle body size"""
    return abs(candle['close'] - candle['open'])

def detect_lic(candles, threshold, idx):
    """Detect LIC at index"""
    if idx < 0 or idx >= len(candles):
        return False, None, 0
    
    c1 = candles[idx]
    body = get_body(c1)
    color = get_color(c1)
    
    is_lic = body >= threshold
    
    return is_lic, color, body

def check_trend(candles, idx):
    """Check if 3 candles from idx are same color"""
    if idx < 2 or idx >= len(candles):
        return False, None
    
    c1_color = get_color(candles[idx])
    c2_color = get_color(candles[idx-1])
    c3_color = get_color(candles[idx-2])
    
    colors = [c1_color, c2_color, c3_color]
    
    is_trend = colors[0] == colors[1] == colors[2]
    
    return is_trend, colors[0]

def analyze_all_candles(pair, interval, threshold, from_date, to_date, leverage):
    """Analyze ALL candles in date range with CORRECT exit logic"""
    st.info(f"📥 Fetching all {pair} candles for {interval}... (Threshold: {threshold})")
    
    candles = get_candles_from_api(pair, interval, limit=1000)
    if not candles:
        st.error("No candles fetched")
        return []
    
    # Reverse to get oldest first
    candles = list(reversed(candles))
    
    analysis_rows = []
    
    for idx, candle in enumerate(candles):
        # Get timestamp from candle
        try:
            ts = datetime.fromtimestamp(candle['time'] / 1000) if 'time' in candle else datetime.now()
        except:
            ts = datetime.now()
        
        candle_date = ts.date()
        
        # Filter by date range
        if candle_date < from_date or candle_date > to_date:
            continue
        
        timestamp = ts.strftime('%d-%m-%Y %H:%M:%S')
        open_price = candle['open']
        close_price = candle['close']
        body = get_body(candle)
        color = get_color(candle)
        
        # Detect LIC and Trend
        if idx >= 2 and idx < len(candles) - 1:
            # Get C1 candle (current)
            is_lic, lic_color, lic_body = detect_lic(candles, threshold, idx)
            
            # Get trend from C1 and 2 previous
            trend_valid, trend_color = check_trend(candles, idx)
            
            # Pattern (3 colors) - C1, C0 (previous), C-1 (2 back)
            c1_color = get_color(candles[idx])
            c0_color = get_color(candles[idx-1])
            cm1_color = get_color(candles[idx-2])
            pattern = f"{c1_color}{c0_color}{cm1_color}"
            
            # ✅ NEW LOGIC: Only show LIC ✅ if BOTH LIC + TREND are confirmed
            combined_lic = is_lic and trend_valid
            lic_status = '✅' if combined_lic else '❌'
            trend_status = '✅' if trend_valid else '❌'
            
            # Signal only if BOTH LIC is true AND trend is valid AND colors match
            signal = '❌'
            entry = '-'
            exit_price = '-'
            qty = '-'
            pnl = '-'
            
            # Signal triggered when:
            # 1. Body >= threshold (LIC detected)
            # 2. Trend confirmed (3 same colors)
            # 3. LIC color == Trend color
            if is_lic and trend_valid and lic_color == trend_color:
                signal = 'SHORT' if lic_color == '🟢' else 'LONG'
                qty = '0.001'
                
                # Entry = C2 Open (NEXT candle's open)
                # Exit = C2 Close (NEXT candle's close)
                
                if idx + 1 < len(candles):
                    c2 = candles[idx + 1]
                    entry_price = c2['open']
                    exit_price_val = c2['close']
                    
                    entry = f"{entry_price:.2f}"
                    exit_price = f"{exit_price_val:.2f}"
                    
                    # Calculate P&L with leverage
                    qty_val = 0.001
                    
                    if signal == 'LONG':
                        pnl_calc = (exit_price_val - entry_price) * qty_val * leverage
                    else:  # SHORT
                        pnl_calc = (entry_price - exit_price_val) * qty_val * leverage
                    
                    pnl = f"₹{pnl_calc:.2f}"
                    
                    if pnl_calc > 0:
                        pnl = f"✅ {pnl}"
                    elif pnl_calc < 0:
                        pnl = f"❌ {pnl}"
                    else:
                        pnl = f"⚪ {pnl}"
                else:
                    entry = '-'
                    exit_price = '-'
                    pnl = '-'
        else:
            lic_status = '?'
            trend_status = '?'
            pattern = '?'
            signal = '?'
            entry = '-'
            exit_price = '-'
            qty = '-'
            pnl = '-'
        
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
            'Exit': exit_price,
            'Qty': qty,
            'P&L': pnl,
        }
        
        analysis_rows.append(row)
    
    return analysis_rows

def load_trades():
    if Path(TRADES_FILE).exists():
        with open(TRADES_FILE, 'r') as f:
            return json.load(f)
    return []

def load_state():
    if Path(BOT_STATE_FILE).exists():
        with open(BOT_STATE_FILE, 'r') as f:
            return json.load(f)
    return {'balance': 1000}

def load_config():
    if Path(CONFIG_FILE).exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        'lic_threshold': 300,
        'check_interval': 60,
        'leverage': 5,
        'interval': '5m',
        'pairs': ['KC-BTC_USDT', 'KC-ETH_USDT']
    }

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=2)

# SIDEBAR
with st.sidebar:
    st.header("⚙️ BOT CONFIG")
    
    cfg = load_config()
    
    st.subheader("📊 Pairs")
    pairs = st.multiselect(
        "Select pairs:",
        ['KC-BTC_USDT', 'KC-ETH_USDT'],
        default=cfg.get('pairs', ['KC-BTC_USDT', 'KC-ETH_USDT'])
    )
    
    st.subheader("⏱️ Timeframe")
    interval = st.selectbox(
        "Interval:",
        ['1m', '5m', '15m', '1h', '4h'],
        index=['1m', '5m', '15m', '1h', '4h'].index(cfg.get('interval', '5m'))
    )
    
    st.subheader("🎯 LIC Threshold")
    lic_threshold = st.slider("Min body:", 100, 1000, cfg.get('lic_threshold', 300), 50)
    st.write(f"**Current: {lic_threshold}**")
    
    st.subheader("⏳ Check Interval")
    check_interval = st.slider("Check every (sec):", 30, 300, cfg.get('check_interval', 60), 10)
    
    st.subheader("🔧 Leverage")
    leverage = st.slider("Leverage:", 1, 10, cfg.get('leverage', 5), 1)
    
    if st.button("💾 Save"):
        save_config({
            'pairs': pairs,
            'interval': interval,
            'lic_threshold': lic_threshold,
            'check_interval': check_interval,
            'leverage': leverage
        })
        st.success("✅ Saved!")
    
    st.markdown("---")
    st.subheader("📈 Status")
    state = load_state()
    st.metric("Balance", f"₹{state['balance']:.2f}")
    
    trades = load_trades()
    open_c = len([t for t in trades if t['status'] == 'OPEN'])
    closed_c = len([t for t in trades if t['status'] == 'CLOSED'])
    
    st.write(f"Open: **{open_c}**")
    st.write(f"Closed: **{closed_c}**")

# MAIN
st.title("🤖 LIC 24/7 Futures Bot")
st.markdown(f"⏰ {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")

if st.button("🔄 Refresh"):
    st.rerun()

st.markdown("---")

# METRICS
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("💰 Balance", f"₹{state['balance']:.2f}")
with col2:
    st.metric("📈 Open", open_c)
with col3:
    st.metric("✅ Closed", closed_c)
with col4:
    wins = len([t for t in trades if t['status'] == 'CLOSED' and t.get('pnl', 0) > 0])
    st.metric("Wins", wins)
with col5:
    total_pnl = sum([t.get('pnl', 0) for t in trades if t['status'] == 'CLOSED'])
    st.metric("P&L", f"₹{total_pnl:.2f}")

st.markdown("---")

# ANALYSIS TABLE WITH DATE RANGE & HISTORICAL CANDLES
st.header("📊 Analysis Table - ALL Candles with Exit & P&L")

col1, col2, col3, col4 = st.columns(4)

with col1:
    from_date = st.date_input("From:", datetime.now().date() - timedelta(days=7))

with col2:
    to_date = st.date_input("To:", datetime.now().date())

with col3:
    selected_pair = st.selectbox("Pair:", pairs)

with col4:
    if st.button("🔍 Fetch & Analyze"):
        st.session_state.analyze_all = True
    analyze_all = st.session_state.get('analyze_all', False)

if analyze_all:
    with st.spinner(f"📥 Fetching all {selected_pair} candles (Threshold: {lic_threshold})..."):
        all_rows = analyze_all_candles(selected_pair, interval, lic_threshold, from_date, to_date, leverage)
    
    if all_rows:
        df = pd.DataFrame(all_rows)
        
        cols_to_show = ['Time', 'Pair', 'Open', 'Close', 'Body', 'Color', 'Pattern', 'LIC', 'Trend', 'Signal', 'Entry', 'Exit', 'Qty', 'P&L']
        display_df = df[cols_to_show].copy()
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=600
        )
        
        signals = df[df['Signal'] != '❌']
        longs = len([s for s in signals['Signal'] if s == 'LONG'])
        shorts = len([s for s in signals['Signal'] if s == 'SHORT'])
        
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Candles", len(df))
        with col2:
            st.metric("Signals Found", len(signals))
        with col3:
            st.metric("LONG Signals", longs)
        with col4:
            st.metric("SHORT Signals", shorts)
        
        # Calculate P&L stats
        signal_rows = df[df['Signal'] != '❌']
        if len(signal_rows) > 0:
            st.markdown("---")
            st.subheader("📊 Signal Performance")
            
            wins = len([p for p in signal_rows['P&L'] if '✅' in str(p)])
            losses = len([p for p in signal_rows['P&L'] if '❌' in str(p)])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Wins ✅", wins)
            with col2:
                st.metric("Losses ❌", losses)
            with col3:
                wr = (wins / len(signal_rows) * 100) if len(signal_rows) > 0 else 0
                st.metric("Win Rate", f"{wr:.1f}%")
        
        # Download CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"analysis_{selected_pair}_{from_date}_{to_date}.csv",
            mime="text/csv"
        )
    else:
        st.warning(f"No candles found for {selected_pair} between {from_date} and {to_date}")

st.markdown("---")

# SETTINGS
st.header("⚙️ Current Config")
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.info(f"**Pairs**\n{', '.join(pairs)}")
with col2:
    st.info(f"**Interval**\n{interval}")
with col3:
    st.info(f"**Threshold**\n{lic_threshold}")
with col4:
    st.info(f"**Check**\n{check_interval}s")
with col5:
    st.info(f"**Leverage**\n{leverage}x")

st.markdown("---")

# OPEN TRADES
if open_c > 0:
    st.header(f"📈 Open Trades ({open_c})")
    for t in trades:
        if t['status'] == 'OPEN':
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**#{t['id']} {t['pair']}**\nSide: {t['side']}")
            with col2:
                st.write(f"Entry: ₹{t['entry_price'] * 83:.2f}\nQty: {t['qty']}")
            with col3:
                st.write(f"SL: ₹{t['sl_price'] * 83:.2f}\nMargin: ₹{t['margin']:.2f}")
            st.divider()

# CLOSED TRADES
if closed_c > 0:
    st.header(f"✅ Closed Trades ({closed_c})")
    
    table_data = []
    for t in trades:
        if t['status'] == 'CLOSED':
            table_data.append({
                'ID': f"#{t['id']}",
                'Pair': t['pair'],
                'Side': t['side'],
                'Entry': f"₹{t['entry_price'] * 83:.2f}",
                'Exit': f"₹{t['exit_price'] * 83:.2f}",
                'P&L': f"₹{t['pnl']:.2f}",
                'Result': '✅ WIN' if t['pnl'] > 0 else '❌ LOSS'
            })
    
    if table_data:
        df_closed = pd.DataFrame(table_data)
        st.dataframe(df_closed, use_container_width=True, hide_index=True)

