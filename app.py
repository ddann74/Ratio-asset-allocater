import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. Configuration & Extreme Thresholds
# For Silver: Higher = Cheaper (Gold/Silver). For Others: Lower = Cheaper (Asset/Gold).
THRESHOLDS = {
    "Silver": {"extreme_buy": 95.0, "buy": 85.0, "extreme_sell": 40.0},
    "S&P 500": {"extreme_buy": 0.8, "buy": 1.2, "extreme_sell": 2.5},
    "Dow Jones": {"extreme_buy": 10.0, "buy": 15.0, "extreme_sell": 25.0},
    "Miners": {"extreme_buy": 0.015, "buy": 0.022, "extreme_sell": 0.05},
    "Oil": {"extreme_buy": 0.025, "buy": 0.04, "extreme_sell": 0.10}
}

st.set_page_config(page_title="Ratio Asset Allocator", layout="wide")
st.title("🚨 Extreme Value Command Center")

@st.cache_data(ttl=3600)
def fetch_data(ticker):
    try:
        # Fetching 30 years of monthly data for ratio analysis
        asset = yf.download(ticker, period="30y", interval="1mo", progress=False)['Close']
        gold = yf.download("GC=F", period="30y", interval="1mo", progress=False)['Close']
        combined = pd.concat([asset, gold], axis=1).dropna()
        combined.columns = ['Asset', 'Gold']
        
        if "SI=F" in ticker:
            # Silver is viewed as Gold/Silver ratio
            return (combined['Gold'] / combined['Asset']).dropna()
        # Others are viewed as Asset/Gold ratio
        return (combined['Asset'] / combined['Gold']).dropna()
    except Exception:
        return pd.Series()

# Ticker and TradingView Mapping
tickers_map = {
    "Silver": "SI=F", 
    "S&P 500": "ES=F", 
    "Dow Jones": "YM=F", 
    "Miners": "GDXJ", 
    "Oil": "CL=F"
}
tv_map = {
    "Silver": "OANDA:XAGUSD", 
    "S&P 500": "CME_MINI:ES1!", 
    "Dow Jones": "CBOT:YM1!", 
    "Miners": "AMEX:GDXJ", 
    "Oil": "NYMEX:CL1!"
}

# 2. Pre-process and Sort by Value Score
asset_list = []
for name, sym in tickers_map.items():
    ratios = fetch_data(sym)
    if not ratios.empty:
        curr = float(ratios.iloc[-1])
        t = THRESHOLDS[name]
        
        # Calculate Value Score: Higher = Better Value (Closest to Gen Buy)
        if name == "Silver":
            score = curr / t['extreme_buy']
        else:
            score = t['extreme_buy'] / curr
            
        asset_list.append({
            "name": name, 
            "sym": sym, 
            "ratios": ratios, 
            "curr": curr, 
            "score": score,
            "t": t
        })

# Sort assets: Highest value score (cheapest) on the left
sorted_assets = sorted(asset_list, key=lambda x: x['score'], reverse=True)

# 3. Display Grid
cols = st.columns(len(sorted_assets))

for i, asset in enumerate(sorted_assets):
    name = asset['name']
    ratios = asset['ratios']
    curr = asset['curr']
    t = asset['t']
    
    # Data Stabilization Calculation [2026-02-07 Instruction]
    avg_12m = float(ratios.tail(12).mean())
    stability_var = abs(curr - avg_12m) / avg_12m
    stability_status = "🟢 Stable" if stability_var < 0.05 else "🔴 Volatile"

    # Signal Color Logic
    if name == "Silver":
        if curr >= t['extreme_buy']: bg, label = "#004d00", "💎 GENERATIONAL BUY"
        elif curr >= t['buy']: bg, label = "#1e4620", "🔥 BUY SIGNAL"
        elif curr <= t['extreme_sell']: bg, label = "#900C3F", "⚠️ EXTREME SELL"
        else: bg, label = "#1E1E1E", "⏳ HOLD"
    else:
        if curr <= t['extreme_buy']: bg, label = "#004d00", "💎 GENERATIONAL BUY"
        elif curr <= t['buy']: bg, label = "#1e4620", "🔥 BUY SIGNAL"
        elif curr >= t['extreme_sell']: bg, label = "#900C3F", "⚠️ EXTREME SELL"
        else: bg, label = "#1E1E1E", "⏳ HOLD"

    # Fix: Format numbers before f-string to prevent ValueError 
    val_str = f"{curr:.2f}" if name in ["Silver", "S&P 500", "Dow Jones"] else f"{curr:.4f}"
    
    with cols[i]:
        st.markdown(f"""
        <div style="background-color:{bg}; padding:15px; border-radius:10px; border:1px solid #444; color:white; height:380px; display:flex; flex-direction:column; justify-content:space-between;">
            <div style="text-align:center;">
                <div style="font-size:0.9em; color:#bbb;">{name}</div>
                <div style="font-size:2.4em; font-weight:bold; color:#FFD700;">{val_str}</div>
            </div>
            <div style="background:rgba(0,0,0,0.3); padding:8px; border-radius:5px; font-size:0.75em;">
                <div style="display:flex; justify-content:space-between;"><span>Stabilization:</span><b>{stability_status}</b></div>
                <div style="display:flex; justify-content:space-between;"><span>30Y High:</span><b>{ratios.max():.2f}</b></div>
                <div style="display:flex; justify-content:space-between;"><span>30Y Low:</span><b>{ratios.min():.2f}</b></div>
            </div>
            <div style="text-align:center; padding:10px; border:2px solid white; font-weight:bold; border-radius:5px; background:rgba(255,255,255,0.1);">
                {label}
            </div>
            <div style="text-align:center; margin-top:5px;">
                <a href="https://www.tradingview.com/chart/?symbol={tv_map[name]}" target="_blank" style="color:#3BB3E4; text-decoration:none; font-size:0.8em;">🔍 TradingView ↗️</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📈 Ratio Trend"):
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ratios.index, y=ratios.values, line=dict(color='#FFD700')))
            fig.add_hline(y=t['buy'], line_dash="dash", line_color="green")
            fig.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

st.divider()
st.caption("Data Stabilization & Value Sorting Active | [2026-02-07 Update] | Fixed Syntax Errors")
