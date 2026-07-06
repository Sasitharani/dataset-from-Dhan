import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Backtester", layout="wide")

st.title("📊 Nifty LIC-LOC Backtester")
st.markdown("Backtest LIC and LOC signals with interactive zoom")

uploaded_file = st.file_uploader("Upload your Nifty 15-min CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file, index_col=0)
    df.index = pd.to_datetime(df.index, format='ISO8601')
    
    st.success(f"✅ Loaded {len(df)} candles")
    
    st.header("🔍 Zoom Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        zoom_option = st.selectbox(
            "Select zoom level:",
            ["Last 10 (Max Zoom)", "Last 20", "Last 50", "Last 100", "All candles"],
            index=2
        )
    
    zoom_map = {
        "Last 10 (Max Zoom)": 10,
        "Last 20": 20,
        "Last 50": 50,
        "Last 100": 100,
        "All candles": len(df)
    }
    
    candles_to_show = zoom_map[zoom_option]
    df_display = df.tail(candles_to_show).copy()
    
    with col2:
        st.metric("Displaying", f"{len(df_display)} candles")
    
    with col3:
        st.metric("Total", f"{len(df)} candles")
    
    def detect_lic(df_local):
        lic_signals = []
        avg_volume = df_local['volume'].rolling(window=20).mean()
        for i in range(len(df_local)):
            if i < 20:
                continue
            volume_ratio = df_local['volume'].iloc[i] / avg_volume.iloc[i]
            if volume_ratio > 1.8:
                lic_signals.append(i)
        return lic_signals
    
    def detect_buy_signal(df_local, lic_indices):
        buy_signals = []
        for lic_idx in lic_indices:
            if lic_idx + 1 < len(df_local):
                next_candle = df_local.iloc[lic_idx + 1]
                if next_candle['close'] > next_candle['open']:
                    buy_signals.append(lic_idx + 1)
        return buy_signals
    
    def detect_sell_signal(df_local):
        sell_signals = []
        for i in range(6, len(df_local)):
            high_in_window = df_local['high'].iloc[i-6:i].max()
            retracement = ((high_in_window - df_local['close'].iloc[i]) / high_in_window) * 100
            if retracement > 25:
                sell_signals.append(i)
        return sell_signals
    
    st.header("⚙️ Analyze")
    
    if st.button("🚀 Analyze Signals", use_container_width=True):
        
        lic_indices = detect_lic(df_display)
        buy_indices = detect_buy_signal(df_display, lic_indices)
        sell_indices = detect_sell_signal(df_display)
        
        st.write(f"📊 LIC: {len(lic_indices)} | BUY: {len(buy_indices)} | SELL: {len(sell_indices)}")
        
        fig = go.Figure()
        
        for i in range(len(df_display)):
            row = df_display.iloc[i]
            color = 'darkgreen' if row['close'] > row['open'] else 'darkred'
            
            fig.add_trace(go.Scatter(
                x=[df_display.index[i], df_display.index[i]],
                y=[row['low'], row['high']],
                mode='lines',
                line=dict(color=color, width=2),
                hoverinfo='skip',
                showlegend=False
            ))
            
            fig.add_trace(go.Scatter(
                x=[df_display.index[i], df_display.index[i]],
                y=[row['open'], row['close']],
                mode='lines',
                line=dict(color=color, width=8),
                hoverinfo='skip',
                showlegend=False
            ))
        
        if lic_indices:
            lic_dates = [df_display.index[i] for i in lic_indices]
            lic_prices = [df_display['high'].iloc[i] for i in lic_indices]
            fig.add_trace(go.Scatter(x=lic_dates, y=lic_prices, mode='markers',
                marker=dict(symbol='diamond', size=14, color='orange'), name='LIC'))
        
        if buy_indices:
            buy_dates = [df_display.index[i] for i in buy_indices]
            buy_prices = [df_display['close'].iloc[i] for i in buy_indices]
            fig.add_trace(go.Scatter(x=buy_dates, y=buy_prices, mode='markers',
                marker=dict(symbol='triangle-up', size=16, color='green'), name='BUY'))
        
        if sell_indices:
            sell_dates = [df_display.index[i] for i in sell_indices]
            sell_prices = [df_display['close'].iloc[i] for i in sell_indices]
            fig.add_trace(go.Scatter(x=sell_dates, y=sell_prices, mode='markers',
                marker=dict(symbol='triangle-down', size=16, color='red'), name='SELL'))
        
        fig.update_layout(
            title="Price & Signals (Drag rangeslider at bottom to zoom!)",
            xaxis_title="Time",
            yaxis_title="Price (₹)",
            height=800,
            hovermode='x unified',
            xaxis=dict(
                rangeslider=dict(visible=True, thickness=0.08),
                type="date"
            ),
            template="plotly_white",
            font=dict(size=12)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        fig_volume = go.Figure()
        for i in range(len(df_display)):
            row = df_display.iloc[i]
            color = 'green' if row['candle_color'] == 'GREEN' else 'red'
            fig_volume.add_trace(go.Bar(
                x=[df_display.index[i]],
                y=[row['volume']],
                marker=dict(color=color),
                hovertemplate='<b>%{x}</b><br>Volume: %{y:,.0f}<extra></extra>',
                showlegend=False
            ))
        
        fig_volume.update_layout(
            title="Volume",
            xaxis_title="Time",
            yaxis_title="Volume",
            height=300,
            template="plotly_white"
        )
        
        st.plotly_chart(fig_volume, use_container_width=True)
        
        st.header("📈 Stats")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("High", f"₹{df_display['high'].max():.0f}")
        col2.metric("Low", f"₹{df_display['low'].min():.0f}")
        col3.metric("Avg Vol", f"{df_display['volume'].mean()/1e6:.1f}M")
        col4.metric("Green", f"{len(df_display[df_display['candle_color']=='GREEN'])}/{len(df_display)}")

else:
    st.info("👆 Upload CSV to start!")
