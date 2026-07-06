import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from lic_detection import detect_lic, detect_loc, identify_patterns, calculate_pnl
import os

st.set_page_config(page_title="LIC-LOC Backtester", layout="wide")

st.title("📊 LIC-LOC Backtesting Report")
st.markdown("Upload OHLCV data to detect liquidity patterns and backtest")

# ═══════════════════════════════════════════════════════════════
# SIDEBAR: SETTINGS
# ═══════════════════════════════════════════════════════════════

st.sidebar.header("⚙️ Settings")

volume_multiplier = st.sidebar.slider(
    "Volume Multiplier", 
    min_value=1.0, 
    max_value=3.0, 
    value=1.5,
    step=0.1,
    help="Volume must be X times average"
)

retracement_pct = st.sidebar.slider(
    "LOC Retracement (%)", 
    min_value=10, 
    max_value=50, 
    value=25,
    help="LOC must retrace X% of LIC"
)

# ═══════════════════════════════════════════════════════════════
# FILE UPLOAD
# ═══════════════════════════════════════════════════════════════

st.header("📁 Step 1: Upload Data")

col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader(
        "Choose OHLCV CSV file", 
        type="csv",
        help="CSV with columns: datetime, open, high, low, close, volume"
    )

with col2:
    csv_files = [f for f in os.listdir('.') if f.startswith('nifty_') and f.endswith('.csv')]
    if csv_files:
        selected_file = st.selectbox(
            "Or select from existing files",
            options=[""] + csv_files,
            help="Use previously downloaded data"
        )
    else:
        selected_file = ""

# Load data
df = None
file_info = None

if uploaded_file:
    df = pd.read_csv(uploaded_file, index_col=0)
    df.index = pd.to_datetime(df.index, format='%d-%m-%Y %H:%M', dayfirst=True)
    file_info = f"📤 Uploaded: {uploaded_file.name}"
elif selected_file:
    df = pd.read_csv(selected_file, index_col=0)
    df.index = pd.to_datetime(df.index, format='%d-%m-%Y %H:%M', dayfirst=True)
    file_info = f"📂 Selected: {selected_file}"

if df is not None:
    st.success(file_info)
    st.write(f"**Data loaded:** {len(df)} candles | Date range: {df.index[0].date()} to {df.index[-1].date()}")
    
    with st.expander("📋 Data Preview"):
        st.dataframe(df.head(10), use_container_width=True)
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 2: DETECT SIGNALS
    # ═══════════════════════════════════════════════════════════════
    
    st.header("🔍 Step 2: Detect Signals")
    
    if st.button("🚀 Analyze Signals", use_container_width=True):
        with st.spinner("Detecting LIC signals..."):
            lic_signals = detect_lic(df, volume_multiplier=volume_multiplier)
            df_with_lic = pd.concat([df, lic_signals], axis=1)
        
        st.success("✅ LIC signals detected")
        
        with st.spinner("Detecting LOC signals..."):
            loc_signals = detect_loc(df_with_lic, lic_signals, retracement_pct=retracement_pct)
            df_with_loc = pd.concat([df_with_lic, loc_signals], axis=1)
        
        st.success("✅ LOC signals detected")
        
        with st.spinner("Identifying patterns..."):
            pattern_signals = identify_patterns(df_with_loc, lic_signals, loc_signals)
            df_final = pd.concat([df_with_loc, pattern_signals], axis=1)
        
        st.success("✅ Patterns identified")
        
        # Calculate P&L
        df_final = calculate_pnl(df_final, pattern_signals)
        
        # ═══════════════════════════════════════════════════════════════
        # RESULTS SUMMARY
        # ═══════════════════════════════════════════════════════════════
        
        st.header("📊 Results Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        total_lic = lic_signals['is_lic'].sum()
        total_loc = loc_signals['is_loc'].sum()
        total_signals = (pattern_signals['signal'] != 'NONE').sum()
        total_profit = df_final[df_final['signal'] != 'NONE']['pnl'].fillna(0).sum()
        
        with col1:
            st.metric("LIC Signals", int(total_lic))
        
        with col2:
            st.metric("LOC Signals", int(total_loc))
        
        with col3:
            st.metric("Trading Signals", int(total_signals))
        
        with col4:
            st.metric("Total Profit (₹)", f"{total_profit:,.0f}")
        
        # ═══════════════════════════════════════════════════════════════
        # DETAILED DATA VIEW WITH P&L
        # ═══════════════════════════════════════════════════════════════
        
        st.header("📈 Detailed Signals with P&L")
        
        signals_df = df_final[df_final['signal'] != 'NONE'].copy()
        
        if len(signals_df) > 0:
            signals_df = signals_df.loc[:, ~signals_df.columns.duplicated()]
            
            # Show with P&L
            display_df = signals_df[['open', 'high', 'low', 'close', 'volume', 'signal', 'pnl', 'pnl_pct']].copy()
            display_df['pnl'] = display_df['pnl'].apply(lambda x: f"₹{x:,.0f}" if pd.notna(x) else "-")
            display_df['pnl_pct'] = display_df['pnl_pct'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "-")
            
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("No trading signals found with current parameters")
        
        # ═══════════════════════════════════════════════════════════════
        # CHART VISUALIZATION (IMPROVED)
        # ═══════════════════════════════════════════════════════════════
        
        st.header("📉 Chart with Signals & Volume")
        
        # ✅ ZOOM CONTROL
        col1, col2 = st.columns([3, 1])
        with col2:
            candles_to_show = st.slider(
                "Candles",
                min_value=20,
                max_value=len(df_final),
                value=min(50, len(df_final)),
                help="How many candles to display (fewer = bigger, clearer)"
            )
        
        # Filter data for display
        df_display = df_final.tail(candles_to_show)
        
        # Create figure with subplots
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.12,
            row_heights=[0.7, 0.3],
            subplot_titles=("Price & Signals", "Volume")
        )
        
        # Add candlesticks (FIXED - NO wickline parameter)
        fig.add_trace(go.Candlestick(
            x=df_display.index,
            open=df_display['open'],
            high=df_display['high'],
            low=df_display['low'],
            close=df_display['close'],
            name="Candlesticks",
            increasing=dict(
                line=dict(color='darkgreen', width=2),
                fillcolor='lightgreen'
            ),
            decreasing=dict(
                line=dict(color='darkred', width=2),
                fillcolor='lightcoral'
            )
        ), row=1, col=1)
        
        # Add volume bars (bottom chart)
        colors = ['red' if df_display.iloc[i]['close'] < df_display.iloc[i]['open'] else 'green' 
                  for i in range(len(df_display))]
        
        fig.add_trace(go.Bar(
            x=df_display.index,
            y=df_display['volume'],
            name="Volume",
            marker=dict(color=colors),
            opacity=0.6,
            showlegend=False
        ), row=2, col=1)
        
        # Add LIC signals (orange diamonds - BIGGER)
        lic_points = df_display[df_display['is_lic']]
        fig.add_trace(go.Scatter(
            x=lic_points.index,
            y=lic_points['close'],
            mode='markers',
            marker=dict(
                symbol='diamond', 
                size=12,
                color='orange',
                line=dict(color='darkorange', width=2)
            ),
            name='LIC',
            showlegend=True
        ), row=1, col=1)
        
        # Add BUY signals (green triangles - BIGGER)
        buy_signals = df_display[df_display['signal'] == 'BUY']
        fig.add_trace(go.Scatter(
            x=buy_signals.index,
            y=buy_signals['close'],
            mode='markers',
            marker=dict(
                symbol='triangle-up', 
                size=14,
                color='lime',
                line=dict(color='darkgreen', width=2)
            ),
            name='BUY',
            showlegend=True
        ), row=1, col=1)
        
        # Add SELL signals (red triangles - BIGGER)
        sell_signals = df_display[df_display['signal'] == 'SELL']
        fig.add_trace(go.Scatter(
            x=sell_signals.index,
            y=sell_signals['close'],
            mode='markers',
            marker=dict(
                symbol='triangle-down', 
                size=14,
                color='red',
                line=dict(color='darkred', width=2)
            ),
            name='SELL',
            showlegend=True
        ), row=1, col=1)
        
        # Update layout (BIGGER, CLEARER)
        fig.update_layout(
            title=f"LIC-LOC Pattern Detection (Last {candles_to_show} candles)",
            height=900,
            hovermode='x unified',
            template="plotly_white",
            font=dict(size=11),
            showlegend=True,
            legend=dict(
                x=0.01,
                y=0.99,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='black',
                borderwidth=1
            )
        )
        
        # Update axes (BIGGER LABELS)
        fig.update_yaxes(title_text="Price (₹)", row=1, col=1, title_font=dict(size=12))
        fig.update_yaxes(title_text="Volume", row=2, col=1, title_font=dict(size=12))
        fig.update_xaxes(title_text="Date", row=2, col=1, title_font=dict(size=12))
        
        # Add grid for clarity
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # ═══════════════════════════════════════════════════════════════
        # DOWNLOAD RESULTS
        # ═══════════════════════════════════════════════════════════════
        
        st.header("💾 Download Results")
        
        csv = df_final.to_csv()
        st.download_button(
            label="📥 Download Full Data (CSV)",
            data=csv,
            file_name="lic_loc_analysis.csv",
            mime="text/csv"
        )

else:
    st.info("👆 Upload a CSV file to get started")