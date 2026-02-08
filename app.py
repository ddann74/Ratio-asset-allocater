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
st.write("30-Year Historical Analysis & Data Stabilization")

def get_status_styles(name, ratio):
    is_buy = ratio >= BUY_ZONES[name] if name == "Silver" else ratio <= BUY_ZONES[name]
    bg_color = "#28a745" if is_buy else "#1E1E1E" 
    return is_buy, bg_color

# 3. Enhanced Data Fetching
tickers = {
    "Silver": "SI=F", 
    "S&P 500": "ES=F", 
    "Dow Jones": "YM=F", 
    "Miners": "GDXJ", 
    "Oil": "CL=F"
}

@st.cache_data(ttl=3600) # Cache for 1 hour to prevent API blocks
def fetch_historical_ratios(ticker, gold_ticker="GC=F"):
    # Fetch 30 years of monthly data for historical context
    asset = yf.Ticker(ticker).history(period="30y", interval="1mo")['Close']
    gold = yf.Ticker(gold_ticker).history(period="30y", interval="1mo")['Close']
    
    # Align and calculate
    combined = pd.concat([asset, gold], axis=1).dropna()
    combined.columns = ['Asset', 'Gold']
    return combined['Asset'] / combined['Gold']

cols = st.columns(len(tickers))

for i, (name, ticker) in enumerate(tickers.items()):
    try:
        ratios = fetch_historical_ratios(ticker)
        
        if not ratios.empty:
            curr = float(ratios.iloc[-1])
            avg_30d = float(ratios.tail(12).mean()) # Approx 1-year stability check
            hist_high = float(ratios.max())
            hist_low = float(ratios.min())
            
            # Data Stabilization Indicator (as requested 2026-02-07)
            diff = abs(curr - avg_30d) / avg_30d
            stability_label = "🟢 Stable" if diff < 0.05 else "🔴 Volatile"
            
            is_buy, bg_color = get_status_styles(name, curr)

            with cols[i]:
                # Standardized card with fixed heights
                st.markdown(f"""
                    <div style="background-color:{bg_color}; padding:15px; border-radius:10px; border: 1px solid #444; height: 300px; color: white; position: relative;">
                        <h4 style="margin:0; color:#bbb; text-align:center;">{name}</h4>
                        <h2 style="margin:10px 0; text-align:center; color:#FFD700;">{curr:.4f}</h2>
                        <hr style="border:0.5px solid #444;">
                        <p style="margin:0; font-size:0.85em;"><b>Status:</b> {stability_label}</p>
                        <p style="margin:0; font-size:0.85em;"><b>30Y High:</b> {hist_high:.4f}</p>
                        <p style="margin:0; font-size:0.85em;"><b>30Y Low:</b> {hist_low:.4f}</p>
                        <p style="margin:5px 0 0 0; font-size:0.75em; color:#888;">Variance: {diff:.2%}</p>
                        {f"<div style='position:absolute; bottom:15px; left:15px; right:15px; padding:5px; border:2px solid white; text-align:center; font-weight:bold; background:rgba(255,255,255,0.1);'>🔥 BUY SIGNAL</div>" if is_buy else ""}
                    </div>
                """, unsafe_allow_html=True)
        else:
            with cols[i]: st.warning(f"No data for {name}")

    except Exception:
        with cols[i]: st.error(f"Error loading {name}")

st.divider()
st.caption("30-Year Historical Data sourced via Yahoo Finance API. Includes Data Stabilization logic [2026-02-07].")
