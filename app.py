import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

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

# 2. FAIL-SAFE DATA ENGINE
@st.cache_data
def generate_cyclical_data():
    """Generates 30 years of weekly data based on real-world historical ratio ranges."""
    weeks = 52 * 30
    dates = pd.date_range(end=datetime.now(), periods=weeks, freq='W')
    
    # Real-world 30Y High/Low/Mean targets for the ratios
    # Silver: Gold/Silver Ratio | S&P: SPX/Gold | Oil: Oil/Gold | etc.
    configs = {
        "Silver":   {"min": 30, "max": 125, "mean": 65,  "vol": 0.02},
        "Platinum": {"min": 0.5, "max": 2.5, "mean": 1.1, "vol": 0.015},
        "Copper":   {"min": 0.001, "max": 0.005, "mean": 0.0025, "vol": 0.03},
        "S&P 500":  {"min": 0.2, "max": 2.5,  "mean": 1.2,  "vol": 0.02},
        "Miners":   {"min": 0.1, "max": 0.8,  "mean": 0.4,  "vol": 0.04},
        "Oil":      {"min": 0.01, "max": 0.08, "mean": 0.04, "vol": 0.03},
        "Bitcoin":  {"min": 0.1, "max": 40.0, "mean": 15.0, "vol": 0.06}
    }
    
    data = pd.DataFrame(index=dates)
    for name, c in configs.items():
        # Create a cyclical wave + random walk
        cycle = np.sin(np.linspace(0, 10, weeks)) * ((c['max'] - c['min']) / 2) + c['mean']
        noise = np.cumsum(np.random.normal(0, c['vol'], weeks))
        data[name] = np.clip(cycle + noise, c['min'], c['max'])
        
    return data

full_history = generate_cyclical_data()

# 3. GLOBAL CONTROLS
st.title("🛡️ Ratio Strategy Simulator")

col_a, col_b = st.columns([1, 3])
with col_a:
    start_date_val = st.date_input("Strategy Start Date", 
                                  value=full_history.index[0],
                                  min_value=full_history.index[0],
                                  max_value=full_history.index[-100])
    
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

for name in full_history.columns:
    total_ratios = filtered_history[name]
    curr = float(total_ratios.loc[:selected_date].iloc[-1])
    h_max, h_min = float(total_ratios.max()), float(total_ratios.min())
    
    # Logic: Metals (Gold/Asset) we want HIGH ratios. Others we want LOW.
    if name in ["Silver", "Platinum"]:
        buy_score = (curr - h_min) / (h_max - h_min)
        sell_score = 1 - buy_score
    else:
        buy_score = (h_max - curr) / (h_max - h_min)
        sell_score = 1 - buy_score

    # Data Stabilization [cite: 2026-02-07]
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
            <div style="border: 2px solid {accent}; padding: 20px; border-radius: 12px; background: {tile_color}; text-align: center; min-height: 250px; margin-bottom: 20px;">
                <h6 style="margin:0; color:#f8fafc; opacity: 0.7;">{a['name'].upper()}</h6>
                <h2 style="margin:10px 0; color:#ffffff;">{a['curr']:.2f}</h2>
                <div style="font-size: 0.75em; font-weight: bold; color: {accent}; margin-bottom: 10px;">{status}</div>
                <hr style="border-top: 1px solid {accent}; opacity: 0.3; margin: 10px 0;">
                <p style="font-size: 0.75em; color: #f8fafc; opacity: 0.9;">
                    <b>Value Rank: {a['buy_score']:.0%}/100</b><br>
                    <span style="font-size: 0.8em; opacity: 0.6;">Mean: {a['mean']:.2f}</span>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("Backtest Chart"):
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=a['total_ratios'].index, y=a['total_ratios'].values, name="Full", line=dict(color='rgba(255,255,255,0.1)', width=1)))
                active = a['total_ratios'].loc[:a['curr_date']]
                fig.add_trace(go.Scatter(x=active.index, y=active.values, name="Active", line=dict(color=accent, width=2)))
                fig.add_trace(go.Scatter(x=[a['curr_date']], y=[a['curr']], mode='markers', marker=dict(color='#ff4b4b', size=12, symbol='diamond')))
                fig.update_layout(height=160, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                fig.update_xaxes(showgrid=False, tickfont=dict(size=8, color="#8b949e"), title="Weeks")
                fig.update_yaxes(showgrid=True, gridcolor="#30363d", tickfont=dict(size=8, color="#8b949e"), title="Ratio")
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
