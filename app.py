import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Set page configuration
st.set_page_config(page_title="Ratio Asset Allocator", layout="wide")

# 1. DATA FETCHING (With Caching and Error Handling)
@st.cache_data(ttl=3600)
def fetch_all_data():
    tickers = {
        "Silver": "SI=F", "S&P 500": "ES=F", "Dow Jones": "YM=F", 
        "Miners": "GDXJ", "Oil": "CL=F", "Gold": "GC=F"
    }
    data_dict = {}
    for name, sym in tickers.items():
        try:
            # Monthly data is more stable for long-term ratio analysis
            df = yf.download(sym, period="max", interval="1mo", progress=False)
            if not df.empty:
                # Use .iloc[:,0] to handle potential MultiIndex columns from yfinance
                data_dict[name] = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
        except Exception: 
            continue
    
    if not data_dict: return pd.DataFrame()
    return pd.concat(data_dict.values(), axis=1, keys=data_dict.keys()).dropna()

full_history = fetch_all_data()

# CRITICAL ERROR FIX: Prevent st.columns crash if data fails to load
if full_history.empty:
    st.error("❌ Critical Error: Market data unavailable. Check internet connection or API status.")
    st.stop()

# --- 2. NAVIGATION CONTROLS ---
st.title("🚨 Dynamic Asset Ratio Command Center")

date_labels = full_history.index.strftime('%b %Y').tolist()
# Min index set to 13 to allow for 12-month stabilization calculation
min_idx, max_idx = 13, len(date_labels) - 1

if 'sim_index' not in st.session_state:
    st.session_state.sim_index = max_idx

def move_timeline(delta):
    new_idx = st.session_state.sim_index + delta
    if min_idx <= new_idx <= max_idx:
        st.session_state.sim_index = new_idx

nav_l, nav_c, nav_r = st.columns([1, 6, 1])
with nav_l:
    st.button("◀ Prev", on_click=move_timeline, args=(-1,), use_container_width=True)
with nav_c:
    sim_index = st.select_slider(
        "Simulation Timeline", options=range(len(date_labels)),
        format_func=lambda x: date_labels[x], key="sim_index"
    )
with nav_r:
    st.button("Next ▶", on_click=move_timeline, args=(1,), use_container_width=True)

st.divider()

# --- 3. ANALYSIS ENGINE ---
current_history = full_history.iloc[:sim_index + 1]
as_of_date = date_labels[sim_index]
gold_price = float(current_history['Gold'].iloc[-1])

st.subheader(f"Snapshot: {as_of_date} | Gold: ${gold_price:,.2f}")

asset_data = []
# Mapping for TradingView links
tv_map = {"Silver": "XAGUSD", "S&P 500": "SPY", "Dow Jones": "DIA", "Miners": "GDXJ", "Oil": "USOIL"}

for name in ["Silver", "S&P 500", "Dow Jones", "Miners", "Oil"]:
    # Ratio Calculation
    if name == "Silver":
        ratios = (current_history['Gold'] / current_history['Silver']).dropna()
    else:
        ratios = (current_history[name] / current_history['Gold']).dropna()
    
    if len(ratios) < 2: continue

    curr, prev = float(ratios.iloc[-1]), float(ratios.iloc[-2])
    h_max, h_min = float(ratios.max()), float(ratios.min())
    
    # DATA STABILIZATION
    # Check if current value is within 5% of the 12-month moving average
    avg_12m = float(ratios.tail(12).mean())
    is_stable = abs(curr - avg_12m) / avg_12m < 0.05
    stability = "🟢 Stable" if is_stable else "🔴 Volatile"
    
    # Determine Scoring and Thresholds
    if name == "Silver":
        ex_buy, buy, ex_sell = h_max * 0.90, h_max * 0.80, h_min * 1.10
        score = curr / h_max 
    else:
        ex_buy, buy, ex_sell = h_min * 1.10, h_min * 1.20, h_max * 0.90
        score = h_min / curr
        
    asset_data.append({
        "name": name, "ratios": ratios, "curr": curr, "trend": "↑" if curr > prev else "↓",
        "score": score, "stability": stability, "max": h_max, "min": h_min,
        "t": {"ex_buy": ex_buy, "buy": buy, "ex_sell": ex_sell}
    })

# Rank assets by value score
sorted_assets = sorted(asset_data, key=lambda x: x['score'], reverse=True)

# --- 4. GRID DISPLAY ---
if not sorted_assets:
    st.warning("No assets found for the selected date range.")
else:
    cols = st.columns(len(sorted_assets))
    for i, asset in enumerate(sorted_assets):
        # Color coding logic
        is_silver = asset['name'] == "Silver"
        c, t = asset['curr'], asset['t']
        
        if (is_silver and c >= t['ex_buy']) or (not is_silver and c <= t['ex_buy']):
            bg, status = "#004d00", "💎 GEN BUY"
        elif (is_silver and c >= t['buy']) or (not is_silver and c <= t['buy']):
            bg, status = "#1e4620", "🔥 BUY"
        else:
            bg, status = "#1E1E1E", "⏳ HOLD"

        with cols[i]:
            st.markdown(f"""
            <div style="background-color:{bg}; padding:15px; border-radius:10px; border:1px solid #444; color:white; height:340px;">
                <h3 style="text-align:center; margin:0;">{asset['name']}</h3>
                <div style="text-align:center; font-size:1.8em; font-weight:bold; color:#FFD700;">{asset['trend']} {asset['curr']:.2f}</div>
                <hr style="border:0.5px solid #555;">
                <div style="font-size:0.85em; line-height:1.6;">
                    <b>Stability:</b> {asset['stability']}<br>
                    <b>30Y High:</b> {asset['max']:.2f}<br>
                    <b>30Y Low:</b> {asset['min']:.2f}
                </div>
                <div style="margin-top:20px; text-align:center; padding:10px; border:2px solid white; border-radius:5px; font-weight:bold;">{status}</div>
                <div style="text-align:center; margin-top:10px;"><a href="https://www.tradingview.com/chart/?symbol={tv_map[asset['name']]}" target="_blank" style="color:#3BB3E4; text-decoration:none; font-size:0.8em;">View TV Chart ↗️</a></div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("Chart"):
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=asset['ratios'].index, y=asset['ratios'].values, line=dict(color='#FFD700', width=1)))
                
                # RED MARKER for current slider position
                fig.add_trace(go.Scatter(
                    x=[asset['ratios'].index[-1]], y=[asset['ratios'].iloc[-1]],
                    mode='markers', marker=dict(color='#FF4B4B', size=10, symbol='diamond')
                ))
                
                fig.update_layout(height=150, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)', 
                                  plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                fig.update_xaxes(visible=False)
                fig.update_yaxes(visible=False)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
