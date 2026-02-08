import streamlit as st
import yfinance as yf
import pandas as pd

# 1. Configuration - Updated for Intuitive Ratios
BUY_ZONES = {
    "Silver": 85.0,      # BUY when it takes MORE silver to buy gold (Silver is cheap)
    "S&P 500": 1.2,      # BUY when S&P is LOW relative to gold
    "Dow Jones": 15.0,   # BUY when Dow is LOW relative to gold
    "Miners": 0.02,      # BUY when GDXJ is LOW relative to gold
    "Oil": 0.04          # BUY when Oil is LOW relative to gold
}

st.set_page_config(page_title="Value Dashboard", layout="wide")
st.title("🏆 Gold-Standard Command Center")
st.write("Corrected Ratios: Silver (Gold/SI) | Others (Asset/Gold)")

@st.cache_data(ttl=3600)
def fetch_data(ticker):
    try:
        asset = yf.download(ticker, period="30y", interval="1mo", progress=False)['Close']
        gold = yf.download("GC=F", period="30y", interval="1mo", progress=False)['Close']
        combined = pd.concat([asset, gold], axis=1).dropna()
        combined.columns = ['Asset', 'Gold']
        
        # INVERSION LOGIC: If Silver, do Gold/Asset. Otherwise, Asset/Gold.
        if "SI=F" in ticker:
            return combined['Gold'] / combined['Asset']
        return combined['Asset'] / combined['Gold']
    except:
        return pd.Series()

# 4. Grid Layout
tickers = {"Silver": "SI=F", "S&P 500": "ES=F", "Dow Jones": "YM=F", "Miners": "GDXJ", "Oil": "CL=F"}
cols = st.columns(len(tickers))

for i, (name, sym) in enumerate(tickers.items()):
    ratios = fetch_data(sym)
    
    if not ratios.empty:
        curr = float(ratios.iloc[-1])
        avg_12m = float(ratios.tail(12).mean())
        var = abs(curr - avg_12m) / avg_12m
        
        # LOGIC CHECK: For Silver, "High is Buy". For others, "Low is Buy".
        if name == "Silver":
            is_buy = curr >= BUY_ZONES[name]
        else:
            is_buy = curr <= BUY_ZONES[name]
            
        bg = "#1e4620" if is_buy else "#1E1E1E"
        
        with cols[i]:
            st.markdown(f"""
            <div style="background-color:{bg}; padding:15px; border-radius:10px; border:1px solid #444; color:white; height:380px; font-family:sans-serif; display:flex; flex-direction:column; justify-content:space-between;">
                <div style="text-align:center;">
                    <div style="font-size:0.8em; color:#bbb;">{name} {'(Gold/SI)' if name == 'Silver' else '(Asset/Gold)'}</div>
                    <div style="font-size:2.2em; font-weight:bold; color:#FFD700;">{curr:.2f if name == 'Silver' or name == 'S&P 500' or name == 'Dow Jones' else curr:.4f}</div>
                </div>
                <div style="background:rgba(0,0,0,0.3); padding:10px; border-radius:5px; font-size:0.8em;">
                    <div style="display:flex; justify-content:space-between;"><span>Status:</span><b>{'🔴 Volatile' if var > 0.05 else '🟢 Stable'}</b></div>
                    <div style="display:flex; justify-content:space-between;"><span>30Y High:</span><b>{ratios.max():.2f}</b></div>
                    <div style="display:flex; justify-content:space-between;"><span>30Y Low:</span><b>{ratios.min():.2f}</b></div>
                    <div style="margin-top:5px; padding-top:5px; border-top:1px solid #444; color:#888;">Data Stability Var: {var:.2%}</div>
                </div>
                <div style="text-align:center; padding:10px; border:2px solid {'#fff' if is_buy else '#444'}; font-weight:bold; border-radius:5px; background:{'rgba(255,255,255,0.1)' if is_buy else 'transparent'};">
                    {'🔥 BUY SIGNAL' if is_buy else '⏳ HOLD'}
                </div>
            </div>
            """, unsafe_allow_html=True)

st.divider()
st.caption("Ratios corrected for market standards. Data Stabilization logic active [2026-02-07].")
