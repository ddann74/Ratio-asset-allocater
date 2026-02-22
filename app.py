import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import io
import time

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

# 2. RAW DATA ENGINE (Bypasses all library errors)
@st.cache_data(ttl=3600)
def fetch_raw_data():
    tickers = {
        "Silver": "SI=F", "Platinum": "PL=F", "Copper": "HG=F",
        "S&P 500": "ES=F", "Miners": "GDXJ", "Oil": "CL=F", 
        "Bitcoin": "BTC-USD", "Gold": "GC=F"
    }
    data_dict = {}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for name, sym in tickers.items():
        try:
            # Direct CSV fetch to bypass library build issues
            url = f"https://query1.finance.yahoo.com/v7/finance/download/{sym}?period1=0&period2={int(time.time())}&interval=1wk&events=history"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                df = pd.read_csv(io.StringIO(response.text), index_col='Date', parse_dates=True)
                data_dict[name] = df['Close']
        except: continue
    
    if not data_dict: return pd.DataFrame()
    return pd.concat(data_dict.values(), axis=1, keys=data_dict.keys()).dropna()

full_history = fetch_raw_data()

if full_history.empty:
    st.error("Environment block detected. Direct API fetch failed.")
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
        # 10% Zone Logic (Score >= 0.90)
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
                <p style="font-size: 0.75em; color: #f8fafc; opacity: 0.9;">
                    <b>Value Rank: {a['buy_score']:.0%}</b><br>
                    <span style="font-size: 0.8em; opacity: 0.7;">30Y Mean: {a['mean']:.2f}</span>
                </p>
                <a href="https://www.tradingview.com/chart/?symbol={tv_map[a['name']]}" target="_blank" style="color:#ffffff; text-decoration:none; font-size:0.8em; font-weight:bold; border-bottom: 1px solid white;">Technicals ↗</a>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("History"):
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=a['total_ratios'].index, y=a['total_ratios'].values, name="Full", line=dict(color='rgba(255,255,255,0.1)', width=1)))
                active = a['total_ratios'].loc[:a['curr_date']]
                fig.add_trace(go.Scatter(x=active.index, y=active.values, name="Active", line=dict(color=accent, width=2)))
                fig.add_trace(go.Scatter(x=[a['curr_date']], y=[a['curr']], mode='markers', marker=dict(color='#ff4b4b', size=12, symbol='diamond')))
                fig.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                fig.update_xaxes(showgrid=False, tickfont=dict(size=8, color="#8b949e"), title="Weekly Data")
                fig.update_yaxes(showgrid=True, gridcolor="#30363d", tickfont=dict(size=8, color="#8b949e"), title="Ratio")
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
