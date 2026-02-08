import streamlit as st
import yfinance as yf
import pandas as pd

# 1. Configuration & Thresholds
# These define your "Green Zones" for buying
BUY_ZONES = {
    "Silver": 80.0,    # Ratio above 80
    "S&P 500": 1.0,    # Ratio below 1.0
    "Dow Jones": 6.0,  # Ratio below 6.0
    "Miners": 0.05,    # Ratio below 0.05
    "Oil": 0.05        # Ratio below 0.05
}

# 2. App UI Setup
st.set_page_config(page_title="Value Dashboard", layout="wide")
st.title("🏆 Gold-Standard Command Center")
st.write("Real-time relative value indicators with Data Stabilization tracking.")

def get_status_styles(name, ratio, is_stable):
    # Logic to determine if we are in a Buy Zone
    is_buy = False
    if name == "Silver":
        is_buy = ratio >= BUY_ZONES[name]
    else:
        is_buy = ratio <= BUY_ZONES[name]
    
    # Visual cues: Green for Buy, Dark for Neutral
    bg_color = "#28a745" if is_buy else "#1E1E1E" 
    return is_buy, bg_color

# 3. Data Fetching & Ratio Calculation
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
        # Fetching 5 days of hourly data for stabilization math
        raw_data = yf.download(ticker, period="5d", interval="1h")['Close']
        gold_data = yf.download("GC=F", period="5d", interval="1h")['Close']
        
        # Calculate the ratio series
        ratios_series = raw_data / gold_data
        
        # FIX: Extract individual scalar values to avoid Ambiguity Error
        # .item() or .iloc[-1] ensures we are dealing with a number, not a list
        curr = float(ratios_series.iloc[-1])
        avg = float(ratios_series.mean())
        
        # Data Stabilization Logic [cite: 12, 13]
        # Checks if current price is within 2% of the 5-day average
        diff = abs(curr - avg) / avg
        stability_label = "🟢 Stable" if diff < 0.02 else "🔴 Volatile"
        
        is_buy, bg_color = get_status_styles(name, curr, stability_label)

        with cols[i]:
            st.markdown(f"""
                <div style="background-color:{bg_color}; padding:20px; border-radius:10px; border: 1px solid #444; min-height: 200px;">
                    <h3 style="margin:0; color:white;">{name}</h3>
                    <h2 style="margin:10px 0; color:white;">{curr:.4f}</h2>
                    <p style="margin:0; color:#bbb;">{stability_label}</p>
                    <p style="margin:5px 0; font-size: 0.8em; color:#888;">Var: {diff:.2%}</p>
                    {f"<div style='margin-top:10px; font-weight:bold; color:#fff; border:1px solid white; text-align:center;'>🔥 BUY SIGNAL</div>" if is_buy else ""}
                </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        with cols[i]:
            st.error(f"Error loading {name}")
            st.caption(str(e))

# 4. Global Footer
st.divider()
st.caption("Data provided by Yahoo Finance. Stabilization based on 5-day hourly rolling average.")
