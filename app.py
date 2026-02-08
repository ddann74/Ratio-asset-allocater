import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Ratio Asset Allocator", layout="wide")

# 1. Data Fetching Logic
@st.cache_data(ttl=3600)
def fetch_all_data():
    tickers = {"Silver": "SI=F", "S&P 500": "ES=F", "Dow Jones": "YM=F", "Miners": "GDXJ", "Oil": "CL=F", "Gold": "GC=F"}
    data_dict = {}
    for name, sym in tickers.items():
        try:
            df = yf.download(sym, period="30y", interval="1mo", progress=False)
            if not df.empty:
                data_dict[name] = df['Close'].squeeze()
        except Exception: continue
    if not data_dict: return pd.DataFrame()
    return pd.concat(data_dict.values(), axis=1, keys=data_dict.keys()).dropna()

full_history = fetch_all_data()

if full_history.empty:
    st.error("No data retrieved. Check your connection.")
    st.stop()

# --- TOP PAGE NAVIGATION CONTROLS ---
st.title("🚨 Dynamic Extreme Value Command Center")

# Create a container for navigation at the top
date_labels = full_history.index.strftime('%b %Y').tolist()
min_idx, max_idx = 13, len(date_labels) - 1

if 'sim_index' not in st.session_state:
    st.session_state.sim_index = max_idx

def change_index(delta):
    new_val = st.session_state.sim_index + delta
    if min_idx <= new_val <= max_idx:
        st.session_state.sim_index = new_val

# Layout for the top controls
nav_col1, nav_col2, nav_col3 = st.columns([1, 6, 1])

with nav_col1:
    st.write("##") # Alignment spacing
    st.button("◀ Prev", on_click=change_index, args=(-1,), use_container_width=True)

with nav_col2:
    sim_index = st.select_slider(
        "Simulation Timeline (Month/Year)",
        options=range(len(date_labels)),
        format_func=lambda x: date_labels[x],
        key="sim_index"
    )

with nav_col3:
    st.write("##") # Alignment spacing
    st.button("Next ▶", on_click=change_index, args=(1,), use_container_width=True)

st.divider()

# 2. State & Price Information
current_history = full_history.iloc[:sim_index + 1]
as_of_date = date_labels[sim_index]
gold_price = float(current_history['Gold'].iloc[-1])

st.subheader(f"Analysis for {as_of_date} | Spot Gold: ${gold_price:,.2f}")

# 3. Calculations & Stabilization Logic
tickers_map = {"Silver": "SI=F", "S&P 500": "ES=F", "Dow Jones": "YM=F", "Miners": "GDXJ", "Oil": "CL=F"}
tv_map = {"Silver": "OANDA:XAGUSD", "S&P 500": "CME_MINI:ES1!", "Dow Jones": "CBOT:YM1!", "Miners": "AMEX:GDXJ", "Oil": "NYMEX:CL1!"}

asset_list = []
for name in tickers_map.keys():
    ratios = (current_history['Gold'] / current_history['Silver']) if name == "Silver" else (current_history[name] / current_history['Gold'])
    ratios = ratios.dropna()
    
    if len(ratios) < 2: continue # Prevents IndexError found in logs

    curr, prev = float(ratios.iloc[-1]), float(ratios.iloc[-2])
    h_max, h_min = float(ratios.max()), float(ratios.min())
    
    # Data Stabilization Indicator [Added 2026-02-07]
    avg_12m = float(ratios.tail(12).mean())
    stability = "🟢 Stable" if (abs(curr - avg_12m) / avg_12m) < 0.05 else "🔴 Volatile"
    
    score = (curr / h_max) if name == "Silver" else (h_min / curr)
        
    asset_list.append({
        "name": name, "ratios": ratios, "curr": curr, "trend": "↑" if curr > prev else "↓",
        "max": h_max, "min": h_min, "score": score, "stability": stability
    })

sorted_assets = sorted(asset_list, key=lambda x: x['score'], reverse=True)

# 4. Grid Display
if sorted_assets:
    cols = st.columns(len(sorted_assets))
    for i, asset in enumerate(sorted_assets):
        with cols[i]:
            st.metric(label=f"{asset['name']} / Gold", value=f"{asset['curr']:.2f}", delta=asset['trend'])
            st.markdown(f"**Status:** {asset['stability']}")
            
            with st.expander("📊 Technical Details"):
                st.write(f"30Y High: {asset['max']:.2f}")
                st.write(f"30Y Low: {asset['min']:.2f}")
                st.markdown(f"[View on TradingView ↗️](https://www.tradingview.com/chart/?symbol={tv_map[asset['name']]})")
else:
    st.warning("Insufficient data for the selected date.")
