import streamlit as st
import yfinance as yf
import pandas as pd

# 1. Configuration & Thresholds
BUY_ZONES = {
    "Silver": 80.0,    # Ratio above 80
    "S&P 500": 1.0,    # Ratio below 1.0
    "Dow Jones": 6.0,  # Ratio below 6.0
    "Miners": 0.05,    # Ratio below 0.05
    "Oil": 0.05        # Ratio below 0.05
}

st.set_page_config(page_title="Value Dashboard", layout="wide")
st.title("🏆 Gold-Standard Command Center")

def get_status_styles(name, ratio, stability):
    is_buy = False
    if name == "Silver":
        is_buy = ratio >= BUY_ZONES[name]
    else:
        is_buy = ratio <= BUY_ZONES[name]
    bg_color = "#28a745" if is_buy else "#1E1E1E" 
    return is_buy, bg_color

# 2. Data Fetching & Ratio Calculation
tickers = {"Silver": "SI=F", "S&P 500": "ES=F", "Dow Jones": "YM=F", "Miners": "GDXJ", "Oil": "CL=F"}
cols = st.columns(len(tickers))

for i, (name, ticker) in enumerate(tickers.items()):
    try:
        # Fetching data
        raw_data = yf.download(ticker, period="5d", interval="1h")['Close']
        gold_data = yf.download("GC=F", period="5d", interval="1h")['Close']
        
        # Calculate Ratios
        ratios_series = raw_data / gold_data
        
        # FIX: Ensure we are using single numbers (floats) for the comparison
        curr = float(ratios_series.iloc[-1])
        avg = float(ratios_series.mean())
        
        # 3. Data Stabilization Logic (Fixed Line 43)
        diff = abs(curr - avg) / avg
        stability = "🟢 Stable" if diff < 0.02 else "🔴 Volatile"
        
        is_buy, bg_color = get_status_styles(name, curr, stability)

        with cols[i]:
            st.markdown(f"""
                <div style="background-color:{bg_color}; padding:20px; border-radius:10px; border: 1px solid #444;">
                    <h3>{name}</h3>
                    <h2>{curr:.4f}</h2>
                    <p>{stability}</p>
                    {f"<b>🔥 BUY SIGNAL</b>" if is_buy else ""}
                </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading {name}: {e}")
