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
st.write("30-Year Analysis | Clean Layout | Data Stabilization")

def get_status_styles(name, ratio):
    is_buy = ratio >= BUY_ZONES[name] if name == "Silver" else ratio <= BUY_ZONES[name]
    bg_color = "#1e4620" if is_buy else "#1E1E1E" 
    status_text = "🔥 BUY SIGNAL" if is_buy else "⏳ HOLD / NEUTRAL"
    return is_buy, bg_color, status_text

# 3. Data Fetching
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
                # Using a single f-string inside st.markdown with unsafe_allow_html=True
                card_html = f"""
                <div style="background-color:{bg_color}; padding:20px; border-radius:12px; border: 1px solid #444; height: 380px; color: white; display: flex; flex-direction: column; justify-content: space-between; font-family: sans-serif;">
                    <div style="text-align: center;">
                        <div style="color:#bbb; text-transform: uppercase; font-size: 0.75em; font-weight: bold;">{name}</div>
                        <div style="margin:10px 0; color:#FFD700; font-size: 2.2em; font-weight: bold;">{curr:.4f}</div>
                    </div>
                    
                    <div style="font-size: 0.85em; background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px; line-height: 1.6;">
                        <div style="display: flex; justify-content: space-between;"><span>Status:</span> <b>{stability_label}</b></div>
                        <div style="display: flex; justify-content: space-between;"><span>30Y High:</span> <b>{hist_high:.2f}</b></div>
                        <div style="display: flex; justify-content: space-between;"><span>30Y Low:</span> <b>{hist_low:.2f}</b></div>
                        <div style="display: flex; justify-content: space-between; color: #888; font-size: 0.9em; border-top: 1px solid #444; margin-top: 5px; padding-top: 5px;"><span>Variance:</span> <b>{diff:.2%}</b></div>
                    </div>

                    <div style="padding: 10px; border: 2px solid {'#fff' if is_buy else '#555'}; text-align: center; font-weight: bold; border-radius: 6px; background: {'rgba(255,255,255,0.15)' if is_buy else 'transparent'};">
                        {status_text}
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
        else:
            cols[i].warning(f"No data: {name}")
    except Exception as e:
        cols[i].error(f"Error: {name}")

st.divider()
st.caption("Standardized Layout | 30Y History | Data Stabilization Active [2026-02-07]")
