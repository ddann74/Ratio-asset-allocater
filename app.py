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
st.write("30-Year Historical Analysis & Data Stabilization [Updated Layout]")

def get_status_styles(name, ratio):
    is_buy = ratio >= BUY_ZONES[name] if name == "Silver" else ratio <= BUY_ZONES[name]
    # Green for Buy, Dark Grey for Hold
    bg_color = "#1e4620" if is_buy else "#1E1E1E" 
    status_text = "🔥 BUY SIGNAL" if is_buy else "⏳ HOLD / NEUTRAL"
    return is_buy, bg_color, status_text

# 3. Enhanced Data Fetching with Caching
@st.cache_data(ttl=3600)
def fetch_historical_ratios(ticker, gold_ticker="GC=F"):
    try:
        asset = yf.Ticker(ticker).history(period="30y", interval="1mo")['Close']
        gold = yf.Ticker(gold_ticker).history(period="30y", interval="1mo")['Close']
        combined = pd.concat([asset, gold], axis=1).dropna()
        combined.columns = ['Asset', 'Gold']
        return combined['Asset'] / combined['Gold']
    except:
        return pd.Series()

tickers = {
    "Silver": "SI=F", 
    "S&P 500": "ES=F", 
    "Dow Jones": "YM=F", 
    "Miners": "GDXJ", 
    "Oil": "CL=F"
}

cols = st.columns(len(tickers))

for i, (name, ticker) in enumerate(tickers.items()):
    try:
        ratios = fetch_historical_ratios(ticker)
        
        if not ratios.empty:
            curr = float(ratios.iloc[-1])
            avg_12m = float(ratios.tail(12).mean())
            hist_high = float(ratios.max())
            hist_low = float(ratios.min())
            
            # Data Stabilization Check (2026-02-07 instruction)
            diff = abs(curr - avg_12m) / avg_12m
            stability_label = "🟢 Stable" if diff < 0.05 else "🔴 Volatile"
            
            is_buy, bg_color, status_text = get_status_styles(name, curr)

            with cols[i]:
                # Updated CSS: Using Flexbox to prevent overlap
                st.markdown(f"""
                    <div style="background-color:{bg_color}; padding:20px; border-radius:12px; border: 1px solid #444; height: 350px; color: white; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 2px 2px 10px rgba(0,0,0,0.5);">
                        <div style="text-align: center;">
                            <h4 style="margin:0; color:#bbb; text-transform: uppercase; font-size: 0.8em; letter-spacing: 1px;">{name}</h4>
                            <h1 style="margin:10px 0; color:#FFD700; font-size: 2.2em;">{curr:.4f}</h1>
                        </div>
                        
                        <div style="font-size: 0.9em; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px;">
                            <p style="margin:3px 0; display: flex; justify-content: space-between;"><span>Stability:</span> <b>{stability_label}</b></p>
                            <p style="margin:3px 0; display: flex; justify-content: space-between;"><span>30Y High:</span> <b>{hist_high:.2f}</b></p>
                            <p style="margin:3px 0; display: flex; justify-content: space-between;"><span>30Y Low:</span> <b>{hist_low:.2f}</b></p>
                            <p style="margin:3px 0; display: flex; justify-content: space-between; color: #888; font-size: 0.8em;"><span>Variance:</span> <b>{diff:.2%}</b></p>
                        </div>

                        <div style="margin-top: 15px; padding: 10px; border: 1px solid {'#fff' if is_buy else '#444'}; text-align: center; font-weight: bold; border-radius: 5px; background: {'rgba(255,255,255,0.1)' if is_buy else 'transparent'};">
                            {status_text}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            cols[i].warning(f"No data for {name}")
    except Exception:
        cols[i].error(f"Error: {name}")

st.divider()
st.caption("Standardized Layout V2 | 30Y Historical Context | Data Stabilization Active")
