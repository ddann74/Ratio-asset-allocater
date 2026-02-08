import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Value Dashboard", layout="wide")
st.title("🏆 Gold-Standard Ratio Dashboard")

# The list of tickers compared to Gold (GC=F)
tickers = {
    "Silver": "SI=F",
    "S&P 500": "ES=F",
    "Dow Jones": "YM=F",
    "Miners": "GDXJ",
    "Oil": "CL=F"
}

def get_data(ticker):
    # Pulls 5 days of hourly data for stabilization check
    df = yf.download(ticker, period="5d", interval="1h")['Close']
    gold = yf.download("GC=F", period="5d", interval="1h")['Close']
    ratio = df / gold
    
    current = ratio.iloc[-1]
    avg = ratio.mean()
    # Your Data Stabilization logic: Is it within 2% of the 5-day mean?
    stability = "🟢 Stable" if abs(current - avg) / avg < 0.02 else "🔴 Volatile"
    return current, stability

cols = st.columns(len(tickers))

for i, (name, ticker) in enumerate(tickers.items()):
    val, status = get_data(ticker)
    with cols[i]:
        st.metric(label=name, value=f"{val:.4f}")
        st.write(f"Status: **{status}**")
