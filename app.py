import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Ratio Asset Allocator", layout="wide")
st.title("🚨 Dynamic Extreme Value Command Center")

@st.cache_data(ttl=3600)
def fetch_data(ticker):
    try:
        asset = yf.download(ticker, period="30y", interval="1mo", progress=False)['Close']
        gold = yf.download("GC=F", period="30y", interval="1mo", progress=False)['Close']
        combined = pd.concat([asset, gold], axis=1).dropna()
        combined.columns = ['Asset', 'Gold']
        
        if "SI=F" in ticker:
            return (combined['Gold'] / combined['Asset']).dropna()
        return (combined['Asset'] / combined['Gold']).dropna()
    except Exception:
        return pd.Series()

# Ticker and TradingView Mapping
tickers_map = {"Silver": "SI=F", "S&P 500": "ES=F", "Dow Jones": "YM=F", "Miners": "GDXJ", "Oil": "CL=F"}
tv_map = {"Silver": "OANDA:XAGUSD", "S&P 500": "CME_MINI:ES1!", "Dow Jones": "CBOT:YM1!", "Miners": "AMEX:GDXJ", "Oil": "NYMEX:CL1!"}

# 1. Process Data & Calculate Dynamic Thresholds
asset_list = []
for name, sym in tickers_map.items():
    ratios = fetch_data(sym)
    if not ratios.empty:
        curr = float(ratios.iloc[-1])
        hist_max = float(ratios.max())
        hist_min = float(ratios.min())
        range_span = hist_max - hist_min
        
        # Calculate Dynamic Thresholds based on 5% and 10% distance from extremes
        # For Assets (Lower is cheaper): Buy near Min. For Silver (Higher is cheaper): Buy near Max.
        if name == "Silver":
            ex_buy = hist_max * 0.95
            reg_buy = hist_max * 0.90
            ex_sell = hist_min * 1.05
            # Score for sorting: how close are we to the max?
            score = curr / hist_max
        else:
            ex_buy = hist_min * 1.05
            reg_buy = hist_min * 1.10
            ex_sell = hist_max * 0.95
            # Score for sorting: how close are we to the min?
            score = hist_min / curr
            
        asset_list.append({
            "name": name, "sym": sym, "ratios": ratios, "curr": curr, 
            "max": hist_max, "min": hist_min, "score": score,
            "thresholds": {"ex_buy": ex_buy, "buy": reg_buy, "ex_sell": ex_sell}
        })

# Sort: Best value (closest to buy extremes) on the left
sorted_assets = sorted(asset_list, key=lambda x: x['score'], reverse=True)

# 2. Display Grid
cols = st.columns(len(sorted_assets))

for i, asset in enumerate(sorted_assets):
    name, ratios, curr, t = asset['name'], asset['ratios'], asset['curr'], asset['thresholds']
    
    # Data Stabilization [2026-02-07 instruction]
    avg_12m = float(ratios.tail(12).mean())
    stability_status = "🟢 Stable" if (abs(curr - avg_12m) / avg_12m) < 0.05 else "🔴 Volatile"

    # Signal Color Logic (Dynamic)
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

    val_str = f"{curr:.2f}" if name in ["Silver", "S&P 500", "Dow Jones"] else f"{curr:.4f}"
    
    with cols[i]:
        st.markdown(f"""
        <div style="background-color:{bg}; padding:15px; border-radius:10px; border:1px solid #444; color:white; height:390px; display:flex; flex-direction:column; justify-content:space-between;">
            <div style="text-align:center;">
                <div style="font-size:0.9em; color:#bbb;">{name} Ratio</div>
                <div style="font-size:2.4em; font-weight:bold; color:#FFD700;">{val_str}</div>
            </div>
            <div style="background:rgba(0,0,0,0.3); padding:8px; border-radius:5px; font-size:0.75em;">
                <div style="display:flex; justify-content:space-between;"><span>Data:</span><b>{stability_status}</b></div>
                <div style="display:flex; justify-content:space-between;"><span>30Y High:</span><b>{asset['max']:.2f}</b></div>
                <div style="display:flex; justify-content:space-between;"><span>30Y Low:</span><b>{asset['min']:.2f}</b></div>
            </div>
            <div style="text-align:center; padding:10px; border:2px solid white; font-weight:bold; border-radius:5px; background:rgba(255,255,255,0.1);">
                {label}
            </div>
            <div style="text-align:center; margin-top:5px;">
                <a href="https://www.tradingview.com/chart/?symbol={tv_map[name]}" target="_blank" style="color:#3BB3E4; text-decoration:none; font-size:0.8em;">🔍 TradingView ↗️</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📈 Visual Range"):
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ratios.index, y=ratios.values, line=dict(color='#FFD700')))
            fig.add_hline(y=t['buy'], line_dash="dash", line_color="green", annotation_text="Buy Zone")
            fig.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

st.divider()
st.caption("Auto-Thresholds: 5% (Extreme) / 10% (Regular) from 30Y Records | Data Stabilization Included")
