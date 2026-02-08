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
st.write("Displaying Last Known Prices (Market Closure Resilient)")

def get_status_styles(name, ratio):
    is_buy = ratio >= BUY_ZONES[name] if name == "Silver" else ratio <= BUY_ZONES[name]
    bg_color = "#28a745" if is_buy else "#1E1E1E" 
    return is_buy, bg_color

# 3. Data Fetching
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
        # FIX: Changed interval to '1d' and period to '1mo'
        # This ensures we get the last known daily close even on weekends.
        raw_data = yf.download(ticker, period="1mo", interval="1d")['Close']
        gold_data = yf.download("GC=F", period="1mo", interval="1d")['Close']
        
        # Align and clean data
        ratios_series = (raw_data / gold_data).dropna()
        
        if not ratios_series.empty:
            # Convert to single numbers (prevents Ambiguity Error)
            curr = float(ratios_series.iloc[-1])
            avg = float(ratios_series.mean())
            
            # 4. Data Stabilization Indicator (Added 2026-02-07)
            diff = abs(curr - avg) / avg
            stability_label = "🟢 Stable" if diff < 0.02 else "🔴 Volatile"
            
            is_buy, bg_color = get_status_styles(name, curr)

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
        else:
            with cols[i]:
                st.warning(f"No recent data for {name}")

    except Exception as e:
        with cols[i]:
            st.error(f"Error: {name}")

st.divider()
st.caption("Data source: Yahoo Finance. Includes Data Stabilization logic.")
