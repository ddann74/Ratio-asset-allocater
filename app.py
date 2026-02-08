import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Ratio Command Center", layout="wide", initial_sidebar_state="collapsed")

# Custom Matte Midnight CSS
st.markdown("""
    <style>
    .main { background-color: #0f1115; }
    .stButton button { 
        width: 100%; border-radius: 6px; height: 3.5em; 
        background-color: #1c1f26; color: #a0aec0; border: 1px solid #2d3748;
        font-weight: 600;
    }
    .stButton button:hover { border-color: #4a5568; color: #edf2f7; }
    [data-testid="stExpander"] { border: none !important; background-color: transparent !important; }
    hr { border-top: 1px solid #2d3748 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. ROBUST DATA ENGINE
@st.cache_data(ttl=3600)
def fetch_market_data():
    tickers = {
        "Silver": "SI=F", "S&P 500": "ES=F", "Dow Jones": "YM=F", 
        "Miners": "GDXJ", "Oil": "CL=F", "Gold": "GC=F"
    }
    data_dict = {}
    for name, sym in tickers.items():
        try:
            df = yf.download(sym, period="max", interval="1mo", progress=False)
            if not df.empty:
                # Handle MultiIndex and Series
                col = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
                data_dict[name] = col
        except Exception: 
            continue
    
    if not data_dict: return pd.DataFrame()
    return pd.concat(data_dict.values(), axis=1, keys=data_dict.keys()).dropna()

full_history = fetch_market_data()

# Prevent column crash if data fails
if full_history.empty:
    st.error("❌ Data Sync Failed. Please check internet connection.")
    st.stop()

# 3. GLOBAL TIMELINE NAVIGATION
st.title("🛡️ Ratio Asset Allocator")
date_labels = full_history.index.strftime('%b %Y').tolist()

# Start at idx 13 to ensure 12 months of back-data for stability logic
min_idx, max_idx = 13, len(date_labels) - 1
if 'sim_index' not in st.session_state:
    st.session_state.sim_index = max_idx

nav_l, nav_c, nav_r = st.columns([1, 6, 1])
with nav_l: 
    st.button("◀ OLDER", on_click=lambda: st.session_state.update(sim_index=max(min_idx, st.session_state.sim_index-1)))
with nav_c:
    sim_index = st.select_slider("Timeline Snapshot", options=range(len(date_labels)), 
                                 format_func=lambda x: date_labels[x], key="sim_index")
with nav_r: 
    st.button("NEWER ▶", on_click=lambda: st.session_state.update(sim_index=min(max_idx, st.session_state.sim_index+1)))

st.divider()

# 4. RATIO & STABILITY LOGIC
curr_hist = full_history.iloc[:sim_index + 1]
gold_px = float(curr_hist['Gold'].iloc[-1]) #

assets_to_analyze = []
tv_map = {"Silver": "XAGUSD", "S&P 500": "SPY", "Dow Jones": "DIA", "Miners": "GDXJ", "Oil": "USOIL"}

for name in tv_map.keys():
    # Gold is the denominator for most, numerator for Silver (G/S ratio)
    if name == "Silver":
        ratios = (curr_hist['Gold'] / curr_hist['Silver']).dropna()
    else:
        ratios = (curr_hist[name] / curr_hist['Gold']).dropna()
    
    if len(ratios) < 2: continue

    curr, prev = float(ratios.iloc[-1]), float(ratios.iloc[-2])
    h_max, h_min = float(ratios.max()), float(ratios.min())
    
    # DATA STABILIZATION INDICATOR
    # Neutral/Stable if within 5% of its 12-month mean
    avg_12m = float(ratios.tail(12).mean())
    is_stable = abs(curr - avg_12m) / avg_12m < 0.05
    
    # Scoring for Grid Sorting (Value Search)
    score = (curr / h_max) if name == "Silver" else (h_min / curr)
    
    assets_to_analyze.append({
        "name": name, "ratios": ratios, "curr": curr, "trend": "↑" if curr > prev else "↓",
        "score": score, "stable": is_stable, "max": h_max, "min": h_min
    })

# 5. UI DISPLAY GRID
sorted_assets = sorted(assets_to_analyze, key=lambda x: x['score'], reverse=True)

# Prevent st.columns(0)
if not sorted_assets:
    st.warning("Insufficient historical data for this period.")
else:
    cols = st.columns(len(sorted_assets))
    for i, a in enumerate(sorted_assets):
        # High Value Logic (Generational Buy zones)
        is_buy = (a['name'] == "Silver" and a['curr'] >= a['max']*0.85) or \
                 (a['name'] != "Silver" and a['curr'] <= a['min']*1.15)
        
        accent = "#38a169" if is_buy else "#4a5568"
        status_box = "#1a365d" if is_buy else "#171923"

        with cols[i]:
            st.markdown(f"""
            <div style="border: 1px solid {accent}; padding: 20px; border-radius: 12px; background: #1a202c; min-height: 310px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
                <h5 style="margin:0; color:#718096; font-size: 0.9em;">{a['name'].upper()}</h5>
                <h2 style="margin:12px 0; color:#e2e8f0; font-family: monospace;">{a['trend']} {a['curr']:.2f}</h2>
                <div style="padding: 5px; border-radius: 4px; background: {'#22543d' if a['stable'] else '#742a2a'}; font-size: 0.75em; margin-bottom: 12px; font-weight: bold; color: white;">
                    {'🟢 STABLE' if a['stable'] else '🔴 VOLATILE'}
                </div>
                <p style="font-size: 0.8em; color: #718096; margin-bottom: 20px;">Range: {a['min']:.1f} — {a['max']:.1f}</p>
                <div style="padding: 10px; border-radius: 6px; background: {status_box}; font-weight: 800; color: {accent if is_buy else '#cbd5e1'}; border: 1px solid {accent};">
                    {'💎 GEN BUY' if is_buy else 'NEUTRAL'}
                </div>
                <hr style="margin: 20px 0;">
                <a href="https://www.tradingview.com/chart/?symbol={tv_map[a['name']]}" target="_blank" style="color:#63b3ed; text-decoration:none; font-size:0.8em; font-weight: 600;">TECHNICALS ↗</a>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("History"):
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=a['ratios'].index, y=a['ratios'].values, line=dict(color='#4a5568', width=1.5)))
                # Red Marker for simulation point
                fig.add_trace(go.Scatter(x=[a['ratios'].index[-1]], y=[a['ratios'].iloc[-1]], mode='markers', marker=dict(color='#e53e3e', size=8)))
                fig.update_layout(height=110, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', 
                                  plot_bgcolor='rgba(0,0,0,0)', showlegend=False, xaxis_visible=False, yaxis_visible=False)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
