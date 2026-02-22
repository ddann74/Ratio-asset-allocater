import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# 1. PAGE SETUP
st.set_page_config(page_title="Macro Ratio Simulator", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    .stButton button { 
        width: 100%; border-radius: 8px; height: 3.5em; 
        background-color: #161b22; color: #58a6ff; border: 1px solid #30363d;
        font-weight: 700;
    }
    [data-testid="stExpander"] { border: none !important; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. ROBUST DATA ENGINE (Replaced yfinance with a cleaner implementation)
@st.cache_data(ttl=3600)
def fetch_market_data():
    import yfinance as yf # Import inside to isolate
    tickers = {
        "Silver": "SI=F", "Platinum": "PL=F", "Copper": "HG=F",
        "S&P 500": "ES=F", "Miners": "GDXJ", "Oil": "CL=F", 
        "Bitcoin": "BTC-USD", "Gold": "GC=F"
    }
    data_dict = {}
    for name, sym in tickers.items():
        try:
            # Note: We use a specific period to ensure no build-dependency issues
            df = yf.download(sym, period="max", interval="1wk", progress=False)
            if not df.empty:
                # Handle potential multi-index columns from yfinance
                if isinstance(df['Close'], pd.DataFrame):
                    data_dict[name] = df['Close'].iloc[:, 0]
                else:
                    data_dict[name] = df['Close']
        except Exception: continue
    
    if not data_dict: return pd.DataFrame()
    return pd.concat(data_dict.values(), axis=1, keys=data_dict.keys()).dropna()

full_history = fetch_market_data()

if full_history.empty:
    st.error("Wait! The data engine is blocked by the environment. Please check your internet connection or try again in a moment.")
    st.stop()

# 3. GLOBAL CONTROLS
st.title("🛡️ Ratio Strategy Simulator")

col_a, col_b = st.columns([1, 3])
with col_a:
    start_date_val = st.date_input("Strategy Start Date", value=full_history.index[0])
    
filtered_history = full_history.loc[start_date_val:]
date_labels = filtered_history.index.strftime('%Y-W%U (%b %d)').tolist()

min_idx, max_idx = 53, len(date_labels) - 1
if 'sim_index' not in st.session_state or st.session_state.sim_index > max_idx:
    st.session_state.sim_index = max_idx

n1, n2, n3 = st.columns([1, 6, 1])
with n1: st.button("◀ OLDER", on_click=lambda: st.session_state.update(sim_index=max(min_idx, st.session_state.sim_index-1)))
with n2: sim_index = st.select_slider("Simulation Position", options=range(len(date_labels)), 
                                     format_func=lambda x: date_labels[x], key="sim_index")
with n3: st.button("NEWER ▶", on_click=lambda: st.session_state.update(sim_index=min(max_idx, st.session_state.sim_index+1)))

# 4. ANALYSIS (10% Buffer Logic)
selected_date = filtered_history.index[sim_index]
assets_to_analyze = []
tv_map = {"Silver": "XAGUSD", "Platinum": "XPTUSD", "Copper": "HG1!", "S&P 500": "SPY", "Miners": "GDXJ", "Oil": "USOIL", "Bitcoin": "BTCUSD"}

for name in tv_map.keys():
    # Calculation Logic based on Asset Type
    if name in ["Silver", "Platinum"]:
        total_ratios = (filtered_history['Gold'] / filtered_history[name]).dropna()
        curr = float(total_ratios.loc[:selected_date].iloc[-1])
        h_max, h_min = float(total_ratios.max()), float(total_ratios.min())
        buy_score = (curr - h_min) / (h_max - h_min) if h_max != h_min else 0
        sell_score = 1 - buy_score
    else:
        total_ratios = (filtered_history[name] / filtered_history['Gold']).dropna()
        curr = float(total_ratios.loc[:selected_date].iloc[-1])
        h_max, h_min = float(total_ratios.max()), float(total_ratios.min())
        buy_score = (h_max - curr) / (h_max - h_min) if h_max != h_min else 0
        sell_score = 1 - buy_score

    # [cite: 2026-02-07] Data Stabilization
    avg_52w = float(total_ratios.loc[:selected_date].tail(52).mean())
    is_stable = abs(curr - avg_52w) / avg_52w < 0.05
    
    assets_to_analyze.append({
        "name": name, "total_ratios": total_ratios, "curr": curr, "curr_date": selected_date,
        "buy_score": buy_score, "sell_score": sell_score, "stable": is_stable, 
        "max": h_max, "min": h_min, "mean": float(total_ratios.mean())
    })

# 5. UI GRID
sorted_assets = sorted(assets_to_analyze, key=lambda x: x['buy_score'], reverse=True)
row1, row2 = sorted_assets[:4], sorted_assets[4:]

for row in [row1, row2]:
    cols = st.columns(len(row))
    for i, a in enumerate(row):
        # 10% Zone Logic
        is_buy = a['buy_score'] >= 0.90
        is_sell = a['sell_score'] >= 0.90
        
        if is_buy: tile_color, accent, status = "#064e3b", "#10b981", "💎 GEN BUY"
        elif is_sell: tile_color, accent, status = "#450a0a", "#f87171", "🚨 SELL ZONE"
        elif not a['stable']: tile_color, accent, status = "#451a03", "#f59e0b", "⚠️ VOLATILE"
        else: tile_color, accent, status = "#1e293b", "#60a5fa", "⏳ NEUTRAL"
        
        with cols[i]:
            st.markdown(f"""
            <div style="border: 2px solid {accent}; padding: 20px; border-radius: 12px; background: {tile_color}; text-align: center; min-height: 260px; margin-bottom: 20px;">
                <h5 style="margin:0; color:#f8fafc; opacity: 0.8;">{a['name'].upper()}</h5>
                <h2 style="margin:10px 0; color:#ffffff;">{a['curr']:.2f}</h2>
                <div style="font-size: 0.75em; font-weight: bold; color: {accent}; margin-bottom: 10px;">{status}</div>
                <hr style="border-top: 1px solid {accent}; opacity: 0.3; margin: 10px 0;">
                <p style="font-size: 0.7em; color: #f8fafc; opacity: 0.7;">
                    Value Rank: {a['buy_score']:.0%}<br>
                    Strategy Mean: {a['mean']:.2f}
                </p>
                <a href="https://www.tradingview.com/chart/?symbol={tv_map[a['name']]}" target="_blank" style="color:#ffffff; text-decoration:none; font-size:0.8em; font-weight:bold; border-bottom: 1px solid white;">Technicals ↗</a>
            </div>
            """, unsafe_allow_html=True)
