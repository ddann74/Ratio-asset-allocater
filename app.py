import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. PAGE SETUP
st.set_page_config(page_title="Ratio Allocator Pro", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for polished layout and fixed-height cards
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton button { width: 100%; border-radius: 5px; height: 3em; background-color: #262730; }
    [data-testid="stExpander"] { border: none !important; box-shadow: none !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATA ENGINE (With MultiIndex and Deprecation Fixes)
@st.cache_data(ttl=3600)
def fetch_data():
    tickers = {"Silver": "SI=F", "S&P 500": "ES=F", "Dow Jones": "YM=F", "Miners": "GDXJ", "Oil": "CL=F", "Gold": "GC=F"}
    data = {}
    for name, sym in tickers.items():
        try:
            df = yf.download(sym, period="max", interval="1mo", progress=False)
            if not df.empty:
                # Handle MultiIndex columns and single-ticker DataFrames
                data[name] = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
        except: continue
    return pd.concat(data.values(), axis=1, keys=data.keys()).dropna() if data else pd.DataFrame()

full_history = fetch_data()

# Stop app if data is missing to avoid ColumnSpecErrors later
if full_history.empty:
    st.error("Critical Error: Market data unavailable. Please check your internet connection.")
    st.stop()

# 3. GLOBAL NAVIGATION
st.title("🛡️ Ratio Asset Allocator")
date_labels = full_history.index.strftime('%b %Y').tolist()

# Min index 13 ensures enough data for 12-month stabilization calculation
min_idx, max_idx = 13, len(date_labels) - 1
if 'sim_index' not in st.session_state:
    st.session_state.sim_index = max_idx

nav_l, nav_c, nav_r = st.columns([1, 6, 1])
with nav_l: st.button("◀ Older", on_click=lambda: st.session_state.update(sim_index=max(min_idx, st.session_state.sim_index-1)))
with nav_c:
    sim_index = st.select_slider("Historical Timeline", options=range(len(date_labels)), 
                                 format_func=lambda x: date_labels[x], key="sim_index")
with nav_r: st.button("Newer ▶", on_click=lambda: st.session_state.update(sim_index=min(max_idx, st.session_state.sim_index+1)))

# 4. ANALYSIS & STABILIZATION LOGIC
curr_hist = full_history.iloc[:sim_index + 1]
# Use .iloc[-1] to avoid float-conversion FutureWarning
gold_px = float(curr_hist['Gold'].iloc[-1]) 

assets = []
tv_map = {"Silver": "XAGUSD", "S&P 500": "SPY", "Dow Jones": "DIA", "Miners": "GDXJ", "Oil": "USOIL"}

for name in tv_map.keys():
    # Ratios are Gold/Asset for Silver, Asset/Gold for others
    ratios = (curr_hist['Gold'] / curr_hist['Silver']) if name == "Silver" else (curr_hist[name] / curr_hist['Gold'])
    ratios = ratios.dropna()
    if len(ratios) < 2: continue

    curr, prev = float(ratios.iloc[-1]), float(ratios.iloc[-2])
    h_max, h_min = float(ratios.max()), float(ratios.min())
    
    # Data Stabilization Indicator
    # Compares current ratio to the 12-month moving average
    avg_12m = float(ratios.tail(12).mean())
    is_stable = abs(curr - avg_12m) / avg_12m < 0.05
    
    # Calculate Value Score for Grid Ranking
    score = (curr / h_max) if name == "Silver" else (h_min / curr)
    assets.append({"name": name, "ratios": ratios, "curr": curr, "trend": "↑" if curr > prev else "↓", 
                   "score": score, "stable": is_stable, "max": h_max, "min": h_min})

# 5. UI GRID DISPLAY
sorted_assets = sorted(assets, key=lambda x: x['score'], reverse=True)

# Check for empty list to prevent st.columns(0) crash
if sorted_assets:
    cols = st.columns(len(sorted_assets)) 
    for i, a in enumerate(sorted_assets):
        # Value Logic Thresholds
        is_buy = (a['name'] == "Silver" and a['curr'] >= a['max']*0.85) or (a['name'] != "Silver" and a['curr'] <= a['min']*1.15)
        border_col = "#2ecc71" if is_buy else "#34495e"
        status_txt = "💎 HIGH VALUE" if is_buy else "⏳ NEUTRAL"

        with cols[i]:
            st.markdown(f"""
            <div style="border: 2px solid {border_col}; padding: 15px; border-radius: 12px; background: #161b22; min-height: 300px; text-align: center;">
                <h4 style="margin:0; color:#8b949e;">{a['name']}</h4>
                <h2 style="margin:10px 0; color:#f0f6fc;">{a['trend']} {a['curr']:.2f}</h2>
                <div style="padding: 5px; border-radius: 5px; background: {'#064a2e' if a['stable'] else '#4a0606'}; font-size: 0.75em; margin-bottom: 15px; font-weight: bold;">
                    {'🟢 STABLE' if a['stable'] else '🔴 VOLATILE'}
                </div>
                <p style="font-size: 0.8em; color: #8b949e; line-height: 1;">Range: {a['min']:.1f} — {a['max']:.1f}</p>
                <div style="margin-top: 20px; font-weight: bold; color: {border_col};">{status_txt}</div>
                <hr style="border-top: 1px solid #30363d;">
                <a href="https://www.tradingview.com/chart/?symbol={tv_map[a['name']]}" target="_blank" style="color:#58a6ff; text-decoration:none; font-size:0.8em;">Technical Chart ↗</a>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("Historical View"):
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=a['ratios'].index, y=a['ratios'].values, line=dict(color='#f0f6fc', width=1.5)))
                # RED MARKER for timeline position
                fig.add_trace(go.Scatter(x=[a['ratios'].index[-1]], y=[a['ratios'].iloc[-1]], mode='markers', marker=dict(color='#ff4b4b', size=8)))
                fig.update_layout(height=120, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', 
                                  plot_bgcolor='rgba(0,0,0,0)', showlegend=False, xaxis_visible=False, yaxis_visible=False)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
