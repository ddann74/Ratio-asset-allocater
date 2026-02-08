import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Ratio Command Center", layout="wide", initial_sidebar_state="collapsed")

# Vibrant Slate Theme
st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    .stButton button { 
        width: 100%; border-radius: 8px; height: 3.5em; 
        background-color: #161b22; color: #58a6ff; border: 1px solid #30363d;
        font-weight: 700; transition: 0.3s;
    }
    .stButton button:hover { border-color: #58a6ff; background-color: #1f2937; }
    [data-testid="stExpander"] { border: none !important; }
    h1 { color: #f0f6fc !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. DATA ENGINE
@st.cache_data(ttl=3600)
def fetch_market_data():
    tickers = {"Silver": "SI=F", "S&P 500": "ES=F", "Dow Jones": "YM=F", "Miners": "GDXJ", "Oil": "CL=F", "Gold": "GC=F"}
    data_dict = {}
    for name, sym in tickers.items():
        try:
            df = yf.download(sym, period="max", interval="1mo", progress=False)
            if not df.empty:
                col = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
                data_dict[name] = col
        except: continue
    return pd.concat(data_dict.values(), axis=1, keys=data_dict.keys()).dropna() if data_dict else pd.DataFrame()

full_history = fetch_market_data()

if full_history.empty:
    st.error("Market data unavailable.")
    st.stop()

# 3. NAVIGATION
st.title("📊 Ratio Command Center")
date_labels = full_history.index.strftime('%b %Y').tolist()
min_idx, max_idx = 13, len(date_labels) - 1

if 'sim_index' not in st.session_state:
    st.session_state.sim_index = max_idx

n1, n2, n3 = st.columns([1, 6, 1])
with n1: st.button("◀ OLDER", on_click=lambda: st.session_state.update(sim_index=max(min_idx, st.session_state.sim_index-1)))
with n2: sim_index = st.select_slider("", options=range(len(date_labels)), format_func=lambda x: date_labels[x], key="sim_index")
with n3: st.button("NEWER ▶", on_click=lambda: st.session_state.update(sim_index=min(max_idx, st.session_state.sim_index+1)))

# 4. RATIO LOGIC
curr_hist = full_history.iloc[:sim_index + 1]
assets_to_analyze = []
tv_map = {"Silver": "XAGUSD", "S&P 500": "SPY", "Dow Jones": "DIA", "Miners": "GDXJ", "Oil": "USOIL"}

for name in tv_map.keys():
    ratios = (curr_hist['Gold'] / curr_hist['Silver']) if name == "Silver" else (curr_hist[name] / curr_hist['Gold'])
    ratios = ratios.dropna()
    if len(ratios) < 2: continue

    curr, prev = float(ratios.iloc[-1]), float(ratios.iloc[-2])
    h_max, h_min = float(ratios.max()), float(ratios.min())
    
    # [cite: 2026-02-07] Data Stabilization Indicator
    avg_12m = float(ratios.tail(12).mean())
    is_stable = abs(curr - avg_12m) / avg_12m < 0.05
    
    score = (curr / h_max) if name == "Silver" else (h_min / curr)
    assets_to_analyze.append({"name": name, "ratios": ratios, "curr": curr, "trend": "↑" if curr > prev else "↓",
                               "score": score, "stable": is_stable, "max": h_max, "min": h_min})

# 5. VIBRANT GRID
sorted_assets = sorted(assets_to_analyze, key=lambda x: x['score'], reverse=True)
if sorted_assets:
    cols = st.columns(len(sorted_assets))
    for i, a in enumerate(sorted_assets):
        is_buy = (a['name'] == "Silver" and a['curr'] >= a['max']*0.85) or (a['name'] != "Silver" and a['curr'] <= a['min']*1.15)
        
        # Color Mapping
        accent = "#238636" if is_buy else "#1f6feb" # Emerald for Buy, Royal Blue for Neutral
        stab_bg = "#238636" if a['stable'] else "#d29922" # Emerald vs Amber
        
        with cols[i]:
            st.markdown(f"""
            <div style="border: 1px solid {accent}; padding: 20px; border-radius: 12px; background: #161b22; text-align: center; box-shadow: 5px 5px 15px rgba(0,0,0,0.5);">
                <h5 style="margin:0; color:#8b949e; letter-spacing: 1px;">{a['name'].upper()}</h5>
                <h2 style="margin:10px 0; color:#f0f6fc; font-size: 2em;">{a['trend']} {a['curr']:.2f}</h2>
                <div style="padding: 4px; border-radius: 4px; background: {stab_bg}; font-size: 0.7em; margin-bottom: 15px; font-weight: 900; color: white;">
                    {'🟢 STABLE' if a['stable'] else '🟡 VOLATILE'}
                </div>
                <div style="margin-top: 15px; padding: 12px; border-radius: 8px; background: {accent}22; font-weight: 800; color: {accent}; border: 1px solid {accent};">
                    {'💎 BUY ZONE' if is_buy else 'WATCHING'}
                </div>
                <hr style="border-top: 1px solid #30363d; margin: 15px 0;">
                <p style="font-size: 0.75em; color: #8b949e;">L: {a['min']:.1f} | H: {a['max']:.1f}</p>
                <a href="https://www.tradingview.com/chart/?symbol={tv_map[a['name']]}" target="_blank" style="color:#58a6ff; text-decoration:none; font-size:0.8em; font-weight:bold;">LIVE CHART ↗</a>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("History"):
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=a['ratios'].index, y=a['ratios'].values, line=dict(color='#58a6ff', width=2)))
                fig.add_trace(go.Scatter(x=[a['ratios'].index[-1]], y=[a['ratios'].iloc[-1]], mode='markers', marker=dict(color='#f85149', size=10)))
                fig.update_layout(height=100, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', 
                                  plot_bgcolor='rgba(0,0,0,0)', showlegend=False, xaxis_visible=False, yaxis_visible=False)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
