import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Set page configuration for a wide dashboard layout
st.set_page_config(page_title="Ratio Asset Allocator", layout="wide")

# 1. DATA FETCHING (Optimized with Caching)
@st.cache_data(ttl=3600)
def fetch_all_data():
    tickers = {
        "Silver": "SI=F", "S&P 500": "ES=F", "Dow Jones": "YM=F", 
        "Miners": "GDXJ", "Oil": "CL=F", "Gold": "GC=F"
    }
    data_dict = {}
    for name, sym in tickers.items():
        try:
            # Monthly interval to ensure smooth slider transitions
            df = yf.download(sym, period="30y", interval="1mo", progress=False)
            if not df.empty:
                # Use .squeeze() to ensure we have a Series for easy manipulation
                data_dict[name] = df['Close'].squeeze()
        except Exception: 
            continue
    
    if not data_dict: 
        return pd.DataFrame()
    
    # Combine all assets into one DataFrame and drop rows with missing values
    return pd.concat(data_dict.values(), axis=1, keys=data_dict.keys()).dropna()

full_history = fetch_all_data()

# Error handling for empty data (Prevents st.columns crash) 
if full_history.empty:
    st.error("❌ Critical Error: Unable to fetch market data. Please check your internet connection.")
    st.stop()

# --- 2. TOP-LEVEL NAVIGATION CONTROLS ---
st.title("🚨 Dynamic Extreme Value Command Center")

# Prepare date labels for the slider (e.g., "Jan 2024")
date_labels = full_history.index.strftime('%b %Y').tolist()
min_idx = 13 # Minimum required for 12-month stabilization calculation
max_idx = len(date_labels) - 1

# Initialize session state for the slider index if not already present
if 'sim_index' not in st.session_state:
    st.session_state.sim_index = max_idx

# Function for arrow button controls
def change_index(delta):
    new_val = st.session_state.sim_index + delta
    if min_idx <= new_val <= max_idx:
        st.session_state.sim_index = new_val

# Control Bar UI Layout
nav_col1, nav_col2, nav_col3 = st.columns([1, 6, 1])

with nav_col1:
    st.write("##") # Vertical alignment spacing
    st.button("◀ Prev", on_click=change_index, args=(-1,), use_container_width=True)

with nav_col2:
    sim_index = st.select_slider(
        "Simulation Timeline (Backtest Perspective)",
        options=range(len(date_labels)),
        format_func=lambda x: date_labels[x],
        key="sim_index"
    )

with nav_col3:
    st.write("##")
    st.button("Next ▶", on_click=change_index, args=(1,), use_container_width=True)

st.divider()

# --- 3. ANALYSIS ENGINE ---
# Slice data based on the slider selection
current_history = full_history.iloc[:sim_index + 1]
as_of_date = date_labels[sim_index]
gold_price = float(current_history['Gold'].iloc[-1]) # Fix for FutureWarning 

st.subheader(f"Current Environment: {as_of_date} | Gold Price: ${gold_price:,.2f}")

tickers_map = {"Silver": "SI=F", "S&P 500": "ES=F", "Dow Jones": "YM=F", "Miners": "GDXJ", "Oil": "CL=F"}
tv_map = {"Silver": "OANDA:XAGUSD", "S&P 500": "CME_MINI:ES1!", "Dow Jones": "CBOT:YM1!", "Miners": "AMEX:GDXJ", "Oil": "NYMEX:CL1!"}

asset_list = []
for name in tickers_map.keys():
    # Calculation Logic: Gold/Silver (Inverted) vs Others/Gold
    ratios = (current_history['Gold'] / current_history['Silver']) if name == "Silver" else (current_history[name] / current_history['Gold'])
    ratios = ratios.dropna()
    
    if len(ratios) < 2: continue # Prevents IndexError 

    curr, prev = float(ratios.iloc[-1]), float(ratios.iloc[-2])
    h_max, h_min = float(ratios.max()), float(ratios.min())
    
    # DATA STABILIZATION INDICATOR
    avg_12m = float(ratios.tail(12).mean())
    stability_val = abs(curr - avg_12m) / avg_12m
    stability = "🟢 Stable" if stability_val < 0.05 else "🔴 Volatile"
    
    # Signal Thresholds
    if name == "Silver":
        ex_buy, reg_buy, ex_sell = h_max * 0.90, h_max * 0.80, h_min * 1.10
        score = curr / h_max 
    else:
        ex_buy, reg_buy, ex_sell = h_min * 1.10, h_min * 1.20, h_max * 0.90
        score = h_min / curr
        
    asset_list.append({
        "name": name, "ratios": ratios, "curr": curr, "trend": "↑" if curr > prev else "↓",
        "max": h_max, "min": h_min, "score": score, "stability": stability,
        "thresholds": {"ex_buy": ex_buy, "buy": reg_buy, "ex_sell": ex_sell}
    })

# Rank assets by best value score
sorted_assets = sorted(asset_list, key=lambda x: x['score'], reverse=True)

# --- 4. DASHBOARD DISPLAY ---
if sorted_assets:
    cols = st.columns(len(sorted_assets))
    for i, asset in enumerate(sorted_assets):
        name, ratios, curr, t = asset['name'], asset['ratios'], asset['curr'], asset['thresholds']
        
        # UI/UX: Determine Card Color Based on Signals
        if name == "Silver":
            if curr >= t['ex_buy']: bg, label = "#004d00", "💎 GENERATIONAL BUY"
            elif curr >= t['buy']: bg, label = "#1e4620", "🔥 BUY SIGNAL"
            elif curr <= t['ex_sell']: bg, label = "#900C3F", "⚠️ EXTREME SELL"
            else: bg, label = "#1E1E1E", "⏳ HOLD"
        else:
            if curr <= t['ex_buy']: bg, label = "#004d00", "💎 GENERATIONAL BUY"
            elif curr <= t['buy']: bg, label = "#1e4620", "🔥 BUY SIGNAL"
            elif curr >= t['ex_sell']: bg, label = "#900C3F", "⚠️ EXTREME SELL"
            else: bg, label = "#1E1E1E", "⏳ HOLD"

        with cols[i]:
            # Main Asset Card
            st.markdown(f"""
            <div style="background-color:{bg}; padding:15px; border-radius:10px; border:1px solid #444; color:white; height:380px; display:flex; flex-direction:column; justify-content:space-between; margin-bottom: 10px;">
                <div style="text-align:center;">
                    <div style="font-size:0.8em; color:#bbb;">{name} / Gold Ratio</div>
                    <div style="font-size:2em; font-weight:bold; color:#FFD700;">{asset['trend']} {curr:.2f}</div>
                </div>
                <div style="background:rgba(0,0,0,0.3); padding:8px; border-radius:5px; font-size:0.75em;">
                    <div style="display:flex; justify-content:space-between;"><span>Stabilization:</span><b>{asset['stability']}</b></div>
                    <div style="display:flex; justify-content:space-between;"><span>30Y Max:</span><b>{asset['max']:.2f}</b></div>
                    <div style="display:flex; justify-content:space-between;"><span>30Y Min:</span><b>{asset['min']:.2f}</b></div>
                </div>
                <div style="text-align:center; padding:10px; border:2px solid white; font-weight:bold; border-radius:5px; background:rgba(255,255,255,0.1);">
                    {label}
                </div>
                <div style="text-align:center; margin-top:5px;">
                    <a href="https://www.tradingview.com/chart/?symbol={tv_map[name]}" target="_blank" style="color:#3BB3E4; text-decoration:none; font-size:0.8em; font-weight:bold;">🔍 TRADINGVIEW CHART ↗️</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Integrated Visual Chart with Current Marker
            with st.expander("📊 Technical Visual Range"):
                fig = go.Figure()
                
                # Full Historical Trend
                fig.add_trace(go.Scatter(x=ratios.index, y=ratios.values, line=dict(color='#FFD700', width=1)))
                
                # NEW: Current Position Marker (Red Diamond)
                fig.add_trace(go.Scatter(
                    x=[ratios.index[-1]], 
                    y=[ratios.iloc[-1]],
                    mode='markers',
                    marker=dict(color='#FF4B4B', size=10, symbol='diamond', line=dict(width=1, color='white'))
                ))
                
                # Signal Threshold Lines
                fig.add_hline(y=t['buy'], line_dash="dash", line_color="green", opacity=0.5)
                fig.add_hline(y=t['ex_buy'], line_dash="solid", line_color="lime", opacity=0.7)
                
                fig.update_layout(
                    height=180, 
                    margin=dict(l=0, r=0, t=10, b=0), 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)', 
                    font=dict(color="white"), 
                    showlegend=False,
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=False)
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
else:
    st.warning("⚠️ Insufficient data available for the chosen simulation date.")
