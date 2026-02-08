import streamlit as st
import yfinance as yf
import pandas as pd

# 1. Setup & Configuration
st.set_page_config(page_title="Value Dashboard", layout="wide")

BUY_ZONES = {
    "Silver": 80.0, "S&P 500": 1.0, "Dow Jones": 6.0, "Miners": 0.05, "Oil": 0.05
}

st.title("🏆 Gold-Standard Command Center")
st.write("30-Year History | Data Stabilization Active")

# 2. Resilient Data Fetching
@st.cache_data(ttl=3600)
def get_ratios(ticker):
    try:
        # progress=False prevents the 'code leakage' you are seeing
        data = yf.download(ticker, period="30y", interval="1mo", progress=False)['Close']
        gold = yf.download("GC=F", period="30y", interval="1mo", progress=False)['Close']
        combined = pd.concat([data, gold], axis=1).dropna()
        return combined.iloc[:, 0] / combined.iloc[:, 1]
    except:
        return pd.Series()

# 3. Grid Layout
tickers = {"Silver": "SI=F", "S&P 500": "ES=F", "Dow Jones": "YM=F", "Miners": "GDXJ", "Oil": "CL=F"}
cols = st.columns(len(tickers))

for i, (name, sym) in enumerate(tickers.items()):
    ratios = get_ratios(sym)
    
    if not ratios.empty:
        curr = float(ratios.iloc[-1])
        avg_12m = float(ratios.tail(12).mean())
        # Variance for Data Stabilization (Added 2026-02-07)
        var = abs(curr - avg_12m) / avg_12m
        
        is_buy = curr >= BUY_ZONES[name] if name == "Silver" else curr <= BUY_ZONES[name]
        bg = "#1e4620" if is_buy else "#1E1E1E"
        
        with cols[i]:
            # The 'unsafe_allow_html' must be TRUE to render correctly
            st.markdown(f"""
            <div style="background-color:{bg}; padding:15px; border-radius:10px; border:1px solid #444; color:white; height:360px; font-family:sans-serif; display:flex; flex-direction:column; justify-content:space-between;">
                <div style="text-align:center;">
                    <div style="font-size:0.8em; color:#bbb;">{name}</div>
                    <div style="font-size:2em; font-weight:bold; color:#FFD700;">{curr:.4f}</div>
                </div>
                <div style="background:rgba(0,0,0,0.3); padding:10px; border-radius:5px; font-size:0.8em;">
                    <div style="display:flex; justify-content:space-between;"><span>Status:</span><b>{'🔴 Volatile' if var > 0.05 else '🟢 Stable'}</b></div>
                    <div style="display:flex; justify-content:space-between;"><span>30Y High:</span><b>{ratios.max():.2f}</b></div>
                    <div style="display:flex; justify-content:space-between;"><span>30Y Low:</span><b>{ratios.min():.2f}</b></div>
                    <div style="margin-top:5px; padding-top:5px; border-top:1px solid #444; color:#888;">Var: {var:.2%}</div>
                </div>
                <div style="text-align:center; padding:8px; border:2px solid {'#fff' if is_buy else '#444'}; font-weight:bold; border-radius:5px;">
                    {'🔥 BUY SIGNAL' if is_buy else '⏳ HOLD'}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        cols[i].error("Data Link Failed")

st.divider()
st.caption("Standardized Layout | Data Stabilization logic updated 2026-02-07")
