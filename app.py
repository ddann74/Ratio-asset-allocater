import streamlit as st
import yfinance as yf
import pandas as pd

# 1. Configuration & Thresholds
# These define your "Green Zones" for potential buy signals
BUY_ZONES = {
    "Silver": 80.0,    # Buy when Ratio is >= 80
    "S&P 500": 1.0,    # Buy when Ratio is <= 1.0
    "Dow Jones": 6.0,  # Buy when Ratio is <= 6.0
    "Miners": 0.05,    # Buy when Ratio is <= 0.05
    "Oil": 0.05        # Buy when Ratio is <= 0.05
}

# 2. App UI Setup
st.set_page_config(page_title="Value Dashboard", layout="wide")
st.title("🏆 Gold-Standard Command Center")
st.write("Real-time relative value indicators with Data Stabilization tracking.")

def get_status_styles(name, ratio):
    # Logic to determine if we are in a Buy Zone
    is_buy = False
    if name == "Silver":
        is_buy = ratio >= BUY_ZONES[name]
    else:
        is_buy = ratio <= BUY_ZONES[name]
    
    # Green background for Buy Signal, Dark Grey for Neutral
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
        # Fetching 5 days of hourly data for stabilization check
        # We fetch the asset and Gold (GC=F) to calculate the ratio
        raw_data = yf.download(ticker, period="5d", interval="1h")['Close']
        gold_data = yf.download("GC=F", period="5d", interval="1h")['Close']
        
        # Create the ratio series
        ratios_series = raw_data / gold_data
        
        # --- FIX FOR LINE 43 ERROR ---
        # Extract the latest value and the 5-day average as single floats
        curr = float(ratios_series.iloc[-1])
        avg = float(ratios_series.mean())
        
        # 4. Data Stabilization Indicator (Added as requested 2026-02-07)
        # Checks if current ratio is within 2% of the 5-day average
        diff = abs(curr - avg) / avg
        stability_label = "🟢 Stable" if diff < 0.02 else "🔴 Volatile"
        
        is_buy, bg_color = get_status_styles(name, curr)

        # 5. Display results in themed cards
        with cols[i]:
            st.markdown(f"""
                <div style="background-color:{bg_color}; padding:20px; border-radius:10px; border: 1px solid #444; min-height: 180px; color: white;">
                    <h4 style="margin:0; color:#bbb;">{name}</h4>
                    <h2 style="margin:10px 0;">{curr:.4f}</h2>
                    <p style="margin:0; font-size:0.9em;">{stability_label}</p>
                    <p style="margin:0; font-size:0.8em; color:#888;">Variance: {diff:.2%}</p>
                    {f"<div style='margin-top:10px; padding:5px; border:1px solid white; text-align:center; font-weight:bold;'>🔥 BUY SIGNAL</div>" if is_buy else ""}
                </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        with cols[i]:
            st.error(f"Error: {name}")
            st.caption("Data currently unavailable.")

# 6. Footer
st.divider()
st.caption("Data sourced via yfinance. Includes real-time Data Stabilization indicators.")
