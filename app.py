import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Ratio Asset Allocator", layout="wide")

# 1. Fetch & Prepare 30Y Data
@st.cache_data(ttl=3600)
def fetch_all_data():
    tickers = {"Silver": "SI=F", "S&P 500": "ES=F", "Dow Jones": "YM=F", "Miners": "GDXJ", "Oil": "CL=F", "Gold": "GC=F"}
    data_dict = {}
    for name, sym in tickers.items():
        try:
            # Fetching 30Y of monthly data
            df = yf.download(sym, period="30y", interval="1mo", progress=False)['Close']
            data_dict[name] = df
        except:
            continue
    return pd.DataFrame(data_dict).dropna()

full_history = fetch_all_data()

# 2. Simulation Slider in Sidebar
st.sidebar.header("🕹️ Simulation Suite")
sim_index = st.sidebar.slider(
    "Backtest Date (Last 30 Years)", 
    min_value=12, # Start at month 12 to allow for trend/stability calculations
    max_value=len(full_history)-1, 
    value=len(full_history)-1,
    help="Slide back in time to see how the dashboard would have looked during past market cycles."
)

# Filter history based on slider (this 'simulates' being at that point in time)
current_history = full_history.iloc[:sim_index + 1]
as_of_date = current_history.index[-1].strftime('%B %Y')
gold_price = float(current_history['Gold'].iloc[-1])

st.title("🚨 Dynamic Extreme Value Command Center")
st.subheader(f"Simulation Mode: {as_of_date} | Gold: ${gold_price:,.2f}")

# 3. Logic & Metric Calculation
tickers_map = {"Silver": "SI=F", "S&P 500": "ES=F", "Dow Jones": "YM=F", "Miners": "GDXJ", "Oil": "CL=F"}
tv_map = {"Silver": "OANDA:XAGUSD", "S&P 500": "CME_MINI:ES1!", "Dow Jones": "CBOT:YM1!", "Miners": "AMEX:GDXJ", "Oil": "NYMEX:CL1!"}

asset_list = []
for name in tickers_map.keys():
    # Calculate Ratio relative to Gold
    if name == "Silver":
        ratios = current_history['Gold'] / current_history['Silver']
    else:
        ratios = current_history[name] / current_history['Gold']
    
    ratios = ratios.dropna()
    curr = float(ratios.iloc[-1])
    hist_max, hist_min = float(ratios.max()), float(ratios.min())
    
    # Trend (Last month vs current)
    trend_arrow = "↑" if curr > float(ratios.iloc[-2]) else "↓"
    
    # Stabilization [2026-02-07 instruction]
    avg_12m = float(ratios.tail(12).mean())
    stability_status = "🟢 Stable" if (abs(curr - avg_12m) / avg_12m) < 0.05 else "🔴 Volatile"
    
    # Dynamic Thresholds (10% Extreme / 20% Buy)
    if name == "Silver":
        ex_buy, reg_buy, ex_sell = hist_max * 0.90, hist_max * 0.80, hist_min * 1.10
        score = curr / hist_max 
    else:
        ex_buy, reg_buy, ex_sell = hist_min * 1.10, hist_min * 1.20, hist_max * 0.90
        score = hist_min / curr
        
    asset_list.append({
        "name": name, "ratios": ratios, "curr": curr, "trend": trend_arrow,
        "max": hist_max, "min": hist_min, "score": score, "stability": stability_status,
        "thresholds": {"ex_buy": ex_buy, "buy": reg_buy, "ex_sell": ex_sell}
    })

# Sort: Best Value (highest score) on the left
sorted_assets = sorted(asset_list, key=lambda x: x['score'], reverse=True)

# 4. Display Grid
cols = st.columns(len(sorted_assets))

for i, asset in enumerate(sorted_assets):
    name, ratios, curr, t = asset['name'], asset['ratios'], asset['curr'], asset['thresholds']
    
    # Signal Logic
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
        <div style="background-color:{bg}; padding:15px; border-radius:10px; border:1px solid #444; color:white; height:430px; display:flex; flex-direction:column; justify-content:space-between;">
            <div style="text-align:center;">
                <div style="font-size:0.9em; color:#bbb;">{name} / Gold</div>
                <div style="font-size:2.4em; font-weight:bold; color:#FFD700;">{asset['trend']} {val_str}</div>
            </div>
            <div style="background:rgba(0,0,0,0.3); padding:8px; border-radius:5px; font-size:0.75em;">
                <div style="display:flex; justify-content:space-between;"><span>Stabilization:</span><b>{asset['stability']}</b></div>
                <div style="display:flex; justify-content:space-between;"><span>Historical Max:</span><b>{asset['max']:.2f}</b></div>
                <div style="display:flex; justify-content:space-between;"><span>Historical Min:</span><b>{asset['min']:.2f}</b></div>
            </div>
            <div style="text-align:center; padding:10px; border:2px solid white; font-weight:bold; border-radius:5px; background:rgba(255,255,255,0.1);">
                {label}
            </div>
            <div style="text-align:center; margin-top:5px;">
                <a href="https://www.tradingview.com/chart/?symbol={tv_map[name]}" target="_blank" style="color:#3BB3E4; text-decoration:none; font-size:0.8em; font-weight:bold;">🔍 View Index ↗️</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📈 Range Visual"):
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ratios.index, y=ratios.values, line=dict(color='#FFD700')))
            fig.add_hline(y=t['buy'], line_dash="dash", line_color="green")
            fig.add_hline(y=t['ex_buy'], line_dash="solid", line_color="lime")
            fig.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

st.divider()
st.caption("Instructions: Use the sidebar slider to travel back in time. The dashboard will recalculate historical extremes based only on data available up to that date.")
