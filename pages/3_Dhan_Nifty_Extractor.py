import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
sys.path.append('/workspaces/dataset-from-Dhan')
from api_client import dhan, DHAN_NIFTY_50_SECURITY_ID

st.set_page_config(page_title="Dhan NIFTY Extractor", page_icon="📈", layout="wide")

st.title("📈 Dhan NIFTY 50 Extractor with LIC Detection")

def get_body(candle):
    return abs(candle.get('close', 0) - candle.get('open', 0))

def get_color(candle):
    return '🟢' if candle.get('close', 0) > candle.get('open', 0) else '🔴'

def check_trend(candles_list, idx):
    """Check if 3 candles are same color"""
    if idx < 2 or idx >= len(candles_list):
        return False, None
    
    c1_color = get_color(candles_list[idx])
    c2_color = get_color(candles_list[idx-1])
    c3_color = get_color(candles_list[idx-2])
    
    if c1_color == c2_color == c3_color:
        return True, c1_color
    return False, None

# Sidebar
st.sidebar.header("📊 Dhan NIFTY Settings")
st.sidebar.info(f"✅ Security ID: {DHAN_NIFTY_50_SECURITY_ID}")

interval = st.sidebar.selectbox("Interval:", ["1", "5", "15", "25", "60"])
threshold = st.sidebar.slider("LIC Threshold:", 10, 500, 50, 10)
leverage = st.sidebar.slider("Leverage:", 1, 10, 5, 1)

st.sidebar.markdown("---")

col1, col2 = st.sidebar.columns(2)
with col1:
    from_date = st.date_input("From Date:", datetime.now().date() - timedelta(days=7))
with col2:
    to_date = st.date_input("To Date:", datetime.now().date())

st.sidebar.markdown("---")

if st.sidebar.button("📥 Extract NIFTY Data"):
    st.session_state.extract = True

# MAIN
if st.session_state.get('extract', False):
    with st.spinner("📡 Fetching NIFTY 50 data from Dhan..."):
        try:
            from_date_str = from_date.strftime('%Y-%m-%d')
            to_date_str = to_date.strftime('%Y-%m-%d')
            
            st.info(f"🔍 Fetching {DHAN_NIFTY_50_SECURITY_ID} | {interval}min | {from_date_str} to {to_date_str}")
            
            candles = dhan.get_candles(
                security_id=DHAN_NIFTY_50_SECURITY_ID,
                interval=interval,
                from_date=from_date_str,
                to_date=to_date_str
            )
            
            if candles and len(candles) > 0:
                st.success(f"✅ Fetched {len(candles)} candles")
                
                # ==================== TABLE 1: BASIC OHLCV + LIC ====================
                st.markdown("---")
                st.subheader("📋 Table 1: OHLCV + LIC Detection")
                
                data1 = []
                for i, candle in enumerate(candles):
                    body = get_body(candle)
                    color = get_color(candle)
                    is_lic = body >= threshold
                    
                    data1.append({
                        'Time': datetime.fromtimestamp(candle.get('timestamp', 0)).strftime('%d-%m-%Y %H:%M:%S'),
                        'Open': f"{candle.get('open', 0):.2f}",
                        'High': f"{candle.get('high', 0):.2f}",
                        'Low': f"{candle.get('low', 0):.2f}",
                        'Close': f"{candle.get('close', 0):.2f}",
                        'Body': f"{body:.2f}",
                        'Color': color,
                        'Volume': candle.get('volume', 0),
                        'LIC': '✅' if is_lic else '❌',
                    })
                
                df1 = pd.DataFrame(data1)
                st.dataframe(df1, use_container_width=True, height=400)
                
                # Download Table 1
                csv1 = df1.to_csv(index=False)
                st.download_button(
                    label="📥 Download Table 1 CSV",
                    data=csv1,
                    file_name=f"NIFTY_OHLCV_{interval}min_{from_date}_{to_date}.csv",
                    mime="text/csv",
                    key="csv1"
                )
                
                # ==================== TABLE 2: LIC + TREND + ENTRY/EXIT/P&L ====================
                st.markdown("---")
                st.subheader("📊 Table 2: LIC Strategy with Entry/Exit/P&L")
                
                data2 = []
                for i, candle in enumerate(candles):
                    body = get_body(candle)
                    color = get_color(candle)
                    is_lic = body >= threshold
                    
                    trend_valid, trend_color = check_trend(candles, i)
                    
                    # Pattern (3 colors)
                    c1_color = get_color(candles[i])
                    c2_color = get_color(candles[i-1]) if i > 0 else '?'
                    c3_color = get_color(candles[i-2]) if i > 1 else '?'
                    pattern = f"{c1_color}{c2_color}{c3_color}"
                    
                    signal = '❌'
                    entry = '-'
                    exit_price = '-'
                    pnl = '-'
                    
                    # Signal if LIC + Trend + Colors match
                    if is_lic and trend_valid and color == trend_color:
                        signal = 'SHORT' if color == '🟢' else 'LONG'
                        
                        # Entry = next candle's open
                        if i + 1 < len(candles):
                            c_next = candles[i + 1]
                            entry_price = c_next.get('open', 0)
                            exit_price_val = c_next.get('close', 0)
                            
                            entry = f"{entry_price:.2f}"
                            exit_price = f"{exit_price_val:.2f}"
                            
                            # Calculate P&L
                            qty_val = 0.001
                            if signal == 'LONG':
                                pnl_calc = (exit_price_val - entry_price) * qty_val * leverage
                            else:
                                pnl_calc = (entry_price - exit_price_val) * qty_val * leverage
                            
                            pnl = f"₹{pnl_calc:.2f}"
                            if pnl_calc > 0:
                                pnl = f"✅ {pnl}"
                            elif pnl_calc < 0:
                                pnl = f"❌ {pnl}"
                    
                    data2.append({
                        'Time': datetime.fromtimestamp(candle.get('timestamp', 0)).strftime('%d-%m-%Y %H:%M:%S'),
                        'Open': f"{candle.get('open', 0):.2f}",
                        'Close': f"{candle.get('close', 0):.2f}",
                        'Body': f"{body:.2f}",
                        'Color': color,
                        'Pattern': pattern,
                        'LIC': '✅' if is_lic else '❌',
                        'Trend': '✅' if trend_valid else '❌',
                        'Signal': signal,
                        'Entry': entry,
                        'Exit': exit_price,
                        'Qty': '0.001' if signal != '❌' else '-',
                        'P&L': pnl,
                    })
                
                df2 = pd.DataFrame(data2)
                st.dataframe(df2, use_container_width=True, height=400)
                
                # Download Table 2
                csv2 = df2.to_csv(index=False)
                st.download_button(
                    label="📥 Download Table 2 CSV",
                    data=csv2,
                    file_name=f"NIFTY_LIC_Strategy_{interval}min_{from_date}_{to_date}.csv",
                    mime="text/csv",
                    key="csv2"
                )
                
                # ==================== STATISTICS ====================
                st.markdown("---")
                st.subheader("📊 Statistics")
                
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Total Candles", len(df2))
                with col2:
                    signals = len([d for d in data2 if d['Signal'] != '❌'])
                    st.metric("Signals Found", signals)
                with col3:
                    longs = len([d for d in data2 if d['Signal'] == 'LONG'])
                    st.metric("LONG Signals", longs)
                with col4:
                    shorts = len([d for d in data2 if d['Signal'] == 'SHORT'])
                    st.metric("SHORT Signals", shorts)
                with col5:
                    wins = len([d for d in data2 if '✅' in str(d['P&L'])])
                    st.metric("Wins", wins)
                
            else:
                st.warning("❌ No data returned")
                
        except Exception as e:
            st.error(f"❌ Error: {e}")
            import traceback
            st.error(traceback.format_exc())

