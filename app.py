import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

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

# 2. DATA ENGINE
@st.cache_data(ttl=3600)
def fetch_market_data():
    tickers = {
        "Silver": "SI=F", "Platinum": "PL=F", "Copper": "HG=F",
        "S&P 500": "ES=F", "Miners": "GDXJ", "Oil": "CL=F", 
        "Bitcoin": "BTC-USD", "Gold": "GC=F"
    }
    data_dict = {}
    for name, sym in tickers.items():
        try:
            df = yf.download(sym, period="max", interval="1wk", progress=False)
            if not df.empty:
                col = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
                data_dict[name] = col
        except: continue
    return pd.concat(data_dict.values(), axis=1, keys=data_dict.keys()).dropna() if data_dict else pd.DataFrame()

full_history = fetch_market_data()

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
    if name in ["Silver", "Platinum"]:
        total_ratios = (filtered_history['Gold'] / filtered_history[name]).dropna()
        # For these, HIGH ratio = Cheap, LOW ratio = Expensive
        curr = float(total_ratios.loc[:selected_date].iloc[-1])
        h_max, h_min = float(total_ratios.max()), float(total_ratios.min())
        score = curr / h_max
        sell_score = h_min / curr
    else:
        total_ratios = (filtered_history[name] / filtered_history['Gold']).dropna()
        # For these, LOW ratio = Cheap, HIGH ratio = Expensive
        curr = float(total_ratios.loc[:selected_date].iloc[-1])
        h_max, h_min = float(total_ratios.max()), float(total_ratios.min())
        score = h_min / curr
        sell_score = curr / h_max

    # Data Stabilization [cite: 2026-02-07]
    avg_52w = float(total_ratios.loc[:selected_date].tail(52).mean())
    is_stable = abs(curr - avg_52w) / avg_52w < 0.05
    
    assets_to_analyze.append({
        "name": name, "total_ratios": total_ratios, "curr": curr, "curr_date": selected_date,
        "score": score, "sell_score": sell_score, "stable": is_stable, "max": h_max, "min": h_min, "mean": float(total_ratios.mean())
    })

# 5. UI GRID
sorted_assets = sorted(assets_to_analyze, key=lambda x: x['score'], reverse=True)
row1, row2 = sorted_assets[:4], sorted_assets[4:]

for row in [row1, row2]:
    cols = st.columns(len(row))
    for i, a in enumerate(row):
        # Trigger zones based on 10% (Score > 0.90)
        is_buy = a['score'] >= 0.90
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
                    Value Score: {a['score']:.2f}<br>
                    30Y Mean: {a['mean']:.2f}
                </p>
                <a href="https://www.tradingview.com/chart/?symbol={tv_map[a['name']]}" target="_blank" style="color:#ffffff; text-decoration:none; font-size:0.8em; font-weight:bold; border-bottom: 1px solid white;">Technicals ↗</a>
            </div>
            """, unsafe_allow_html=True)
