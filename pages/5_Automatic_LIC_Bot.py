import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import sys
import pytz

sys.path.append('/workspaces/dataset-from-Dhan')

from coindcx import Client
from coindcx.enums import OrderSide, FuturesOrderType
from dotenv import load_dotenv

st.set_page_config(page_title="Automatic LIC Bot", page_icon="🤖", layout="wide")
st.title("🤖 Forward Testing - LIC Trading Bot - DOGE 🐕")

IST = pytz.timezone('Asia/Kolkata')

load_dotenv(Path('/workspaces/dataset-from-Dhan/.env'), override=True)

try:
    client = Client(
        api_key=os.getenv('COINDCX_API_KEY'),
        api_secret=os.getenv('COINDCX_API_SECRET')
    )
except Exception as e:
    st.error(f"API Error: {e}")
    st.stop()

TRADES_LOG = Path('/workspaces/dataset-from-Dhan/forward_trades.json')

st.sidebar.header("⚙️ Bot Settings")

st.sidebar.subheader("💱 Currency Conversion")

exchange_rate_input = st.sidebar.text_input("USD to INR Rate", value="83")

try:
    exchange_rate = float(exchange_rate_input)
except:
    exchange_rate = 83

st.sidebar.info(f"1 USD = ₹{exchange_rate:.2f}")

st.sidebar.subheader("🎯 Pattern & Validation")

small_candle_input = st.sidebar.text_input("Small Candle Threshold (<)", value="0.000080")

try:
    small_candle_threshold = float(small_candle_input)
except:
    small_candle_threshold = 0.000080

cooldown_candles = st.sidebar.select_slider(
    "Cooldown After Trade (candles)",
    options=[0, 1, 2, 3],
    value=2
)

pattern_length = st.sidebar.select_slider(
    "Pattern Length (consecutive candles)",
    options=[3, 4, 5, 6, 7],
    value=3
)

min_body_input = st.sidebar.text_input("Min Body Size (>=)", value="0.000130")

try:
    min_body = float(min_body_input)
except:
    min_body = 0.000130

st.sidebar.success(f"""
✅ FORWARD TESTING (Live Data)
✅ USD to INR: {exchange_rate}
✅ Small Candle: < ${small_candle_threshold:.6f}
✅ Cooldown: {cooldown_candles} candles
✅ Pattern: {pattern_length} consecutive
✅ Min Body: >= ${min_body:.6f}
""")

if st.sidebar.button("🔄 Refresh Data (Get Latest Candles)", key="refresh"):
    st.rerun()

st.sidebar.markdown("---")

if st.sidebar.button("📊 View Trade History"):
    st.session_state.show_history = True

if st.sidebar.button("🗑️ Clear Trade Log"):
    if TRADES_LOG.exists():
        TRADES_LOG.unlink()
        st.sidebar.success("✅ Trade log cleared!")
        st.rerun()

def get_candles(hours=24):
    """Get LIVE/CURRENT candles only"""
    try:
        now = int(datetime.now().timestamp())
        past = int((datetime.now() - timedelta(hours=hours)).timestamp())
        candles = client.get_futures_candles(pair='B-DOGE_USDT', from_time=past, to_time=now, resolution='15')
        if candles and isinstance(candles, dict) and 'data' in candles:
            data = candles['data']
            return list(reversed(data)) if data else []
        return []
    except:
        return []

def utc_to_ist(utc_timestamp_ms):
    utc_time = datetime.fromtimestamp(utc_timestamp_ms / 1000, tz=pytz.UTC)
    ist_time = utc_time.astimezone(IST)
    return ist_time.strftime('%d-%m-%Y %H:%M:%S')

def to_inr(usd_value, rate):
    return usd_value * rate

def log_trade(trade_info):
    """Log executed trade to file"""
    trades = []
    if TRADES_LOG.exists():
        with open(TRADES_LOG, 'r') as f:
            trades = json.load(f)
    
    trades.append(trade_info)
    
    with open(TRADES_LOG, 'w') as f:
        json.dump(trades, f, indent=2)

def get_trade_history():
    """Get all executed trades"""
    if TRADES_LOG.exists():
        with open(TRADES_LOG, 'r') as f:
            return json.load(f)
    return []

st.subheader("📊 Forward Testing Status")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Mode", "🔴 LIVE")
with col2:
    st.metric("Exchange Rate", f"1 USD = ₹{exchange_rate:.2f}")
with col3:
    st.metric("Cooldown", f"{cooldown_candles} candles")
with col4:
    st.metric("Pattern", f"{pattern_length} candles")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["Live Monitoring", "Trade History", "OHLV Data"])

with tab1:
    candles = get_candles(hours=24)
    
    if candles:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Current Candles", len(candles))
        with col2:
            latest_time = utc_to_ist(candles[-1].get('time', 0))
            st.metric("Latest", latest_time)
        with col3:
            earliest_time = utc_to_ist(candles[0].get('time', 0))
            st.metric("Earliest", earliest_time)
        with col4:
            st.metric("Status", "🟢 Active")
        
        st.markdown("---")
        
        st.warning("""
        **⚠️ FORWARD TESTING MODE:**
        - Shows LIVE candles only (last 24 hours)
        - Executes trades in REAL-TIME as patterns form
        - All trades are logged to history
        - NO backtesting of past data
        """)
        
        st.markdown("---")
        
        inherited_colors = []
        inherited_flags = []
        
        for i in range(len(candles)):
            c = candles[i]
            actual_color = '🟢' if c.get('close', 0) > c.get('open', 0) else '🔴'
            body = abs(c.get('close', 0) - c.get('open', 0))
            
            if body < small_candle_threshold and i > 0:
                color_to_use = inherited_colors[i - 1]
                is_inherited = True
            else:
                color_to_use = actual_color
                is_inherited = False
            
            inherited_colors.append(color_to_use)
            inherited_flags.append(is_inherited)
        
        lic_data = []
        signal_count = 0
        total_pnl_usd = 0
        last_trade_index = -999
        executed_trades = []
        
        for i in range(len(candles)):
            c = candles[i]
            time_str = utc_to_ist(c.get('time', 0))
            open_price = c.get('open', 0)
            close_price = c.get('close', 0)
            body = abs(close_price - open_price)
            
            actual_color = '🟢' if close_price > open_price else '🔴'
            
            pattern_str = '—'
            pattern_match = '—'
            signal = '—'
            entry = '—'
            exit_p = '—'
            pnl = '—'
            inheritance_note = '—'
            cooldown_note = '—'
            status = '⏳ Waiting'
            
            if inherited_flags[i]:
                inheritance_note = f"Inherited (body < ${small_candle_threshold:.6f})"
            
            candles_since_trade = i - last_trade_index
            in_cooldown = candles_since_trade <= cooldown_candles
            
            if in_cooldown and last_trade_index >= 0:
                cooldown_note = f"🔒 Cooldown ({candles_since_trade}/{cooldown_candles})"
            
            if i >= pattern_length - 1:
                pattern_colors = []
                for j in range(pattern_length):
                    pattern_colors.append(inherited_colors[i - pattern_length + 1 + j])
                
                pattern_str = ''.join(pattern_colors)
                
                if len(set(pattern_colors)) == 1:
                    pattern_match = f'✅ ALL {pattern_colors[-1]}'
                    
                    if body >= min_body:
                        if not in_cooldown:
                            if pattern_colors[-1] == '🔴':
                                signal = 'LONG'
                                signal_count += 1
                                last_trade_index = i
                                status = '🟢 EXECUTED'
                                
                                if i + 1 < len(candles):
                                    next_c = candles[i + 1]
                                    entry_val = next_c.get('open', 0)
                                    exit_val = next_c.get('close', 0)
                                    entry = f"${entry_val:.6f}"
                                    exit_p = f"${exit_val:.6f}"
                                    
                                    pnl_usd = (exit_val - entry_val) * 100
                                    pnl_inr = to_inr(pnl_usd, exchange_rate)
                                    pnl_sym = '✅' if pnl_usd > 0 else '❌'
                                    pnl = f"{pnl_sym} ${pnl_usd:.4f}\n(₹{pnl_inr:.2f})"
                                    total_pnl_usd += pnl_usd
                                    
                                    # ← Log trade
                                    trade_log = {
                                        'time': time_str,
                                        'signal': 'LONG',
                                        'entry': entry_val,
                                        'exit': exit_val,
                                        'pnl_usd': pnl_usd,
                                        'pnl_inr': pnl_inr,
                                        'status': 'Executed'
                                    }
                                    executed_trades.append(trade_log)
                                    log_trade(trade_log)
                                else:
                                    entry = "NEXT CANDLE PENDING"
                                    status = '⏳ Awaiting next candle'
                            
                            else:
                                signal = 'SHORT'
                                signal_count += 1
                                last_trade_index = i
                                status = '🟢 EXECUTED'
                                
                                if i + 1 < len(candles):
                                    next_c = candles[i + 1]
                                    entry_val = next_c.get('open', 0)
                                    exit_val = next_c.get('close', 0)
                                    entry = f"${entry_val:.6f}"
                                    exit_p = f"${exit_val:.6f}"
                                    
                                    pnl_usd = (entry_val - exit_val) * 100
                                    pnl_inr = to_inr(pnl_usd, exchange_rate)
                                    pnl_sym = '✅' if pnl_usd > 0 else '❌'
                                    pnl = f"{pnl_sym} ${pnl_usd:.4f}\n(₹{pnl_inr:.2f})"
                                    total_pnl_usd += pnl_usd
                                    
                                    # ← Log trade
                                    trade_log = {
                                        'time': time_str,
                                        'signal': 'SHORT',
                                        'entry': entry_val,
                                        'exit': exit_val,
                                        'pnl_usd': pnl_usd,
                                        'pnl_inr': pnl_inr,
                                        'status': 'Executed'
                                    }
                                    executed_trades.append(trade_log)
                                    log_trade(trade_log)
                                else:
                                    entry = "NEXT CANDLE PENDING"
                                    status = '⏳ Awaiting next candle'
                        else:
                            pattern_match = f'⏸️ {pattern_match} (cooldown)'
                            status = '🔒 In Cooldown'
                    else:
                        pattern_match = f'❌ TOO SMALL (${body:.6f} < ${min_body:.6f})'
                        status = '❌ Body too small'
                else:
                    pattern_match = f'❌ MIXED'
                    status = '❌ Pattern mixed'
            
            lic_data.append({
                'Time': time_str,
                'Open': f"${open_price:.6f}",
                'Close': f"${close_price:.6f}",
                'Body': f"${body:.6f}",
                'Actual': actual_color,
                'Adopted': inherited_colors[i],
                'Inherit': inheritance_note,
                'Last N': pattern_str,
                'Check': pattern_match,
                'Cooldown': cooldown_note,
                'Signal': signal,
                'Entry': entry,
                'Exit': exit_p,
                'P&L': pnl,
                'Status': status
            })
        
        st.markdown("---")
        
        total_pnl_inr = to_inr(total_pnl_usd, exchange_rate)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Trades Executed", signal_count)
        with col2:
            st.write(f"**Total P&L**")
            sym = "✅" if total_pnl_usd > 0 else "❌"
            st.write(f"{sym} ${total_pnl_usd:.4f}")
            st.write(f"(₹{total_pnl_inr:.2f})")
        with col3:
            st.metric("Last Updated", utc_to_ist(candles[-1].get('time', 0)))
        with col4:
            st.metric("Exchange", f"1 USD = ₹{exchange_rate:.2f}")
        with col5:
            st.metric("Mode", "🔴 LIVE")
        
        st.markdown("---")
        
        df = pd.DataFrame(lic_data)
        st.dataframe(df, use_container_width=True, height=500)

with tab2:
    st.subheader("📜 Trade History")
    
    history = get_trade_history()
    
    if history:
        total_hist_pnl_usd = sum(t.get('pnl_usd', 0) for t in history)
        total_hist_pnl_inr = sum(t.get('pnl_inr', 0) for t in history)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Trades", len(history))
        with col2:
            sym = "✅" if total_hist_pnl_usd > 0 else "❌"
            st.write(f"**Total P&L**")
            st.write(f"{sym} ${total_hist_pnl_usd:.4f}")
            st.write(f"(₹{total_hist_pnl_inr:.2f})")
        with col3:
            wins = len([t for t in history if t.get('pnl_usd', 0) > 0])
            wr = (wins / len(history) * 100) if history else 0
            st.metric("Win Rate", f"{wr:.1f}% ({wins}/{len(history)})")
        
        st.markdown("---")
        
        # Display trades table
        trades_df = pd.DataFrame(history)
        st.dataframe(trades_df, use_container_width=True)
        
        # Download history
        csv = trades_df.to_csv(index=False)
        st.download_button("📥 Download Trade History", csv, "forward_trade_history.csv", "text/csv")
    else:
        st.info("No trades executed yet. Waiting for signal conditions...")

with tab3:
    candles = get_candles(hours=24)
    if candles:
        ohlv = []
        for c in candles:
            ohlv.append({'Time': utc_to_ist(c.get('time', 0)), 'Open': f"${c.get('open', 0):.6f}", 'High': f"${c.get('high', 0):.6f}", 'Low': f"${c.get('low', 0):.6f}", 'Close': f"${c.get('close', 0):.6f}", 'Body': f"${abs(c.get('close', 0) - c.get('open', 0)):.6f}"})
        df_o = pd.DataFrame(ohlv)
        st.dataframe(df_o, use_container_width=True, height=400)

st.success("🐕 Forward Testing Active!")

