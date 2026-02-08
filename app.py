import streamlit as st
import yfinance as yf

# 1. Configuration & Thresholds
BUY_ZONES = {
    "Silver": 80.0,    # Ratio above 80
    "S&P 500": 1.0,    # Ratio below 1.0
    "Dow Jones": 6.0,  # Ratio below 6.0
    "Miners": 0.05,    # Ratio below 0.05
    "Oil": 0.05        # Ratio below 0.05
}

# 2. App UI
st.set_page_config(page_title="Value Dashboard", layout="wide")
st.title("🏆 Gold-Standard Command Center")

def get_status_styles(name, ratio, stability):
    # Buy Alert Logic
    is_buy = False
    if name == "Silver":
        is_buy = ratio >= BUY_ZONES[name]
    else:
        is_buy = ratio <= BUY_ZONES[name]
    
    color = "#28a745" if is_buy else "#333" # Green if Buy Signal
    return is_buy, color

# 3. Data Fetching & Display
tickers = {"Silver": "SI=F", "S&P 500": "ES=F", "Dow Jones": "YM=F", "Miners": "GDXJ", "Oil": "CL=F"}

cols = st.columns(len(tickers))

for i, (name, ticker) in enumerate(tickers.items()):
    # Hourly data for 5 days for the Stabilization check
    raw_data = yf.download(ticker, period="5d", interval="1h")['Close']
    gold_data = yf.download("GC=F", period="5d", interval="1h")['Close']
    ratios = raw_data / gold_data
    
    curr = ratios.iloc[-1]
    avg = ratios.mean()
    
    # Data Stabilization Indicator
    stability = "🟢 Stable" if abs(curr - avg) / avg < 0.02 else "🔴 Volatile"
    is_buy, bg_color = get_status_styles(name, curr, stability)

    with cols[i]:
        st.markdown(f"""
            <div style="background-color:{bg_color}; padding:20px; border-radius:10px; border: 1px solid #555">
                <h3 style="margin:0">{name}</h3>
                <h2 style="margin:0">{curr:.4f}</h2>
                <p style="margin:0">{stability}</p>
                {f"<b>🔥 BUY SIGNAL</b>" if is_buy else ""}
            </div>
        """, unsafe_allow_value=True)
