import streamlit as st
import yfinance as yf
import pandas as pd

# 1. Configuration with Multi-Level Thresholds
# For Silver: Higher = Cheaper. For Others: Lower = Cheaper.
THRESHOLDS = {
    "Silver": {"extreme_buy": 95.0, "buy": 85.0, "extreme_sell": 40.0},
    "S&P 500": {"extreme_buy": 0.8, "buy": 1.2, "extreme_sell": 2.5},
    "Dow Jones": {"extreme_buy": 10.0, "buy": 15.0, "extreme_sell": 25.0},
    "Miners": {"extreme_buy": 0.015, "buy": 0.022, "extreme_sell": 0.05},
    "Oil": {"extreme_buy": 0.025, "buy": 0.04, "extreme_sell": 0.10}
}

st.set_page_config(page_title="Value Dashboard", layout="wide")
st.title("🚨 Extreme Value Command Center")

@st.cache_data(ttl=3600)
def fetch_data(ticker):
    try:
        asset = yf.download(ticker, period="30y", interval="1mo", progress=False)['Close']
        gold = yf.download("GC=F", period="30y", interval="1mo", progress=False)['Close']
        combined = pd.concat([asset, gold], axis=1).dropna()
        combined.columns = ['Asset', 'Gold']
        if "SI=F" in ticker:
            return combined['Gold'] / combined['Asset'] # Gold/Silver Ratio
        return combined['Asset'] / combined['Gold'] # Asset/Gold Ratio
    except:
        return pd.Series()

# 2. Grid Layout
tickers = {"Silver": "SI=F", "S&P 500": "ES=F", "Dow Jones": "YM=F", "Miners": "GDXJ", "Oil": "CL=F"}
cols = st.columns(len(tickers))

for i, (name, sym) in enumerate(tickers.items()):
    ratios = fetch_data(sym)
    
    if not ratios.empty:
        curr = float(ratios.iloc[-1])
        t = THRESHOLDS[name]
        
        # Determine Signal State
        if name == "Silver":
            if curr >= t['extreme_buy']:
                status, bg, label = "EXTREME BUY", "#004d00", "💎 GENERATIONAL BUY"
            elif curr >= t['buy']:
                status, bg, label = "BUY", "#1e4620", "🔥 BUY SIGNAL"
            elif curr <= t['extreme_sell']:
                status, bg, label = "EXTREME SELL", "#900C3F", "⚠️ EXTREME SELL"
            else:
                status, bg, label = "HOLD", "#1E1E1E", "⏳ HOLD"
        else:
            if curr <= t['extreme_buy']:
                status, bg, label = "EXTREME BUY", "#004d00", "💎 GENERATIONAL BUY"
            elif curr <= t['buy']:
                status, bg, label = "BUY", "#1e4620", "🔥 BUY SIGNAL"
            elif curr >= t['extreme_sell']:
                status, bg, label = "EXTREME SELL", "#900C3F", "⚠️ EXTREME SELL"
            else:
                status, bg, label = "HOLD", "#1E1E1E", "⏳ HOLD"

        val_display = f"{curr:.2f}" if name in ["Silver", "S&P 500", "Dow Jones"] else f"{curr:.4f}"
        
        with cols[i]:
            st.markdown(f"""
            <div style="background-color:{bg}; padding:15px; border-radius:10px; border:1px solid #444; color:white; height:400px; display:flex; flex-direction:column; justify-content:space-between;">
                <div style="text-align:center;">
                    <div style="font-size:0.8em; color:#bbb;">{name}</div>
                    <div style="font-size:2.4em; font-weight:bold; color:#FFD700;">{val_display}</div>
                </div>
                <div style="background:rgba(0,0,0,0.3); padding:10px; border-radius:5px; font-size:0.8em;">
                    <div style="display:flex; justify-content:space-between;"><span>30Y High:</span><b>{ratios.max():.2f}</b></div>
                    <div style="display:flex; justify-content:space-between;"><span>30Y Low:</span><b>{ratios.min():.2f}</b></div>
                </div>
                <div style="text-align:center; padding:12px; border:2px solid white; font-weight:bold; border-radius:5px; background:rgba(255,255,255,0.1);">
                    {label}
                </div>
            </div>
            """, unsafe_allow_html=True)

st.divider()
st.caption("Includes Data Stabilization [2026-02-07] | Multi-level Buy/Sell Signals Active")
