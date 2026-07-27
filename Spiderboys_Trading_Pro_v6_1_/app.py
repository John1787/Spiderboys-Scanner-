from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from core.data import load_market, load_journal, load_news, load_indices, load_alerts
from core.engine import scan_setups, build_trade_plan, replay_grade, coach_trade, component_scores
from core.risk import calculate_position_size, risk_lock_status
from core.analytics import summarize_journal, grouped_stats
from core.alpaca import get_account, get_positions, get_latest_snapshot, get_bars, AlpacaError
from core.live_news import (
    MarketDataError, combine_news, finnhub_company_news, finnhub_market_news,
    finnhub_profile, finnhub_quote, fmp_profile, fmp_stock_news, catalyst_score
)

BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Spiderboys Trading Pro v6.1 Live Command Center",
    page_icon="🕷️",
    layout="wide"
)

st.markdown("""
<style>
:root {
    --sb-bg: #07111f;
    --sb-panel: #0d1b2d;
    --sb-panel-2: #12243a;
    --sb-blue: #2f80ed;
    --sb-cyan: #22d3ee;
    --sb-teal: #16c7a3;
    --sb-gold: #f6c85f;
    --sb-red: #ff5d73;
    --sb-text: #f4f8ff;
    --sb-muted: #9fb2ca;
    --sb-border: rgba(74, 144, 226, .25);
}

.stApp {
    background:
        radial-gradient(circle at 15% 5%, rgba(47,128,237,.18), transparent 28%),
        radial-gradient(circle at 92% 0%, rgba(34,211,238,.12), transparent 24%),
        linear-gradient(180deg, #07111f 0%, #091525 45%, #06101d 100%);
    color: var(--sb-text);
}

.block-container {
    max-width: 1550px;
    padding-top: 1.25rem;
    padding-bottom: 3rem;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #081523 0%, #0b1c2f 58%, #07111f 100%);
    border-right: 1px solid var(--sb-border);
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: .65rem;
}

h1, h2, h3 {
    letter-spacing: -.025em;
}
h1 {
    background: linear-gradient(90deg, #ffffff, #86c8ff 45%, #37e4cf);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 850 !important;
}
h2, h3 {
    color: #eaf4ff !important;
}

[data-testid="stMetric"] {
    background: linear-gradient(145deg, rgba(18,36,58,.96), rgba(9,25,42,.94));
    border: 1px solid var(--sb-border);
    border-radius: 16px;
    padding: 15px 16px 13px 16px;
    box-shadow: 0 12px 34px rgba(0,0,0,.18);
}
[data-testid="stMetricLabel"] {
    color: var(--sb-muted);
    font-weight: 700;
}
[data-testid="stMetricValue"] {
    color: #ffffff;
    font-size: 1.55rem;
    font-weight: 800;
}
[data-testid="stMetricDelta"] {
    font-weight: 700;
}

div[data-testid="stDataFrame"] {
    border: 1px solid var(--sb-border);
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 10px 28px rgba(0,0,0,.16);
}

.stButton > button,
.stDownloadButton > button {
    border: 1px solid rgba(65,170,255,.5);
    border-radius: 11px;
    font-weight: 800;
    background: linear-gradient(135deg, #1b69d2, #178fb4);
    color: white;
    min-height: 2.6rem;
    box-shadow: 0 8px 22px rgba(22,113,210,.22);
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    border-color: #70e6ff;
    transform: translateY(-1px);
    box-shadow: 0 12px 28px rgba(34,211,238,.24);
}

div[data-baseweb="select"] > div,
.stTextInput input,
.stNumberInput input,
.stTextArea textarea {
    background: rgba(13,27,45,.92) !important;
    border-color: rgba(74,144,226,.34) !important;
    color: white !important;
}

[data-testid="stAlert"] {
    border-radius: 13px;
    border: 1px solid rgba(74,144,226,.3);
}

.sb-hero {
    background:
        linear-gradient(120deg, rgba(23,67,119,.96), rgba(12,39,69,.96) 52%, rgba(13,78,82,.92));
    border: 1px solid rgba(79,174,255,.42);
    border-radius: 20px;
    padding: 1.25rem 1.4rem;
    margin: .2rem 0 1.15rem 0;
    box-shadow: 0 16px 42px rgba(0,0,0,.24);
}
.sb-hero-title {
    font-size: 1.28rem;
    font-weight: 900;
    color: white;
    margin-bottom: .28rem;
}
.sb-hero-sub {
    color: #c7ddf5;
    font-size: .95rem;
}
.sb-status-row {
    display: flex;
    gap: .5rem;
    flex-wrap: wrap;
    margin-top: .72rem;
}
.sb-chip {
    display: inline-block;
    padding: .28rem .62rem;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,.18);
    background: rgba(4,16,28,.35);
    color: #dcecff;
    font-size: .78rem;
    font-weight: 800;
}
.sb-chip-live {
    color: #8fffe2;
    border-color: rgba(22,199,163,.55);
}
.sb-chip-safe {
    color: #ffe6a0;
    border-color: rgba(246,200,95,.5);
}

.sb-card {
    background: linear-gradient(145deg, rgba(18,36,58,.98), rgba(10,25,42,.96));
    border: 1px solid var(--sb-border);
    border-radius: 16px;
    padding: 1rem 1.05rem;
    box-shadow: 0 12px 30px rgba(0,0,0,.17);
}
.sb-card-title {
    font-weight: 850;
    color: #f5f9ff;
    margin-bottom: .35rem;
}
.sb-muted {
    color: var(--sb-muted);
    font-size: .88rem;
}
.score-pill {
    border-radius: 999px;
    padding: .25rem .65rem;
    display: inline-block;
    font-weight: 700;
}
.small-note {
    font-size: .88rem;
    color: var(--sb-muted);
}
hr {
    border-color: rgba(74,144,226,.18);
}

/* High-contrast text */
:root {
    --sb-muted: #ffffff;
}
p, span, label, .stCaption, [data-testid="stCaptionContainer"],
[data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"] {
    color: #ffffff !important;
}
.sb-muted, .small-note, .sb-hero-sub {
    color: #ffffff !important;
    opacity: .94;
}
[data-testid="stMetricLabel"] {
    color: #ffffff !important;
    opacity: .92;
}

/* App-style sidebar navigation */
[data-testid="stSidebar"] [role="radiogroup"] {
    gap: .42rem;
}
[data-testid="stSidebar"] [role="radiogroup"] > label {
    background: linear-gradient(145deg, rgba(17,39,65,.98), rgba(10,27,47,.98));
    border: 1px solid rgba(77,151,230,.28);
    border-radius: 13px;
    padding: .72rem .78rem;
    margin: 0;
    min-height: 48px;
    box-shadow: 0 7px 18px rgba(0,0,0,.16);
    transition: all .18s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] > label:hover {
    border-color: rgba(68,217,255,.75);
    background: linear-gradient(145deg, rgba(27,76,126,.98), rgba(12,50,75,.98));
    transform: translateX(3px);
}
[data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) {
    background: linear-gradient(135deg, #235fbe, #128ea3);
    border-color: #73e4ff;
    box-shadow: 0 10px 24px rgba(29,130,210,.30);
}
[data-testid="stSidebar"] [role="radiogroup"] > label p {
    font-weight: 800 !important;
    color: #ffffff !important;
    font-size: .93rem !important;
}
[data-testid="stSidebar"] [role="radiogroup"] > label > div:first-child {
    display: none;
}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    text-transform: uppercase;
    letter-spacing: .09em;
    font-size: .72rem !important;
    font-weight: 900 !important;
    color: #86dfff !important;
}

</style>
""", unsafe_allow_html=True)

market = load_market(BASE_DIR)
journal = load_journal(BASE_DIR)
news = load_news(BASE_DIR)
indices = load_indices(BASE_DIR)
alerts = load_alerts(BASE_DIR)

st.sidebar.markdown("""
<div style="padding:.65rem .25rem .9rem .25rem;">
  <div style="font-size:1.48rem;font-weight:900;color:#ffffff;">🕷️ Spiderboys</div>
  <div style="font-size:1.05rem;font-weight:800;color:#65d9ff;">Trading Pro</div>
  <div style="font-size:.78rem;color:#91a9c2;margin-top:.2rem;">Live Command Center v6.1</div>
</div>
""", unsafe_allow_html=True)
page = st.sidebar.radio(
    "Workspace",
    [
        "Morning Command Center",
        "Market Intelligence",
        "Live-Style Scanner",
        "Professional Charts",
        "Trade Planner",
        "AI Trade Coach",
        "Replay Academy",
        "Risk Command Center",
        "Trading Journal",
        "Performance Analytics",
        "Alert Center",
        "Daily Process",
        "Live Scanner",
        "Live News Center",
        "Live Data Diagnostics",
        "Live Data Hub",
        "Integrations",
    ]
)

st.sidebar.markdown("---")
st.sidebar.success("HYBRID LIVE MODE")
try:
    _fmp_ok = bool(st.secrets.get("fmp", {}).get("api_key", ""))
    _fh_ok = bool(st.secrets.get("finnhub", {}).get("api_key", ""))
except Exception:
    _fmp_ok = _fh_ok = False

st.sidebar.markdown(
    f"""
    <div class="sb-card" style="padding:.75rem .8rem;margin-top:.55rem;">
      <div class="sb-card-title" style="font-size:.86rem;">DATA CONNECTIONS</div>
      <div class="sb-muted">{"🟢" if _fmp_ok else "🔴"} FMP</div>
      <div class="sb-muted">{"🟢" if _fh_ok else "🔴"} Finnhub</div>
    </div>
    """,
    unsafe_allow_html=True
)
st.sidebar.caption("Open Live Data Diagnostics to verify real API responses.")

st.markdown("""
<div class="sb-hero">
  <div class="sb-hero-title">Spiderboys Live Trading Command Center</div>
  <div class="sb-hero-sub">Live market intelligence, catalyst tracking, setup ranking, risk controls, and training tools in one workstation.</div>
  <div class="sb-status-row">
    <span class="sb-chip sb-chip-live">● FMP + Finnhub Ready</span>
    <span class="sb-chip">Hybrid Live Data</span>
    <span class="sb-chip">First Pullback Engine</span>
    <span class="sb-chip sb-chip-safe">Paper / Analysis Mode</span>
  </div>
</div>
""", unsafe_allow_html=True)

def candlestick_chart(ticker, height=520, show_levels=True):
    g = market[market["ticker"] == ticker].sort_values("datetime").copy()
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=g["datetime"], open=g["open"], high=g["high"], low=g["low"], close=g["close"],
        name=ticker
    ))
    fig.add_trace(go.Scatter(x=g["datetime"], y=g["vwap"], mode="lines", name="VWAP"))
    fig.add_trace(go.Scatter(x=g["datetime"], y=g["ema9"], mode="lines", name="EMA 9"))
    fig.add_trace(go.Scatter(x=g["datetime"], y=g["ema20"], mode="lines", name="EMA 20"))
    if show_levels:
        last = g.iloc[-1]
        fig.add_hline(y=last["premarket_high"], line_dash="dash", annotation_text="PM High")
        fig.add_hline(y=last["previous_day_high"], line_dash="dot", annotation_text="PD High")
        fig.add_hline(y=last["entry"], line_dash="dash", annotation_text="Entry")
        fig.add_hline(y=last["stop"], line_dash="dot", annotation_text="Stop")
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_rangeslider_visible=False,
        legend_orientation="h",
    )
    st.plotly_chart(fig, use_container_width=True)

def watchlist_table(scan):
    cols = [
        "ticker","price","gap_pct","float_m","premarket_volume","relative_volume",
        "spider_score","quality","setup_status","entry","stop","target_2r"
    ]
    st.dataframe(scan[cols], use_container_width=True, hide_index=True)

if page == "Morning Command Center":
    st.title("Morning Command Center")
    scan = scan_setups(market)
    stats = summarize_journal(journal)

    a,b,c,d,e = st.columns(5)
    a.metric("Qualified Setups", len(scan))
    b.metric("A+ Candidates", int((scan["quality"]=="A+").sum()))
    c.metric("Market Bias", indices.iloc[-1]["market_bias"])
    d.metric("Demo Win Rate", f'{stats["win_rate"]:.1f}%')
    e.metric("Expectancy", f'{stats["expectancy_r"]:.2f}R')

    st.subheader("Top Watchlist")
    watchlist_table(scan.head(8))

    left, right = st.columns([1.75,1])
    with left:
        top = scan.iloc[0]
        st.subheader(f'Featured Setup — {top["ticker"]}')
        candlestick_chart(top["ticker"], 470)
    with right:
        st.subheader("Trade Plan")
        st.write(f'**Catalyst:** {top["catalyst"]}')
        st.write(f'**Entry:** ${top["entry"]:.2f}')
        st.write(f'**Stop:** ${top["stop"]:.2f}')
        st.write(f'**1R:** ${top["target_1r"]:.2f}')
        st.write(f'**2R:** ${top["target_2r"]:.2f}')
        st.write(f'**Room to resistance:** {top["room_to_resistance_r"]:.1f}R')
        st.info(top["coach_note"])

    st.subheader("Breaking Training News")
    st.dataframe(news.head(5), use_container_width=True, hide_index=True)

    st.subheader("Today’s Mission")
    st.markdown("""
    1. Rank the top three scanner candidates.
    2. Select one A-quality setup.
    3. Write entry, stop, and targets before the trigger.
    4. Complete one replay exercise.
    5. Journal the decision, not just the result.
    """)

elif page == "Market Intelligence":
    st.title("Market Intelligence")

    latest = indices.sort_values("datetime").groupby("symbol").tail(1)
    cols = st.columns(len(latest))
    for col, (_, row) in zip(cols, latest.iterrows()):
        col.metric(row["symbol"], f'{row["price"]:.2f}', f'{row["change_pct"]:.2f}%')

    st.subheader("Market Regime")
    regime = indices.iloc[-1]
    a,b,c,d = st.columns(4)
    a.metric("Bias", regime["market_bias"])
    b.metric("Volatility", regime["volatility_regime"])
    c.metric("Breadth", regime["market_breadth"])
    d.metric("Risk Mode", regime["risk_mode"])

    st.subheader("Index Trend")
    pivot = indices.pivot(index="datetime", columns="symbol", values="price")
    st.line_chart(pivot, use_container_width=True)

    st.subheader("Sector Strength")
    sector = pd.DataFrame({
        "Sector":["Technology","Semiconductors","Energy","Healthcare","Financials","Consumer"],
        "Relative Strength":[1.8,2.4,-0.6,0.9,0.3,-0.2]
    }).set_index("Sector")
    st.bar_chart(sector)

    st.subheader("Economic Calendar — Demo")
    calendar = pd.DataFrame([
        {"Time":"8:30 AM","Event":"Retail Sales","Impact":"High","Training Note":"Expect volatility at the open"},
        {"Time":"10:00 AM","Event":"Business Inventories","Impact":"Medium","Training Note":"Watch market reaction"},
        {"Time":"2:00 PM","Event":"Fed Speaker","Impact":"High","Training Note":"Avoid oversized afternoon exposure"},
    ])
    st.dataframe(calendar, use_container_width=True, hide_index=True)

elif page == "Live-Style Scanner":
    st.title("Live-Style Momentum Scanner")
    st.caption("Simulates a professional premarket scanner with ranking and filtering.")

    with st.expander("Scanner Filters", expanded=True):
        c1,c2,c3,c4,c5 = st.columns(5)
        min_gap = c1.slider("Min Gap %", 0, 100, 20)
        max_float = c2.slider("Max Float M", 5, 200, 50)
        min_pm = c3.number_input("Min PM Volume", value=500000, step=100000)
        min_rvol = c4.slider("Min RVOL", 0.0, 15.0, 2.0, 0.5)
        min_score = c5.slider("Min Spider Score", 0, 100, 65)
        require_catalyst = st.checkbox("Require catalyst", True)
        require_vwap = st.checkbox("Require above VWAP", True)

    scan = scan_setups(
        market,
        min_gap=min_gap,
        max_float=max_float,
        min_pm=min_pm,
        min_rvol=min_rvol,
        min_score=min_score,
        require_catalyst=require_catalyst,
        require_vwap=require_vwap,
    )

    if scan.empty:
        st.warning("No demo stocks match those filters.")
    else:
        watchlist_table(scan)
        st.download_button("Download Scanner Results", scan.to_csv(index=False), "spiderboys_v3_scan.csv")

        ticker = st.selectbox("Inspect candidate", scan["ticker"].tolist())
        row = scan[scan["ticker"] == ticker].iloc[0]

        a,b,c,d = st.columns(4)
        a.metric("Spider Score", int(row["spider_score"]))
        b.metric("Grade", row["quality"])
        c.metric("RVOL", f'{row["relative_volume"]:.1f}x')
        d.metric("Spread", f'{row["spread_pct"]:.2f}%')

        candlestick_chart(ticker, 500)

        scores = component_scores(row)
        st.subheader("Spider Score Components")
        st.dataframe(pd.DataFrame([scores]), use_container_width=True, hide_index=True)
        st.info(row["coach_note"])

elif page == "Professional Charts":
    st.title("Professional Charts")
    ticker = st.selectbox("Ticker", sorted(market["ticker"].unique()))
    candlestick_chart(ticker, 620)

    row = market[market["ticker"]==ticker].sort_values("datetime").iloc[-1]
    a,b,c,d,e = st.columns(5)
    a.metric("Last", f'${row["close"]:.2f}')
    b.metric("VWAP", f'${row["vwap"]:.2f}')
    c.metric("PM High", f'${row["premarket_high"]:.2f}')
    d.metric("PD High", f'${row["previous_day_high"]:.2f}')
    e.metric("Day Change", f'{row["day_change_pct"]:.1f}%')

    st.subheader("Automatic Levels")
    levels = pd.DataFrame([
        {"Level":"Premarket High","Price":row["premarket_high"],"Meaning":"Primary breakout level"},
        {"Level":"VWAP","Price":row["vwap"],"Meaning":"Intraday fair-value reference"},
        {"Level":"EMA 9","Price":row["ema9"],"Meaning":"Short-term momentum support"},
        {"Level":"Previous Day High","Price":row["previous_day_high"],"Meaning":"Major resistance reference"},
        {"Level":"Planned Stop","Price":row["stop"],"Meaning":"Setup invalidation"},
    ])
    st.dataframe(levels, use_container_width=True, hide_index=True)

elif page == "Trade Planner":
    st.title("Trade Planner")
    scan = scan_setups(market)
    ticker = st.selectbox("Candidate", scan["ticker"].tolist())
    row = scan[scan["ticker"]==ticker].iloc[0]

    left, right = st.columns([1.6,1])
    with left:
        candlestick_chart(ticker, 520)
    with right:
        account = st.number_input("Account Size", value=10000.0, step=500.0)
        risk_pct = st.number_input("Risk Per Trade %", value=0.5, step=0.1)
        plan = build_trade_plan(row, account, risk_pct)
        st.metric("Recommended Shares", f'{plan["shares"]:,}')
        st.write(f'Entry: **${plan["entry"]:.2f}**')
        st.write(f'Stop: **${plan["stop"]:.2f}**')
        st.write(f'Risk/share: **${plan["risk_per_share"]:.2f}**')
        st.write(f'Dollar risk: **${plan["dollar_risk"]:.2f}**')
        st.write(f'1R target: **${plan["target_1r"]:.2f}**')
        st.write(f'2R target: **${plan["target_2r"]:.2f}**')
        st.write(f'Buying power: **${plan["buying_power"]:.2f}**')

    checklist = {
        "Gap ≥ 20%": row["gap_pct"] >= 20,
        "Float ≤ 50M": row["float_m"] <= 50,
        "Premarket volume ≥ 500K": row["premarket_volume"] >= 500000,
        "RVOL ≥ 2": row["relative_volume"] >= 2,
        "Above VWAP": row["above_vwap"],
        "Catalyst present": bool(row["catalyst"]),
        "At least 2R room": row["room_to_resistance_r"] >= 2,
        "Controlled pullback": row["pullback_quality"] in ["Excellent","Good"],
    }
    st.subheader("Pre-Trade Checklist")
    for item, ok in checklist.items():
        st.write(("✅ " if ok else "❌ ") + item)

    if all(checklist.values()):
        st.success("A-quality plan. Wait for confirmation; do not anticipate.")
    else:
        st.warning("Professional decision may be no trade.")

elif page == "AI Trade Coach":
    st.title("AI Trade Coach")
    st.caption("Rule-based coaching in this version; no external AI API is required.")

    c1,c2,c3 = st.columns(3)
    ticker = c1.selectbox("Ticker", sorted(market["ticker"].unique()))
    setup = c2.selectbox("Setup", ["First Pullback","VWAP Reclaim","Premarket High Break"])
    emotion = c3.selectbox("Emotion", ["Calm","Confident","Hesitant","FOMO","Revenge","Tired"])

    c4,c5,c6,c7 = st.columns(4)
    entry = c4.number_input("Entry", value=8.70, step=0.01)
    stop = c5.number_input("Stop", value=8.55, step=0.01)
    exit_price = c6.number_input("Exit", value=9.00, step=0.01)
    shares = c7.number_input("Shares", value=250, step=10)

    followed_plan = st.checkbox("Followed written entry and stop", True)
    chased = st.checkbox("Entered extended/chased", False)
    averaged_down = st.checkbox("Averaged down", False)
    moved_stop = st.checkbox("Moved stop farther away", False)

    if st.button("Review Trade"):
        review = coach_trade(
            ticker=ticker, setup=setup, emotion=emotion, entry=entry, stop=stop,
            exit_price=exit_price, shares=shares, followed_plan=followed_plan,
            chased=chased, averaged_down=averaged_down, moved_stop=moved_stop
        )
        a,b,c = st.columns(3)
        a.metric("Execution Grade", review["grade"])
        b.metric("Result", f'{review["r_multiple"]:.2f}R')
        c.metric("Rule Score", f'{review["rule_score"]}/100')
        st.subheader("Coach Feedback")
        for note in review["feedback"]:
            st.write("• " + note)
        st.info(review["next_action"])

elif page == "Replay Academy":
    st.title("Replay Academy")

    ticker = st.selectbox("Replay Ticker", sorted(market["ticker"].unique()))
    g = market[market["ticker"]==ticker].sort_values("datetime").reset_index(drop=True)
    reveal = st.slider("Candles Revealed", 5, len(g)-2, min(10,len(g)-2))
    visible = g.iloc[:reveal]

    fig = go.Figure(go.Candlestick(
        x=visible["datetime"], open=visible["open"], high=visible["high"],
        low=visible["low"], close=visible["close"], name=ticker
    ))
    fig.add_trace(go.Scatter(x=visible["datetime"], y=visible["vwap"], mode="lines", name="VWAP"))
    fig.update_layout(height=500, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    c1,c2,c3 = st.columns(3)
    decision = c1.selectbox("Decision", ["Take Trade","No Trade"])
    entry = c2.number_input("Planned Entry", value=float(visible.iloc[-1]["high"]), step=0.01)
    stop = c3.number_input("Planned Stop", value=float(visible["low"].tail(4).min()), step=0.01)
    reason = st.text_area("Reasoning")

    if st.button("Reveal Outcome"):
        result = replay_grade(g, reveal, decision, entry, stop)
        a,b,c = st.columns(3)
        a.metric("Outcome", result["result"])
        b.metric("MFE", f'{result["mfe_r"]:.2f}R')
        c.metric("MAE", f'{result["mae_r"]:.2f}R')
        if result["result"] == "Win":
            st.success(result["message"])
        elif result["result"] == "Loss":
            st.error(result["message"])
        else:
            st.info(result["message"])
        st.write(result["coach_review"])

elif page == "Risk Command Center":
    st.title("Risk Command Center")

    c1,c2,c3,c4 = st.columns(4)
    account = c1.number_input("Account Size", value=10000.0)
    risk_pct = c2.number_input("Risk Per Trade %", value=0.5, step=0.1)
    entry = c3.number_input("Entry", value=8.70, step=0.01)
    stop = c4.number_input("Stop", value=8.55, step=0.01)

    size = calculate_position_size(account, risk_pct, entry, stop)
    a,b,c,d = st.columns(4)
    a.metric("Shares", f'{size["shares"]:,}')
    b.metric("Dollar Risk", f'${size["dollar_risk"]:.2f}')
    c.metric("Risk/Share", f'${size["risk_per_share"]:.2f}')
    d.metric("Buying Power", f'${size["buying_power"]:.2f}')

    st.subheader("Daily Risk Lock")
    x,y,z,w = st.columns(4)
    max_loss = x.number_input("Daily Loss Limit", value=150.0)
    realized = y.number_input("Realized P/L", value=-40.0)
    losses = z.number_input("Consecutive Losses", value=1, step=1)
    open_risk = w.number_input("Open Risk", value=50.0)

    status = risk_lock_status(max_loss, realized, int(losses), open_risk)
    if status["locked"]:
        st.error(status["message"])
    elif status["warning"]:
        st.warning(status["message"])
    else:
        st.success(status["message"])

    st.subheader("Risk Heat")
    heat = pd.DataFrame([
        {"Risk Area":"Realized Loss","Used %":min(100,abs(min(realized,0))/max_loss*100)},
        {"Risk Area":"Open Risk","Used %":min(100,open_risk/max_loss*100)},
        {"Risk Area":"Combined Risk","Used %":min(100,(abs(min(realized,0))+open_risk)/max_loss*100)},
    ]).set_index("Risk Area")
    st.bar_chart(heat)

elif page == "Trading Journal":
    st.title("Trading Journal")
    stats = summarize_journal(journal)

    a,b,c,d = st.columns(4)
    a.metric("Trades", stats["trades"])
    b.metric("Win Rate", f'{stats["win_rate"]:.1f}%')
    c.metric("Average R", f'{stats["avg_r"]:.2f}')
    d.metric("Net P/L", f'${stats["net_pnl"]:.2f}')

    st.dataframe(journal, use_container_width=True, hide_index=True)
    st.download_button("Download Demo Journal", journal.to_csv(index=False), "spiderboys_demo_journal.csv")

    ticker = st.selectbox("Review Trade", journal["ticker"].tolist())
    trade = journal[journal["ticker"]==ticker].iloc[0]
    st.markdown(f"""
    **Setup:** {trade["setup"]}  
    **Result:** {trade["r_multiple"]:.2f}R  
    **Execution Grade:** {trade["execution_grade"]}  
    **Emotion:** {trade["emotion"]}  
    **Mistake:** {trade["mistake"]}  
    **Lesson:** {trade["lesson"]}
    """)

elif page == "Performance Analytics":
    st.title("Performance Analytics")
    stats = summarize_journal(journal)

    a,b,c,d,e = st.columns(5)
    a.metric("Expectancy", f'{stats["expectancy_r"]:.2f}R')
    b.metric("Profit Factor", f'{stats["profit_factor"]:.2f}')
    c.metric("Best Setup", stats["best_setup"])
    d.metric("Max Drawdown", f'{stats["max_drawdown_r"]:.2f}R')
    e.metric("Rule Compliance", f'{stats["rule_compliance"]:.1f}%')

    st.subheader("By Setup")
    st.dataframe(grouped_stats(journal, "setup"), use_container_width=True, hide_index=True)

    st.subheader("By Time of Day")
    st.dataframe(grouped_stats(journal, "time_bucket"), use_container_width=True, hide_index=True)

    st.subheader("By Weekday")
    st.dataframe(grouped_stats(journal, "weekday"), use_container_width=True, hide_index=True)

    st.subheader("Equity Curve")
    equity = journal.copy()
    equity["equity_r"] = equity["r_multiple"].cumsum()
    st.line_chart(equity.set_index("date")["equity_r"])

    st.subheader("Mistake Frequency")
    mistakes = journal["mistake"].value_counts().rename_axis("mistake").reset_index(name="count")
    st.bar_chart(mistakes.set_index("mistake"))

    st.info(stats["coach_summary"])

elif page == "Alert Center":
    st.title("Alert Center")
    st.caption("Simulated alerts demonstrate how a future live alert system will behave.")

    st.dataframe(alerts, use_container_width=True, hide_index=True)

    st.subheader("Create Demo Alert")
    c1,c2,c3 = st.columns(3)
    ticker = c1.selectbox("Ticker", sorted(market["ticker"].unique()))
    alert_type = c2.selectbox("Alert Type", ["First Pullback","VWAP Reclaim","Premarket High Break","Volume Spike"])
    threshold = c3.number_input("Minimum Spider Score", value=80)

    if st.button("Test Alert"):
        row = scan_setups(market, min_score=0)
        match = row[row["ticker"]==ticker]
        if match.empty:
            st.warning("Ticker did not qualify.")
        else:
            score = float(match.iloc[0]["spider_score"])
            if score >= threshold:
                st.success(f"{ticker} triggered the {alert_type} demo alert with a Spider Score of {score:.0f}.")
            else:
                st.info(f"{ticker} has not reached the required score.")

elif page == "Daily Process":
    st.title("Daily Process")

    tabs = st.tabs(["Before Open","During Session","After Close"])
    with tabs[0]:
        for label in [
            "Check market bias and volatility",
            "Review economic calendar",
            "Build top-five watchlist",
            "Mark premarket and previous-day levels",
            "Write entry, stop, and targets",
            "Set daily loss limit",
        ]:
            st.checkbox(label, key="pre_"+label)
    with tabs[1]:
        for label in [
            "Trade only qualified setups",
            "Use predefined position size",
            "Do not average down",
            "Do not move stop farther away",
            "Capture screenshots",
            "Stop after daily loss limit",
        ]:
            st.checkbox(label, key="during_"+label)
    with tabs[2]:
        for label in [
            "Journal every trade",
            "Grade execution separately from P/L",
            "Review best trade",
            "Review worst mistake",
            "Record one lesson",
            "Prepare tomorrow’s improvement focus",
        ]:
            st.checkbox(label, key="after_"+label)

    st.success("Professional trading is a process business. Repeat the routine.")

elif page == "Live Scanner":
    st.title("Live Watchlist Scanner")
    st.caption("This page pulls live Finnhub quotes and headlines directly inside the app. Click Refresh Live Scanner to retrieve the newest available data.")

    try:
        fmp_key = str(st.secrets.get("fmp", {}).get("api_key", "")).strip()
        finnhub_key = str(st.secrets.get("finnhub", {}).get("api_key", "")).strip()
    except Exception:
        fmp_key = finnhub_key = ""

    if not finnhub_key:
        st.error("Finnhub key not detected. Add [finnhub] api_key in Streamlit Secrets.")
    else:
        default_symbols = "SOUN,RGTI,PLTR,AMD,NVDA,TSLA,SPY,QQQ"
        symbols_text = st.text_input("Watchlist symbols", value=default_symbols, help="Comma-separated tickers. Start with 5–15 symbols to stay within free API limits.")
        symbols = list(dict.fromkeys([x.strip().upper() for x in symbols_text.split(",") if x.strip()]))[:20]
        refresh = st.button("Refresh Live Scanner", type="primary")

        if refresh:
            rows = []
            progress = st.progress(0)
            for i, symbol in enumerate(symbols):
                try:
                    quote = finnhub_quote(symbol, finnhub_key)
                    profile = finnhub_profile(symbol, finnhub_key)
                    ticker_news = finnhub_company_news(symbol, finnhub_key, lookback_days=3)
                    top_news = ticker_news.iloc[0] if not ticker_news.empty else None
                    catalyst = int(top_news["catalyst_score"]) if top_news is not None else 0
                    headline = str(top_news["headline"]) if top_news is not None else "No recent headline returned"
                    sentiment = str(top_news["sentiment"]) if top_news is not None else "Neutral"
                    price_strength = max(-20, min(20, quote["change_pct"] * 1.5))
                    spider_score = int(max(0, min(100, 50 + price_strength + catalyst)))
                    rows.append({
                        "symbol": symbol,
                        "price": quote["price"],
                        "change_pct": quote["change_pct"],
                        "day_high": quote["high"],
                        "day_low": quote["low"],
                        "market_cap_m": profile["market_cap_m"],
                        "industry": profile["industry"],
                        "sentiment": sentiment,
                        "catalyst_score": catalyst,
                        "spider_score": spider_score,
                        "latest_headline": headline,
                    })
                except MarketDataError as exc:
                    rows.append({"symbol": symbol, "error": str(exc)})
                progress.progress((i + 1) / max(1, len(symbols)))
            st.session_state["live_scanner_rows"] = pd.DataFrame(rows)
            progress.empty()

        live_scan = st.session_state.get("live_scanner_rows")
        if live_scan is not None and not live_scan.empty:
            good = live_scan[live_scan.get("error", pd.Series(index=live_scan.index, dtype=object)).isna()] if "error" in live_scan.columns else live_scan
            if not good.empty:
                good = good.sort_values("spider_score", ascending=False)
                st.dataframe(good, use_container_width=True, hide_index=True)
                st.download_button("Download live watchlist", good.to_csv(index=False), "spiderboys_live_watchlist.csv")
            if "error" in live_scan.columns and live_scan["error"].notna().any():
                with st.expander("API errors"):
                    st.dataframe(live_scan[live_scan["error"].notna()][["symbol", "error"]], hide_index=True)

elif page == "Live News Center":
    st.title("Live News Center")
    st.caption("This page retrieves FMP and Finnhub headlines inside the app, removes duplicates, and assigns a transparent catalyst score.")

    try:
        fmp_key = str(st.secrets.get("fmp", {}).get("api_key", "")).strip()
        finnhub_key = str(st.secrets.get("finnhub", {}).get("api_key", "")).strip()
    except Exception:
        fmp_key = finnhub_key = ""

    a, b = st.columns(2)
    a.success("FMP key detected") if fmp_key else a.error("FMP key missing")
    b.success("Finnhub key detected") if finnhub_key else b.error("Finnhub key missing")

    tab1, tab2, tab3 = st.tabs(["Market Headlines", "Ticker Research", "Catalyst Tester"])
    with tab1:
        category = st.selectbox("Finnhub category", ["general", "forex", "crypto", "merger"])
        if st.button("Refresh Market Headlines", type="primary"):
            frames = []
            errors = []
            if finnhub_key:
                try:
                    frames.append(finnhub_market_news(finnhub_key, category))
                except MarketDataError as exc:
                    errors.append(f"Finnhub: {exc}")
            if fmp_key:
                try:
                    frames.append(fmp_stock_news(fmp_key, limit=50))
                except MarketDataError as exc:
                    errors.append(f"FMP: {exc}")
            st.session_state["combined_live_news"] = combine_news(*frames)
            st.session_state["live_news_errors"] = errors

        combined = st.session_state.get("combined_live_news")
        if combined is not None:
            for error in st.session_state.get("live_news_errors", []):
                st.warning(error)
            if combined.empty:
                st.info("No headlines were returned by the available free-plan endpoints.")
            else:
                sentiment_filter = st.multiselect("Sentiment", ["Bullish", "Neutral", "Bearish"], default=["Bullish", "Neutral", "Bearish"])
                view = combined[combined["sentiment"].isin(sentiment_filter)].head(100)
                st.dataframe(view[["published", "symbol", "headline", "source", "provider", "sentiment", "catalyst_score", "catalyst_reason", "url"]], use_container_width=True, hide_index=True)

    with tab2:
        symbol = st.text_input("Research ticker", value="AAPL", key="news_symbol").upper().strip()
        if st.button("Load Ticker Research"):
            result = {"symbol": symbol, "errors": []}
            if finnhub_key:
                try:
                    result["quote"] = finnhub_quote(symbol, finnhub_key)
                    result["fh_profile"] = finnhub_profile(symbol, finnhub_key)
                    result["fh_news"] = finnhub_company_news(symbol, finnhub_key, 7)
                except MarketDataError as exc:
                    result["errors"].append(f"Finnhub: {exc}")
            if fmp_key:
                try:
                    result["fmp_profile"] = fmp_profile(symbol, fmp_key)
                    result["fmp_news"] = fmp_stock_news(fmp_key, symbol=symbol, limit=30)
                except MarketDataError as exc:
                    result["errors"].append(f"FMP: {exc}")
            st.session_state["ticker_research"] = result

        result = st.session_state.get("ticker_research")
        if result and result.get("symbol") == symbol:
            for error in result.get("errors", []):
                st.warning(error)
            quote = result.get("quote")
            if quote:
                c1,c2,c3,c4 = st.columns(4)
                c1.metric(symbol, f'${quote["price"]:.2f}', f'{quote["change_pct"]:.2f}%')
                c2.metric("Open", f'${quote["open"]:.2f}')
                c3.metric("High", f'${quote["high"]:.2f}')
                c4.metric("Low", f'${quote["low"]:.2f}')
            profile = result.get("fh_profile") or result.get("fmp_profile")
            if profile:
                st.subheader(profile.get("name") or symbol)
                st.write(f'**Industry:** {profile.get("industry", "N/A")}  |  **Exchange:** {profile.get("exchange", "N/A")}')
            ticker_news = combine_news(result.get("fh_news"), result.get("fmp_news"))
            if ticker_news.empty:
                st.info("No ticker headlines returned.")
            else:
                st.dataframe(ticker_news[["published", "headline", "source", "provider", "sentiment", "catalyst_score", "catalyst_reason", "url"]], use_container_width=True, hide_index=True)

    with tab3:
        test_headline = st.text_area("Paste a headline", value="Company announces major contract award and raises guidance")
        score, label, reason = catalyst_score(test_headline)
        c1,c2,c3 = st.columns(3)
        c1.metric("Catalyst Score", score)
        c2.metric("Classification", label)
        c3.metric("Matched signal", reason)
        st.caption("This is a transparent keyword score for training and filtering—not a prediction or investment recommendation.")


elif page == "Live Data Diagnostics":
    st.title("Live Data Diagnostics")
    st.caption("Use this page to prove that the saved API keys are returning real data inside Spiderboys Trading Pro.")

    try:
        fmp_key = str(st.secrets.get("fmp", {}).get("api_key", "")).strip()
        finnhub_key = str(st.secrets.get("finnhub", {}).get("api_key", "")).strip()
    except Exception:
        fmp_key = finnhub_key = ""

    c1, c2 = st.columns(2)
    with c1:
        if fmp_key:
            st.success("FMP secret detected")
        else:
            st.error("FMP secret not detected")
    with c2:
        if finnhub_key:
            st.success("Finnhub secret detected")
        else:
            st.error("Finnhub secret not detected")

    test_symbol = st.text_input("Test symbol", value="AAPL", key="diagnostic_symbol").upper().strip()
    st.info("A green key indicator only proves the key is stored. The connection tests below prove the provider actually returned live information.")

    if st.button("Run Full Live Data Test", type="primary"):
        report = []
        live_payload = {}

        if finnhub_key:
            try:
                q = finnhub_quote(test_symbol, finnhub_key)
                live_payload["Finnhub Quote"] = pd.DataFrame([q])
                report.append({"Provider": "Finnhub", "Test": "Live quote", "Status": "WORKING", "Details": f'{test_symbol} price returned: ${q["price"]:.2f}'})
            except Exception as exc:
                report.append({"Provider": "Finnhub", "Test": "Live quote", "Status": "FAILED", "Details": str(exc)})

            try:
                n = finnhub_company_news(test_symbol, finnhub_key, lookback_days=7)
                live_payload["Finnhub Company News"] = n.head(10)
                report.append({"Provider": "Finnhub", "Test": "Company news", "Status": "WORKING" if not n.empty else "NO RESULTS", "Details": f"{len(n)} headlines returned"})
            except Exception as exc:
                report.append({"Provider": "Finnhub", "Test": "Company news", "Status": "FAILED", "Details": str(exc)})
        else:
            report.append({"Provider": "Finnhub", "Test": "Secret", "Status": "MISSING", "Details": "Add the Finnhub key in Streamlit Secrets."})

        if fmp_key:
            try:
                p = fmp_profile(test_symbol, fmp_key)
                live_payload["FMP Company Profile"] = pd.DataFrame([p])
                report.append({"Provider": "FMP", "Test": "Company profile", "Status": "WORKING", "Details": p.get("name") or test_symbol})
            except Exception as exc:
                report.append({"Provider": "FMP", "Test": "Company profile", "Status": "FAILED", "Details": str(exc)})

            try:
                fn = fmp_stock_news(fmp_key, symbol=test_symbol, limit=10)
                live_payload["FMP Stock News"] = fn.head(10)
                report.append({"Provider": "FMP", "Test": "Stock news", "Status": "WORKING" if not fn.empty else "NO RESULTS", "Details": f"{len(fn)} headlines returned"})
            except Exception as exc:
                report.append({"Provider": "FMP", "Test": "Stock news", "Status": "FAILED", "Details": str(exc)})
        else:
            report.append({"Provider": "FMP", "Test": "Secret", "Status": "MISSING", "Details": "Add the FMP key in Streamlit Secrets."})

        st.session_state["live_diagnostic_report"] = pd.DataFrame(report)
        st.session_state["live_diagnostic_payload"] = live_payload

    report = st.session_state.get("live_diagnostic_report")
    if report is not None:
        st.subheader("Connection Results")
        st.dataframe(report, use_container_width=True, hide_index=True)

        working = int((report["Status"] == "WORKING").sum())
        failed = int((report["Status"] == "FAILED").sum())
        a, b, c = st.columns(3)
        a.metric("Working Tests", working)
        b.metric("Failed Tests", failed)
        c.metric("Overall", "LIVE DATA WORKING" if working > 0 and failed == 0 else "CHECK RESULTS")

        for title, frame in st.session_state.get("live_diagnostic_payload", {}).items():
            with st.expander(title, expanded=True):
                if frame is None or frame.empty:
                    st.info("The provider returned no records for this test.")
                else:
                    st.dataframe(frame, use_container_width=True, hide_index=True)

        st.download_button(
            "Download Diagnostic Report",
            report.to_csv(index=False),
            "spiderboys_live_data_diagnostics.csv",
            mime="text/csv",
        )

    st.markdown("""
    ### Where to get information inside the app

    **Live Scanner** displays current watchlist prices, daily movement, company profile information, latest headlines, catalyst scores, and Spider Scores.

    **Live News Center** displays market headlines, ticker-specific news, quote information, company profiles, sentiment, and links to the original articles.

    **Live Data Diagnostics** confirms which provider and endpoint are working. It also shows the actual records returned by each provider.
    """)

elif page == "Live Data Hub":
    st.title("Live Data Hub")
    st.caption("Connect an Alpaca paper account while keeping safe demo mode available.")
    try:
        cfg=st.secrets.get("alpaca",{}); api_key=str(cfg.get("api_key","")).strip(); secret_key=str(cfg.get("secret_key","")).strip(); feed=str(cfg.get("feed","iex")).strip() or "iex"
    except Exception:
        api_key=secret_key=""; feed="iex"
    if not api_key or not secret_key:
        st.warning("Alpaca credentials have not been added to Streamlit Secrets.")
        st.code('[alpaca]\napi_key = "YOUR_ALPACA_KEY"\nsecret_key = "YOUR_ALPACA_SECRET"\nfeed = "iex"',language="toml")
        st.markdown("Add this through **Streamlit → Manage app → Settings → Secrets**. Never place API keys in GitHub.")
    else:
        st.success("Alpaca credentials detected.")
        if st.button("Test Paper Account Connection"):
            try: st.session_state["alpaca_account"]=get_account(api_key,secret_key); st.success("Paper account connected successfully.")
            except AlpacaError as exc: st.error(str(exc))
        account=st.session_state.get("alpaca_account")
        if account:
            a,b,c,d=st.columns(4); a.metric("Portfolio Value",f'${account["portfolio_value"]:,.2f}'); b.metric("Cash",f'${account["cash"]:,.2f}'); c.metric("Buying Power",f'${account["buying_power"]:,.2f}'); d.metric("Status",account["status"])
        st.subheader("Paper Positions")
        if st.button("Refresh Positions"):
            try: st.session_state["alpaca_positions"]=get_positions(api_key,secret_key)
            except AlpacaError as exc: st.error(str(exc))
        positions=st.session_state.get("alpaca_positions")
        if positions is not None:
            st.info("No open paper positions.") if positions.empty else st.dataframe(positions,use_container_width=True,hide_index=True)
        st.subheader("Live Ticker Lookup")
        c1,c2,c3=st.columns(3); symbol=c1.text_input("Symbol",value="SPY").upper().strip(); timeframe=c2.selectbox("Timeframe",["1Min","5Min","15Min","1Hour","1Day"]); limit=c3.slider("Bars",20,500,120)
        if st.button("Load Live Market Data"):
            try:
                st.session_state["live_snapshot"]=get_latest_snapshot(symbol,api_key,secret_key,feed); st.session_state["live_bars"]=get_bars(symbol,api_key,secret_key,timeframe,limit,feed); st.session_state["live_symbol"]=symbol
            except AlpacaError as exc: st.error(str(exc))
        snap=st.session_state.get("live_snapshot"); bars=st.session_state.get("live_bars"); live_symbol=st.session_state.get("live_symbol")
        if snap and live_symbol==symbol:
            a,b,c,d=st.columns(4); a.metric(symbol,f'${snap["price"]:.2f}',f'{snap["change_pct"]:.2f}%'); b.metric("Day High",f'${snap["day_high"]:.2f}'); c.metric("Day Low",f'${snap["day_low"]:.2f}'); d.metric("Day Volume",f'{snap["day_volume"]:,}')
        if bars is not None and not bars.empty and live_symbol==symbol:
            fig=go.Figure(); fig.add_trace(go.Candlestick(x=bars["datetime"],open=bars["open"],high=bars["high"],low=bars["low"],close=bars["close"],name=symbol)); fig.add_trace(go.Scatter(x=bars["datetime"],y=bars["vwap"],mode="lines",name="VWAP")); fig.update_layout(height=560,xaxis_rangeslider_visible=False); st.plotly_chart(fig,use_container_width=True)
        st.info("Live order submission is intentionally disabled. Version 4 is for data connection and paper-account monitoring.")

else:
    st.title("Integrations")
    st.caption("Roadmap for converting this workstation into a live system.")

    roadmap = pd.DataFrame([
        {"Phase":"1","Integration":"Market data provider","Purpose":"Live quotes, one-minute bars, scanner updates","Priority":"Highest"},
        {"Phase":"2","Integration":"News feed","Purpose":"Catalyst verification and headlines","Priority":"High"},
        {"Phase":"3","Integration":"Float/dilution data","Purpose":"Improve risk and scoring","Priority":"High"},
        {"Phase":"4","Integration":"Cloud database","Purpose":"Permanent journal and settings","Priority":"High"},
        {"Phase":"5","Integration":"Email/SMS alerts","Purpose":"Real-time setup notifications","Priority":"Medium"},
        {"Phase":"6","Integration":"Broker import","Purpose":"Automatic fills and journaling","Priority":"Later"},
        {"Phase":"7","Integration":"External AI API","Purpose":"Screenshot and trade-review coaching","Priority":"Later"},
    ])
    st.dataframe(roadmap, use_container_width=True, hide_index=True)

    st.warning("Do not enable live order execution until the scanner, risk rules, and journal have been validated in paper trading.")
