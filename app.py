import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Ratio Asset Allocator", layout="wide")

# 1. Gold Context Header (Checking the baseline)
@st.cache_data(ttl=3600)
def get_gold_context():
    gold = yf.download("GC=F", period="2y", interval="1d", progress=False)['Close']
    curr_gold = float(gold.iloc[-1])
    high_2y = float(gold.max())
    is_record = "🔥 Gold at/near Record Highs" if curr_gold >= (high_2y * 0.98) else "⚖️ Gold in Normal Range"
    return curr_gold, is_record

gold_price, gold_status = get_gold_context()

st.title("🚨 Dynamic Extreme Value Command Center")
st.subheader(f"Baseline: Gold ${gold_price:,.2f} | {gold_status}")

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

# 2. Process Data & Calculate Metrics
asset_list = []
for name, sym in tickers_map.items():
    ratios = fetch_data(sym)
    if not ratios.empty:
        curr = float(ratios.iloc[-1])
        hist_max, hist_min = float(ratios.max()), float(ratios.min())
        
        # Trend Momentum (Last 30 days vs current)
        prev_month = float(ratios.iloc[-2])
        trend_arrow = "↑" if curr > prev_month else "↓"
        
        # Dynamic Threshold Logic (10% Extreme / 20% Signal)
        if name == "Silver":
            ex_buy, reg_buy, ex_sell = hist_max * 0.90, hist_max * 0.80, hist_min * 1.10
            score = curr / hist_max 
        else:
            ex_buy, reg_buy, ex_sell = hist_min * 1.10, hist_min * 1.20, hist_max * 0.90
            score = hist_min / curr
            
        asset_list.append({
            "name": name, "sym": sym, "ratios": ratios, "curr": curr, "trend": trend_arrow,
            "max": hist_max, "min": hist_min, "score": score,
            "thresholds": {"ex_buy": ex_buy, "buy": reg_buy, "ex_sell": ex_sell}
        })

# Sort by Best Value (Score)
sorted_assets = sorted(asset_list, key=lambda x: x['score'], reverse=True)

# 3. Display Grid
cols = st.columns(len(sorted_assets))

for i, asset in enumerate(sorted_assets):
    name, ratios, curr, t = asset['name'], asset['ratios'], asset['curr'], asset['thresholds']
    
    # Data Stabilization Calculation
    avg_12m = float(ratios.tail(12).mean())
    stability_status = "🟢 Stable" if (abs(curr - avg_12m) / avg_12m) < 0.05 else "🔴 Volatile"

    # Signal Color Logic
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
                <div style="display:flex; justify-content:space-between;"><span>Stabilization:</span><b>{stability_status}</b></div>
                <div style="display:flex; justify-content:space-between;"><span>30Y High:</span><b>{asset['max']:.2f}</b></div>
                <div style="display:flex; justify-content:space-between;"><span>30Y Low:</span><b>{asset['min']:.2f}</b></div>
            </div>
            <div style="text-align:center; padding:10px; border:2px solid white; font-weight:bold; border-radius:5px; background:rgba(255,255,255,0.1);">
                {label}
            </div>
            <div style="text-align:center; margin-top:5px;">
                <a href="https://www.tradingview.com/chart/?symbol={tv_map[name]}" target="_blank" style="color:#3BB3E4; text-decoration:none; font-size:0.8em; font-weight:bold;">🔍 TradingView Chart ↗️</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📈 Range Visual"):
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ratios.index, y=ratios.values, line=dict(color='#FFD700')))
            fig.add_hline(y=t['buy'], line_dash="dash", line_color="green", annotation_text="20% Zone")
            fig.add_hline(y=t['ex_buy'], line_dash="solid", line_color="lime", annotation_text="10% Extreme")
            fig.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

st.divider()
st.caption("Value Strategy: 10%/20% Historical Range Thresholds | Trend & Stabilization Monitoring Enabled")
