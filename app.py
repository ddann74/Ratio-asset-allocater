import streamlit as st
import yfinance as yf
import pandas as pd

# 1. Configuration
BUY_ZONES = {
    "Silver": 80.0,
    "S&P 500": 1.0,
    "Dow Jones": 6.0,
    "Miners": 0.05,
    "Oil": 0.05
}

# 2. App UI Setup
st.set_page_config(page_title="Value Dashboard", layout="wide")
st.title("🏆 Gold-Standard Command Center")
st.write("30-Year History | Data Stabilization [Updated 2026-02-07]")

# 3. Data Fetching Logic (Fixed to prevent code leakage)
@st.cache_data(ttl=3600)
def fetch_data(ticker, gold_ticker="GC=F"):
    try:
        # progress=False is critical to prevent code bars on screen
        asset = yf.download(ticker, period="30y", interval="1mo", progress=False)['Close']
        gold = yf.download(gold_ticker, period="30y", interval="1mo", progress=False)['Close']
        
        combined = pd.concat([asset, gold], axis=1).dropna()
        combined.columns = ['Asset', 'Gold']
        return combined['Asset'] / combined['Gold']
    except Exception:
        return pd.Series()

def get_status(name, ratio):
    is_buy = ratio >= BUY_ZONES[name] if name == "Silver" else ratio <= BUY_ZONES[name]
    bg = "#1e4620" if is_buy else "#1E1E1E" 
    text = "🔥 BUY SIGNAL" if is_buy else "⏳ HOLD / NEUTRAL"
    return is_buy, bg, text

# 4. Dashboard Grid
tickers = {
    "Silver": "SI=F", 
    "S&P 500": "ES=F", 
    "Dow Jones": "YM=F", 
    "Miners": "GDXJ", 
    "Oil": "CL=F"
}

cols = st.columns(len(tickers))

for i, (name, ticker) in enumerate(tickers.items()):
    ratios = fetch_data(ticker)
    
    if not ratios.empty:
        curr = float(ratios.iloc[-1])
        avg_year = float(ratios.tail(12).mean())
        h_high, h_low = float(ratios.max()), float(ratios.min())
        
        # Data Stabilization (User Request 2026-02-07)
        var = abs(curr - avg_year) / avg_year
        stab = "🟢 Stable" if var < 0.05 else "🔴 Volatile"
        is_buy, bg_color, signal = get_status(name, curr)

        with cols[i]:
            # Encapsulated HTML to prevent leakage
            st.markdown(f"""
            <div style="background-color:{bg_color}; padding:20px; border-radius:12px; border: 1px solid #444; height: 380px; color: white; display: flex; flex-direction: column; justify-content: space-between; font-family: sans-serif;">
                <div style="text-align: center;">
                    <div style="color:#bbb; text-transform: uppercase; font-size: 0.75em; font-weight: bold;">{name}</div>
                    <div style="margin:10px 0; color:#FFD700; font-size: 2.2em; font-weight: bold;">{curr:.4f}</div>
                </div>
                
                <div style="font-size: 0.85em; background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>Status:</span> <b>{stab}</b></div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>30Y High:</span> <b>{h_high:.2f}</b></div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>30Y Low:</span> <b>{h_low:.2f}</b></div>
                    <div style="display: flex; justify-content: space-between; color: #888; font-size: 0.9em; border-top: 1px solid #444; margin-top: 8px; padding-top: 8px;">
                        <span>Variance:</span> <b>{var:.2%}</b>
                    </div>
                </div>

                <div style="padding: 10px; border: 2px solid {'#fff' if is_buy else '#555'}; text-align: center; font-weight: bold; border-radius: 6px; background: {'rgba(255,255,255,0.15)' if is_buy else 'transparent'};">
                    {signal}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        cols[i].warning(f"Connecting to {name}...")

st.divider()
st.caption("Standardized Layout | 30Y History | Data Stabilization Active [2026-02-07]")
