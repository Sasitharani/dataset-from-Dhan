import streamlit as st

st.set_page_config(page_title="LIC-LOC Trading System", layout="wide")

st.title("🚀 LIC-LOC Algorithmic Trading System")

st.markdown("""
Welcome to your personal Nifty intraday trading system!

**Features:**
- 📊 Extract real Nifty data from Dhan API
- 🔍 Detect LIC-LOC patterns automatically
- 💹 Backtest trading signals
- 📈 Analyze P&L performance
- 🎯 Fine-tune parameters with sliders

**How to use:**
1. Go to **Data Extractor** tab → Enter API token & get data
2. Go to **Backtester** tab → Select CSV → See signals & chart
3. Use slider to zoom in/out on candlesticks
4. Analyze results and download CSV

---

**Current status:** Ready to extract and backtest! 🎯
""")