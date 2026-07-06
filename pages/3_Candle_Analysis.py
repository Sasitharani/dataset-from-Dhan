import streamlit as st
import pandas as pd

st.set_page_config(page_title="Candle Analysis", layout="wide")

st.title("📊 Candle Analysis - LIC→LOC Detection")
st.markdown("With Stop-Loss & Risk Management")

st.header("📁 Upload CSV Data")

uploaded_file = st.file_uploader("Upload your Nifty 15-min CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file, index_col=0)
    df.index = pd.to_datetime(df.index, format='ISO8601')
    
    st.success(f"✅ Loaded {len(df)} candles")
    
    st.write("---")
    st.header("📅 Data Range")
    st.write(f"**From:** {df.index[0]}")
    st.write(f"**To:** {df.index[-1]}")
    
    st.write("---")
    st.header("⚙️ Risk Management Settings")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        max_loss_per_trade = st.number_input(
            "Max Loss Per Trade (₹):",
            value=500,
            step=100
        )
    with col2:
        max_daily_loss = st.number_input(
            "Max Daily Loss (₹):",
            value=2000,
            step=500
        )
    with col3:
        capital = st.number_input(
            "Account Capital (₹):",
            value=50000,
            step=10000
        )
    
    st.write("---")
    st.header("🎯 Filter Options")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        retracement_filter = st.selectbox(
            "Filter by Retracement:",
            ["All", "YES", "NO"]
        )
    
    with col2:
        trade_type_filter = st.selectbox(
            "Filter by Trade Type:",
            ["All", "LONG (C1 RED)", "SHORT (C1 GREEN)"]
        )
    
    with col3:
        show_stopped = st.selectbox(
            "Show Stopped Trades:",
            ["No (Only Valid Trades)", "Yes (All)"]
        )
    
    st.write("---")
    
    if st.button("🚀 Analyze All Candle Pairs", use_container_width=True):
        
        st.header("📋 Candle-by-Candle Analysis")
        
        analysis = []
        cumulative_pl = 0
        daily_loss = 0
        trades_executed = 0
        
        for i in range(len(df) - 1):
            candle1_high = df['high'].iloc[i]
            candle1_low = df['low'].iloc[i]
            candle1_open = df['open'].iloc[i]
            candle1_close = df['close'].iloc[i]
            candle1_size = abs(candle1_high - candle1_low)
            candle1_time = df.index[i]
            
            candle2_high = df['high'].iloc[i+1]
            candle2_low = df['low'].iloc[i+1]
            candle2_open = df['open'].iloc[i+1]
            candle2_close = df['close'].iloc[i+1]
            candle2_size = abs(candle2_high - candle2_low)
            candle2_time = df.index[i+1]
            
            # Colors
            c1_color = "RED" if candle1_close < candle1_open else "GREEN"
            c2_color = "RED" if candle2_close < candle2_open else "GREEN"
            
            # LIC check
            is_lic = "YES" if candle1_size > 45 else "NO"
            
            # Trade type
            trade_type = "LONG" if c1_color == "RED" else "SHORT"
            
            # Directions
            c1_direction = "DOWN" if candle1_close < candle1_open else "UP"
            c2_direction = "DOWN" if candle2_close < candle2_open else "UP"
            is_retracement = "YES" if c1_direction != c2_direction else "NO"
            
            # Threshold
            if c1_color == "RED":  # LONG
                threshold = candle1_low + (candle1_size / 4)
            else:  # SHORT
                threshold = candle1_high - (candle1_size / 4)
            
            # STOP-LOSS CHECK
            stop_loss_triggered = "NO"
            sl_reason = ""
            
            if is_retracement == "YES":
                if c1_color == "RED" and candle2_open > threshold:  # LONG
                    stop_loss_triggered = "YES"
                    sl_reason = "C2 Open above Threshold"
                elif c1_color == "GREEN" and candle2_open < threshold:  # SHORT
                    stop_loss_triggered = "YES"
                    sl_reason = "C2 Open below Threshold"
            
            # LOC and Profit calculation
            is_loc = "NO"
            profit = 0
            profit_pct = 0
            trade_status = "INVALID"
            
            if stop_loss_triggered == "NO" and is_retracement == "YES":
                if c1_color == "RED" and candle2_high > threshold:  # LONG
                    is_loc = "YES"
                    profit = threshold - candle2_open
                    profit_pct = (profit / candle2_open) * 100 if candle2_open > 0 else 0
                    
                    # Risk management check
                    if abs(profit) <= max_loss_per_trade and daily_loss + abs(profit) <= max_daily_loss:
                        cumulative_pl += profit
                        daily_loss += abs(profit) if profit < 0 else 0
                        trades_executed += 1
                        trade_status = "EXECUTED"
                    else:
                        trade_status = "REJECTED (Risk Limit)"
                    
                elif c1_color == "GREEN" and candle2_low < threshold:  # SHORT
                    is_loc = "YES"
                    profit = candle2_open - threshold
                    profit_pct = (profit / candle2_open) * 100 if candle2_open > 0 else 0
                    
                    # Risk management check
                    if abs(profit) <= max_loss_per_trade and daily_loss + abs(profit) <= max_daily_loss:
                        cumulative_pl += profit
                        daily_loss += abs(profit) if profit < 0 else 0
                        trades_executed += 1
                        trade_status = "EXECUTED"
                    else:
                        trade_status = "REJECTED (Risk Limit)"
            
            if stop_loss_triggered == "YES":
                trade_status = f"STOPPED ({sl_reason})"
            
            analysis.append({
                'C1 Time': candle1_time.strftime('%Y-%m-%d %H:%M'),
                'C1 High': f"₹{candle1_high:.0f}",
                'C1 Low': f"₹{candle1_low:.0f}",
                'C1 Size': f"₹{candle1_size:.0f}",
                'C1 Color': c1_color,
                'Is LIC': is_lic,
                'Trade Type': trade_type,
                'C2 Size': f"₹{candle2_size:.0f}",
                'C2 Retracement': is_retracement,
                'Threshold': f"₹{threshold:.0f}",
                'C2 Open': f"₹{candle2_open:.0f}",
                'C2 High': f"₹{candle2_high:.0f}",
                'C2 Low': f"₹{candle2_low:.0f}",
                'Stop-Loss': stop_loss_triggered,
                'Status': trade_status,
                'Profit (₹)': f"{profit:.0f}" if profit != 0 else "-",
                'C2 Color': c2_color,
                'Profit %': f"{profit_pct:.2f}%" if profit != 0 else "-",
                'profit_value': profit,
                'trade_type': trade_type,
                'is_retracement': is_retracement,
                'stop_loss': stop_loss_triggered
            })
        
        # Apply filters
        filtered_analysis = analysis.copy()
        
        if retracement_filter == "YES":
            filtered_analysis = [x for x in filtered_analysis if x['is_retracement'] == 'YES']
        elif retracement_filter == "NO":
            filtered_analysis = [x for x in filtered_analysis if x['is_retracement'] == 'NO']
        
        if trade_type_filter == "LONG (C1 RED)":
            filtered_analysis = [x for x in filtered_analysis if x['trade_type'] == 'LONG']
        elif trade_type_filter == "SHORT (C1 GREEN)":
            filtered_analysis = [x for x in filtered_analysis if x['trade_type'] == 'SHORT']
        
        if show_stopped[0] == "N":
            filtered_analysis = [x for x in filtered_analysis if x['stop_loss'] == 'NO']
        
        # Remove helper columns
        for row in filtered_analysis:
            del row['profit_value']
            del row['trade_type']
            del row['is_retracement']
            del row['stop_loss']
        
        analysis_df = pd.DataFrame(filtered_analysis)
        
        if len(analysis_df) > 0:
            st.dataframe(analysis_df, use_container_width=True, hide_index=True)
            
            st.write("---")
            st.header("💰 Summary")
            
            cumulative = 0
            trades_data = []
            for row in filtered_analysis:
                profit_str = row['Profit (₹)'].replace('₹', '').strip()
                if profit_str != "-":
                    profit_val = float(profit_str)
                    cumulative += profit_val
                    trades_data.append(profit_val)
            
            total_pl = cumulative
            winning_trades = len([p for p in trades_data if p > 0])
            losing_trades = len([p for p in trades_data if p < 0])
            total_trades = winning_trades + losing_trades
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("💰 Total P&L", f"₹{total_pl:.0f}")
            col2.metric("🎯 Trades Executed", total_trades)
            col3.metric("✅ Wins", winning_trades)
            col4.metric("❌ Losses", losing_trades)
            
            st.write("---")
            st.header("📊 Risk Analysis")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Daily Loss Used", f"₹{daily_loss:.0f} / ₹{max_daily_loss:.0f}")
            with col2:
                st.metric("Capital Used", f"₹{total_pl:.0f} / ₹{capital:.0f}")
                if capital > 0:
                    roi = (total_pl / capital) * 100
                    st.metric("ROI", f"{roi:.2f}%")
            with col3:
                if total_trades > 0:
                    st.metric("Win Rate", f"{(winning_trades/total_trades)*100:.1f}%")
                    st.metric("Avg P&L", f"₹{(total_pl/total_trades):.0f}")
        else:
            st.warning("⚠️ No trades match your filter criteria!")

else:
    st.info("👆 Upload CSV to start!")

st.markdown("""
**Stop-Loss Logic:**
- LONG: If C2 Open > Threshold → Stop-Loss Triggered (exit immediately)
- SHORT: If C2 Open < Threshold → Stop-Loss Triggered (exit immediately)

**Risk Management:**
- Max Loss Per Trade: Rejects if loss > limit
- Max Daily Loss: Prevents over-trading
- Tracks capital utilization
""")
