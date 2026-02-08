import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. PAGE SETUP
st.set_page_config(page_title="Asset Ratio Command", layout="wide", initial_sidebar_state="collapsed")

# Theme CSS
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
st.title("🛡️ Ratio Command Center")
date_labels = full_history.index.strftime('%b %Y').tolist()
min_idx, max_idx = 13, len(date_labels) - 1

if 'sim_index' not in st.session_state:
    st.session_state.sim_index = max_idx

n1, n2, n3 = st.columns([1, 6, 1])
with n1: st.button("◀ OLDER", on_click=lambda: st.session_state.update(sim_index=max(min_idx, st.session_state.sim_index-1)))
with n2: sim_index = st.select_slider("", options=range(len(date_labels)), format_func=lambda x: date_labels[x], key="sim_index")
with n3: st.button("NEWER ▶", on_click=lambda: st.session_state.update(sim_index=min(max_idx, st.session_state.sim_index+1)))

# 4. ANALYSIS
curr_hist = full_history.iloc[:sim_index + 1]
assets_to_analyze = []
tv_map = {"Silver": "XAGUSD", "S&P 500": "SPY", "Dow Jones": "DIA", "Miners": "GDXJ", "Oil": "USOIL"}

for name in tv_map.keys():
    ratios = (curr_hist['Gold'] / curr_hist['Silver']) if name == "Silver" else (curr_hist[name] / curr_hist['Gold'])
    ratios = ratios.dropna()
    if len(ratios) < 2: continue

    curr, prev = float(ratios.iloc[-1]), float(ratios.iloc[-2])
    h_max, h_min = float(ratios.max()), float(ratios.min())
    
    # [cite: 2026-02-07] Data Stabilization
    avg_12m = float(ratios.tail(12).mean())
    is_stable = abs(curr - avg_12m) / avg_12m < 0.05
    
    score = (curr / h_max) if name == "Silver" else (h_min / curr)
    assets_to_analyze.append({"name": name, "ratios": ratios, "curr": curr, "trend": "↑" if curr > prev else "↓",
                               "score": score, "stable": is_stable, "max": h_max, "min": h_min})

# 5. COLOURISED GRID
sorted_assets = sorted(assets_to_analyze, key=lambda x: x['score'], reverse=True)

if sorted_assets:
    cols = st.columns(len(sorted_assets))
    for i, a in enumerate(sorted_assets):
        is_buy = (a['name'] == "Silver" and a['curr'] >= a['max']*0.85) or (a['name'] != "Silver" and a['curr'] <= a['min']*1.15)
        
        # Tile Coloring Logic
        if is_buy:
            tile_color = "#064e3b" # Deep Emerald
            accent_color = "#10b981"
            status_text = "💎 GEN BUY"
        elif not a['stable']:
            tile_color = "#451a03" # Deep Amber/Brown
            accent_color = "#f59e0b"
            status_text = "⚠️ VOLATILE"
        else:
            tile_color = "#1e293b" # Slate Blue
            accent_color = "#60a5fa"
            status_text = "⏳ NEUTRAL"
        
        with cols[i]:
            st.markdown(f"""
            <div style="border: 2px solid {accent_color}; padding: 20px; border-radius: 12px; background: {tile_color}; text-align: center; min-height: 280px;">
                <h5 style="margin:0; color:#f8fafc; opacity: 0.8;">{a['name'].upper()}</h5>
                <h2 style="margin:10px 0; color:#ffffff;">{a['trend']} {a['curr']:.2f}</h2>
                <div style="font-size: 0.75em; font-weight: bold; color: {accent_color}; margin-bottom: 15px;">
                    {status_text}
                </div>
                <hr style="border-top: 1px solid {accent_color}; opacity: 0.3; margin: 15px 0;">
                <p style="font-size: 0.7em; color: #f8fafc; opacity: 0.7;">30Y Low: {a['min']:.1f} | High: {a['max']:.1f}</p>
                <a href="https://www.tradingview.com/chart/?symbol={tv_map[a['name']]}" target="_blank" style="color:#ffffff; text-decoration:none; font-size:0.8em; font-weight:bold; border-bottom: 1px solid white;">Technical View ↗</a>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("History Chart"):
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=a['ratios'].index, y=a['ratios'].values, name="Ratio", line=dict(color=accent_color, width=2)))
                
                # Highlight current point
                fig.add_trace(go.Scatter(x=[a['ratios'].index[-1]], y=[a['ratios'].iloc[-1]], mode='markers', marker=dict(color='white', size=10, line=dict(width=2, color=accent_color))))
                
                # Axis Labeling
                fig.update_layout(
                    height=180, margin=dict(l=10,r=10,t=10,b=10),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=False,
                    xaxis=dict(title="Year", title_font=dict(size=10, color="#8b949e"), showgrid=False, tickfont=dict(size=8, color="#8b949e")),
                    yaxis=dict(title="Ratio Value", title_font=dict(size=10, color="#8b949e"), showgrid=True, gridcolor="#30363d", tickfont=dict(size=8, color="#8b949e"))
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
