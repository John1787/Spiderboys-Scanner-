from pathlib import Path
import re
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
    finnhub_profile, finnhub_quote, fmp_intraday, fmp_profile, fmp_stock_news, catalyst_score
)

BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Spiderboys Trading Pro v9 Responsive Workstation",
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


/* v6.2 cleaner layout */
.block-container {
    max-width: 1280px;
    padding-top: .85rem;
}
.sb-hero-compact {
    padding: .85rem 1.05rem;
    border-radius: 15px;
    margin-bottom: .8rem;
}
.sb-hero-compact .sb-hero-title {
    font-size: 1.08rem;
}
.sb-hero-compact .sb-status-row {
    margin-top: .5rem;
}
[data-testid="stSidebar"] {
    min-width: 270px;
    max-width: 270px;
}
[data-testid="stSidebar"] [role="radiogroup"] > label {
    min-height: 44px;
    padding: .58rem .7rem;
    border-radius: 11px;
}
[data-testid="stSidebar"] [role="radiogroup"] > label p {
    font-size: .9rem !important;
}
[data-testid="stSidebar"] hr {
    margin: .8rem 0;
}
div[data-baseweb="select"] > div,
[data-baseweb="input"] > div {
    background-color: #10233a !important;
    color: #ffffff !important;
}
[data-baseweb="select"] span,
[data-baseweb="popover"] li {
    color: #ffffff !important;
}
[data-testid="stDataFrame"] {
    background: #0e1d30;
}
[data-testid="stDataFrame"] * {
    font-size: .84rem;
}
[data-testid="stAlert"] {
    padding-top: .65rem;
    padding-bottom: .65rem;
}


/* Version 9 integrated workstation */
[data-testid="stSidebar"] .stTextInput input {
    background: #10233a !important;
    border: 1px solid rgba(83,183,255,.55) !important;
    border-radius: 10px !important;
    font-weight: 850 !important;
    text-transform: uppercase;
}
.stTextInput input, .stNumberInput input,
div[data-baseweb="select"] > div {
    background: #10233a !important;
    color: #ffffff !important;
}
[data-testid="stDataFrame"] {
    background: #101f34 !important;
}
[data-testid="stDataFrame"] canvas {
    background: #101f34 !important;
}
[data-testid="stDataFrame"] [role="columnheader"] {
    background: #17314f !important;
    color: white !important;
}
[data-testid="stDataFrame"] [role="gridcell"] {
    color: #f5f9ff !important;
}


/* v8 premium polish */
.sb-ai-score {
    font-size: 2.4rem;
    font-weight: 900;
    line-height: 1;
}
[data-testid="stSidebar"] .stButton > button {
    min-height: 38px;
}
[data-testid="stMetric"] {
    min-height: 94px;
}
[data-testid="stMetricValue"] {
    font-size: 1.45rem !important;
}
[data-testid="stDataFrame"] {
    border-radius: 13px;
}
.stPlotlyChart {
    border: 1px solid rgba(74,144,226,.20);
    border-radius: 14px;
    overflow: hidden;
}


/* v9 responsive workstation */
@media (max-width: 1100px) {
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }
    [data-testid="stMetric"] {
        min-height: 82px;
        padding: 10px 11px;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.18rem !important;
    }
    .sb-hero {
        display: none;
    }
}
@media (max-width: 760px) {
    [data-testid="stSidebar"] {
        min-width: 235px;
        max-width: 235px;
    }
    h1 {
        font-size: 1.75rem !important;
    }
}
.sb-ai-score {
    font-size: 2.25rem;
    font-weight: 900;
    margin: .35rem 0;
}

</style>
""", unsafe_allow_html=True)

market = load_market(BASE_DIR)
journal = load_journal(BASE_DIR)
news = load_news(BASE_DIR)
indices = load_indices(BASE_DIR)

alerts = load_alerts(BASE_DIR)

try:
    FMP_KEY = str(st.secrets.get("fmp", {}).get("api_key", "")).strip()
    FINNHUB_KEY = str(st.secrets.get("finnhub", {}).get("api_key", "")).strip()
except Exception:
    FMP_KEY = FINNHUB_KEY = ""

if "active_ticker" not in st.session_state:
    st.session_state["active_ticker"] = str(market["ticker"].iloc[0]).upper()
if "layout_mode" not in st.session_state:
    st.session_state["layout_mode"] = "Compact"
if "saved_watchlist" not in st.session_state:
    st.session_state["saved_watchlist"] = ["SPY", "QQQ", "AAPL", "NVDA", st.session_state["active_ticker"]]

def normalize_symbol(value: str) -> str:
    return re.sub(r"[^A-Z0-9.\-]", "", str(value).upper().strip())[:12]

def set_active_ticker(value: str) -> None:
    symbol = normalize_symbol(value)
    if symbol:
        st.session_state["active_ticker"] = symbol

@st.cache_data(ttl=60, show_spinner=False)
def load_live_chart(symbol: str, interval: str, api_key: str):
    return fmp_intraday(symbol, api_key, interval)

def get_chart_frame(symbol: str, interval: str = "5min"):
    """Always return exactly: DataFrame, mode string, source note."""
    symbol = normalize_symbol(symbol)
    live_error = ""

    if FMP_KEY:
        try:
            bars = load_live_chart(symbol, interval, FMP_KEY)
            if isinstance(bars, pd.DataFrame) and not bars.empty:
                return bars.copy(), "LIVE", "FMP intraday bars"
            live_error = "FMP returned no usable intraday bars."
        except Exception as exc:
            live_error = f"{type(exc).__name__}: {exc}"
    else:
        live_error = "FMP key is not configured."

    try:
        demo = market[market["ticker"].astype(str).str.upper() == symbol].sort_values("datetime").copy()
    except Exception:
        demo = pd.DataFrame()

    if isinstance(demo, pd.DataFrame) and not demo.empty:
        return demo, "DEMO", f"Training fallback — {live_error}"

    return pd.DataFrame(), "UNAVAILABLE", live_error or "No chart source available."

def get_market_payload(symbol: str, interval: str = "5min") -> dict:
    """Unified, exception-safe data object used by Home, Charts, News and Trade Plan."""
    symbol = normalize_symbol(symbol)
    payload = {
        "symbol": symbol,
        "bars": pd.DataFrame(),
        "chart_mode": "UNAVAILABLE",
        "chart_note": "",
        "quote": {},
        "profile": {},
        "news": pd.DataFrame(),
        "errors": [],
    }

    try:
        bars, mode, note = get_chart_frame(symbol, interval)
        payload["bars"] = bars if isinstance(bars, pd.DataFrame) else pd.DataFrame()
        payload["chart_mode"] = str(mode)
        payload["chart_note"] = str(note)
    except Exception as exc:
        payload["errors"].append(f"Chart: {type(exc).__name__}: {exc}")

    if FINNHUB_KEY:
        try:
            payload["quote"] = finnhub_quote(symbol, FINNHUB_KEY) or {}
        except Exception as exc:
            payload["errors"].append(f"Finnhub quote: {type(exc).__name__}: {exc}")
        try:
            payload["profile"] = finnhub_profile(symbol, FINNHUB_KEY) or {}
        except Exception as exc:
            payload["errors"].append(f"Finnhub profile: {type(exc).__name__}: {exc}")
        try:
            payload["news"] = finnhub_company_news(symbol, FINNHUB_KEY, lookback_days=7)
        except Exception as exc:
            payload["errors"].append(f"Finnhub news: {type(exc).__name__}: {exc}")

    if not payload["profile"] and FMP_KEY:
        try:
            payload["profile"] = fmp_profile(symbol, FMP_KEY) or {}
        except Exception as exc:
            payload["errors"].append(f"FMP profile: {type(exc).__name__}: {exc}")

    return payload


def market_session_label() -> str:
    """Approximate U.S. equity session label using local server time."""
    now = pd.Timestamp.now(tz="America/New_York")
    weekday = now.weekday()
    minutes = now.hour * 60 + now.minute
    if weekday >= 5:
        return "Closed"
    if 4 * 60 <= minutes < 9 * 60 + 30:
        return "Premarket"
    if 9 * 60 + 30 <= minutes < 16 * 60:
        return "Open"
    if 16 * 60 <= minutes < 20 * 60:
        return "After Hours"
    return "Closed"

def safe_quote(symbol: str) -> dict:
    if not FINNHUB_KEY:
        return {}
    try:
        return finnhub_quote(symbol, FINNHUB_KEY) or {}
    except Exception:
        return {}

def build_watchlist_snapshot(symbols: list[str]) -> pd.DataFrame:
    rows = []
    for symbol in symbols[:12]:
        q = safe_quote(symbol)
        rows.append({
            "symbol": symbol,
            "price": q.get("price"),
            "change_pct": q.get("change_pct"),
            "high": q.get("high"),
            "low": q.get("low"),
        })
    return pd.DataFrame(rows)

def compact_news_view(news: pd.DataFrame, limit: int = 6) -> pd.DataFrame:
    if not isinstance(news, pd.DataFrame) or news.empty:
        return pd.DataFrame()
    cols = [c for c in ["published", "headline", "source", "url"] if c in news.columns]
    return news[cols].head(limit).copy()

def spider_ai_summary(payload: dict) -> dict:
    """Transparent rule-based setup summary; not a prediction."""
    bars = payload.get("bars", pd.DataFrame())
    news = payload.get("news", pd.DataFrame())
    quote = payload.get("quote", {}) or {}
    profile = payload.get("profile", {}) or {}

    score = 0
    reasons = []
    trend = "Unknown"
    entry = stop = target = None

    if isinstance(bars, pd.DataFrame) and not bars.empty:
        bars = bars.sort_values("datetime").copy()
        last = bars.iloc[-1]
        close = float(last.get("close", 0) or 0)
        vwap = float(last.get("vwap", close) or close)
        ema9 = float(last.get("ema9", close) or close)
        ema20 = float(last.get("ema20", close) or close)

        if close > vwap:
            score += 20
            reasons.append("Price is above VWAP")
        if ema9 > ema20:
            score += 20
            reasons.append("EMA 9 is above EMA 20")
        if close > ema9:
            score += 10
            reasons.append("Price is holding above EMA 9")

        recent = bars.tail(min(12, len(bars)))
        entry = float(recent["high"].max())
        stop = float(recent["low"].min())
        risk = max(entry - stop, 0)
        target = entry + (2 * risk) if risk > 0 else None
        trend = "Bullish" if close > vwap and ema9 > ema20 else "Mixed"

    day_change = float(quote.get("change_pct", 0) or 0)
    if day_change >= 3:
        score += 15
        reasons.append("Strong positive daily momentum")
    elif day_change > 0:
        score += 7
        reasons.append("Positive daily momentum")

    if isinstance(news, pd.DataFrame) and not news.empty:
        score += 15
        reasons.append("Recent company news is available")

    market_cap = profile.get("market_cap") or profile.get("marketCapitalization")
    try:
        if market_cap and float(market_cap) < 2_000_000_000:
            score += 10
            reasons.append("Smaller market capitalization")
    except Exception:
        pass

    score = max(0, min(100, int(score)))
    grade = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "WATCH"
    confidence = "High" if score >= 80 else "Moderate" if score >= 60 else "Low"

    return {
        "score": score,
        "grade": grade,
        "confidence": confidence,
        "trend": trend,
        "entry": entry,
        "stop": stop,
        "target_2r": target,
        "reasons": reasons or ["Insufficient live information for a complete setup review"],
    }

def candlestick_chart(ticker, height=620, show_levels=True, interval="5min"):
    g, mode, source_note = get_chart_frame(ticker, interval)
    if g.empty:
        st.error(f"No chart data available for {ticker}. {source_note}")
        st.info("Quotes and news may still be live. Intraday candles require a provider/plan that includes historical bars.")
        return pd.DataFrame(), mode

    g = g.sort_values("datetime").copy()
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=g["datetime"], open=g["open"], high=g["high"], low=g["low"], close=g["close"],
        name=ticker
    ))
    for col, label in [("vwap", "VWAP"), ("ema9", "EMA 9"), ("ema20", "EMA 20")]:
        if col in g.columns:
            fig.add_trace(go.Scatter(x=g["datetime"], y=g[col], mode="lines", name=label))

    if show_levels and mode == "DEMO":
        last = g.iloc[-1]
        for field, dash, label in [
            ("premarket_high", "dash", "PM High"),
            ("previous_day_high", "dot", "PD High"),
            ("entry", "dash", "Entry"),
            ("stop", "dot", "Stop"),
        ]:
            if field in g.columns:
                fig.add_hline(y=float(last[field]), line_dash=dash, annotation_text=label)

    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=28, b=8),
        xaxis_rangeslider_visible=False,
        legend_orientation="h",
        legend_y=1.02,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(8,18,32,.55)",
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
    if mode == "LIVE":
        st.success(f"● LIVE CHART — {source_note}", icon="✅")
    elif mode == "DEMO":
        st.warning(f"DEMO CHART — {source_note}", icon="⚠️")
    else:
        st.error(f"CHART UNAVAILABLE — {source_note}")
    return g, mode

def watchlist_table(scan):
    cols = [
        "ticker","price","gap_pct","float_m","premarket_volume","relative_volume",
        "spider_score","quality","setup_status","entry","stop","target_2r"
    ]
    st.dataframe(scan[cols], use_container_width=True, hide_index=True)


# -------------------------------------------------------------------
# Application shell and navigation
# -------------------------------------------------------------------
st.sidebar.markdown("""
<div style="padding:.65rem .25rem .9rem .25rem;">
  <div style="font-size:1.48rem;font-weight:900;color:#ffffff;">🕷️ Spiderboys</div>
  <div style="font-size:1.05rem;font-weight:800;color:#65d9ff;">Trading Pro</div>
  <div style="font-size:.78rem;color:#ffffff;margin-top:.2rem;">Responsive Workstation v9.0</div>
</div>
""", unsafe_allow_html=True)

main_nav = st.sidebar.radio(
    "Main Menu",
    [
        "🏠 Command Center",
        "⚡ Live Scanner",
        "📰 Live News",
        "📈 Charts",
        "🧭 Trade Plan",
        "📓 Journal",
        "📊 Performance",
        "🧰 More Tools",
    ],
    label_visibility="collapsed",
    key="main_navigation",
)

_main_page_map = {
    "🏠 Command Center": "Morning Command Center",
    "⚡ Live Scanner": "Live Scanner",
    "📰 Live News": "Live News Center",
    "📈 Charts": "Professional Charts",
    "🧭 Trade Plan": "Trade Planner",
    "📓 Journal": "Trading Journal",
    "📊 Performance": "Performance Analytics",
}
page = _main_page_map.get(main_nav, "Morning Command Center")

if main_nav == "🧰 More Tools":
    page = st.sidebar.selectbox(
        "Additional tools",
        [
            "Live Data Diagnostics",
            "Market Intelligence",
            "Live-Style Scanner",
            "AI Trade Coach",
            "Replay Academy",
            "Risk Command Center",
            "Alert Center",
            "Daily Process",
            "Live Data Hub",
            "Integrations",
        ],
        key="secondary_navigation",
    )

st.sidebar.markdown("---")
st.sidebar.caption("LAYOUT")
st.session_state["layout_mode"] = st.sidebar.segmented_control(
    "Layout mode",
    options=["Compact", "Desk"],
    default=st.session_state.get("layout_mode", "Compact"),
    label_visibility="collapsed",
    key="layout_mode_control",
)
st.sidebar.caption("Compact fits smaller windows. Desk adds side panels.")

st.sidebar.markdown("---")
st.sidebar.caption("ACTIVE TICKER")
ticker_col, apply_col = st.sidebar.columns([3, 1])
with ticker_col:
    _ticker_entry = st.text_input(
        "Ticker",
        value=st.session_state["active_ticker"],
        label_visibility="collapsed",
        key="global_ticker_input",
        placeholder="AAPL",
    )
with apply_col:
    if st.button("↵", key="apply_global_ticker", help="Load ticker across the app"):
        set_active_ticker(_ticker_entry)
        st.rerun()

st.sidebar.caption(f'Linked across app: **{st.session_state["active_ticker"]}**')
st.sidebar.markdown("---")

_fmp_ok = bool(FMP_KEY)
_fh_ok = bool(FINNHUB_KEY)

st.sidebar.success("HYBRID LIVE MODE")
st.sidebar.markdown(
    f"""
    <div class="sb-card" style="padding:.75rem .8rem;margin-top:.55rem;">
      <div class="sb-card-title" style="font-size:.86rem;">DATA CONNECTIONS</div>
      <div class="sb-muted">{"🟢" if _fmp_ok else "🔴"} FMP key</div>
      <div class="sb-muted">{"🟢" if _fh_ok else "🔴"} Finnhub key</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.caption("Green means the key was detected. Diagnostics confirms whether each endpoint responds.")

st.markdown("""
<div class="sb-hero sb-hero-compact">
  <div class="sb-hero-title">Spiderboys Trading Pro</div>
  <div class="sb-hero-sub">Spider AI · scanner · news · charts · planning · journal</div>
  <div class="sb-status-row">
    <span class="sb-chip sb-chip-live">● Hybrid data engine</span>
    <span class="sb-chip sb-chip-safe">Analysis mode</span>
  </div>
</div>
""", unsafe_allow_html=True)

# Defensive guard: page should always exist even if navigation changes later.
if not isinstance(page, str) or not page:
    page = "Morning Command Center"


if page == "Morning Command Center":
    active = st.session_state["active_ticker"]
    layout_mode = st.session_state.get("layout_mode", "Compact")
    payload = get_market_payload(active, "5min")
    ai = spider_ai_summary(payload)
    quote = payload.get("quote", {}) or {}
    session = market_session_label()

    st.title("Spider AI Command Center")
    st.caption("What is moving, what is valid, and what needs your attention right now.")

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Market", session)
    k2.metric("Ticker", active)
    k3.metric("Last", f'${float(quote.get("price")):.2f}' if quote.get("price") else "—",
              f'{float(quote.get("change_pct", 0)):+.2f}%' if quote else None)
    k4.metric("Spider Score", f'{ai["score"]}/100')
    k5.metric("Grade", ai["grade"])
    k6.metric("Data", payload["chart_mode"])

    if layout_mode == "Desk":
        left, center, right = st.columns([1.0, 2.25, 1.05])

        with left:
            st.subheader("Watchlist")
            watch = build_watchlist_snapshot(st.session_state["saved_watchlist"])
            if not watch.empty:
                st.dataframe(
                    watch,
                    use_container_width=True,
                    hide_index=True,
                    height=300,
                    column_config={
                        "price": st.column_config.NumberColumn(format="$%.2f"),
                        "change_pct": st.column_config.NumberColumn("Day %", format="%.2f%%"),
                        "high": st.column_config.NumberColumn(format="$%.2f"),
                        "low": st.column_config.NumberColumn(format="$%.2f"),
                    },
                )
            st.caption("Use the sidebar ticker box or Scanner row to change the linked symbol.")

            st.subheader("Quick Filters")
            f1, f2 = st.columns(2)
            with f1:
                st.button("Under $10", use_container_width=True, key="filter_under10")
                st.button("Low Float", use_container_width=True, key="filter_lowfloat")
            with f2:
                st.button("Gap Up", use_container_width=True, key="filter_gap")
                st.button("High RVOL", use_container_width=True, key="filter_rvol")

        with center:
            st.subheader(f"{active} Chart")
            candlestick_chart(active, 520, interval="5min")

        with right:
            st.subheader("Spider AI")
            st.markdown(
                f"""
                <div class="sb-card">
                  <div class="sb-card-title">{active} Setup</div>
                  <div class="sb-ai-score">{ai["score"]}/100</div>
                  <div class="sb-muted">Grade {ai["grade"]} · {ai["confidence"]} confidence</div>
                  <hr>
                  <div><b>Trend:</b> {ai["trend"]}</div>
                  <div><b>Entry:</b> {"$"+format(ai["entry"], ".2f") if ai["entry"] else "—"}</div>
                  <div><b>Stop:</b> {"$"+format(ai["stop"], ".2f") if ai["stop"] else "—"}</div>
                  <div><b>2R:</b> {"$"+format(ai["target_2r"], ".2f") if ai["target_2r"] else "—"}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            for reason in ai["reasons"][:5]:
                st.write(f"✓ {reason}")

            news_small = compact_news_view(payload.get("news"), 4)
            if not news_small.empty:
                st.subheader("Latest News")
                for _, row in news_small.iterrows():
                    st.markdown(f"**{row.get('headline', '')}**")
                    st.caption(str(row.get("source", "")))

    else:
        top_left, top_right = st.columns([1.7, 1])
        with top_left:
            st.subheader(f"{active} Chart")
            candlestick_chart(active, 500, interval="5min")
        with top_right:
            st.subheader("Spider AI")
            st.markdown(
                f"""
                <div class="sb-card">
                  <div class="sb-card-title">{active} Setup Summary</div>
                  <div class="sb-ai-score">{ai["score"]}/100</div>
                  <div class="sb-muted">Grade {ai["grade"]} · {ai["confidence"]} confidence</div>
                  <hr>
                  <div><b>Trend:</b> {ai["trend"]}</div>
                  <div><b>Entry:</b> {"$"+format(ai["entry"], ".2f") if ai["entry"] else "—"}</div>
                  <div><b>Stop:</b> {"$"+format(ai["stop"], ".2f") if ai["stop"] else "—"}</div>
                  <div><b>2R Target:</b> {"$"+format(ai["target_2r"], ".2f") if ai["target_2r"] else "—"}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            for reason in ai["reasons"][:4]:
                st.write(f"✓ {reason}")

        tab1, tab2, tab3 = st.tabs(["Watchlist", "News", "Alerts"])
        with tab1:
            watch = build_watchlist_snapshot(st.session_state["saved_watchlist"])
            if not watch.empty:
                st.dataframe(
                    watch,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "price": st.column_config.NumberColumn(format="$%.2f"),
                        "change_pct": st.column_config.NumberColumn("Day %", format="%.2f%%"),
                    },
                )
        with tab2:
            news_small = compact_news_view(payload.get("news"), 8)
            if news_small.empty:
                st.info("No recent company news returned.")
            else:
                st.dataframe(
                    news_small,
                    use_container_width=True,
                    hide_index=True,
                    column_config={"url": st.column_config.LinkColumn("Article")},
                )
        with tab3:
            st.info("No triggered alerts for the active ticker.")

    st.subheader("Saved Watchlist")
    watch_text = st.text_input(
        "Tickers separated by commas",
        value=", ".join(st.session_state["saved_watchlist"]),
        key="watchlist_editor_v9",
    )
    if st.button("Save Watchlist", type="primary"):
        parsed = [normalize_symbol(x) for x in watch_text.split(",")]
        st.session_state["saved_watchlist"] = list(dict.fromkeys([x for x in parsed if x]))[:20]
        st.success("Watchlist saved for this session.")

    if payload["errors"]:
        with st.expander("Data connection notes"):
            for error in payload["errors"]:
                st.caption(error)

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

        ticker = st.selectbox("Inspect candidate", scan["ticker"].tolist(), index=0)
        set_active_ticker(ticker)
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
    st.title("Charts")
    st.caption("Type any supported U.S. ticker. The symbol is shared with Scanner, News, and Trade Plan.")

    c_symbol, c_interval, c_refresh = st.columns([3, 1, 1])
    with c_symbol:
        chart_symbol = st.text_input(
            "Ticker search",
            value=st.session_state["active_ticker"],
            key="chart_symbol_input",
            placeholder="Type AAPL, SOUN, TSLA...",
        )
    with c_interval:
        interval = st.selectbox("Timeframe", ["1min", "5min", "15min", "30min"], index=1)
    with c_refresh:
        st.write("")
        st.write("")
        load_clicked = st.button("Load Chart", type="primary", use_container_width=True)

    if load_clicked:
        set_active_ticker(chart_symbol)
        st.cache_data.clear()
        st.rerun()

    ticker = st.session_state["active_ticker"]
    bars, chart_mode = candlestick_chart(ticker, 680, interval=interval)

    if not bars.empty:
        last = bars.iloc[-1]
        previous = bars.iloc[-2] if len(bars) > 1 else last
        change_pct = ((last["close"] / previous["close"]) - 1) * 100 if previous["close"] else 0
        high = float(bars["high"].max())
        low = float(bars["low"].min())
        volume = float(bars["volume"].sum()) if "volume" in bars else 0
        vwap = float(last.get("vwap", last["close"]))

        a,b,c,d,e = st.columns(5)
        a.metric("Last", f'${last["close"]:.2f}', f"{change_pct:.2f}% bar")
        b.metric("VWAP", f"${vwap:.2f}")
        c.metric("Chart High", f"${high:.2f}")
        d.metric("Chart Low", f"${low:.2f}")
        e.metric("Volume", f"{volume:,.0f}")

        st.subheader("Automatic Levels")
        recent = bars.tail(min(20, len(bars)))
        support = float(recent["low"].min())
        resistance = float(recent["high"].max())
        levels = pd.DataFrame([
            {"Level":"Current Price","Price":float(last["close"]),"Meaning":"Most recent bar close"},
            {"Level":"VWAP","Price":vwap,"Meaning":"Volume-weighted intraday reference"},
            {"Level":"EMA 9","Price":float(last.get("ema9", last["close"])),"Meaning":"Short-term momentum"},
            {"Level":"EMA 20","Price":float(last.get("ema20", last["close"])),"Meaning":"Trend reference"},
            {"Level":"Recent Support","Price":support,"Meaning":"Lowest low in recent bars"},
            {"Level":"Recent Resistance","Price":resistance,"Meaning":"Highest high in recent bars"},
        ])
        st.dataframe(
            levels,
            use_container_width=True,
            hide_index=True,
            column_config={"Price": st.column_config.NumberColumn(format="$%.2f")},
        )

        if FINNHUB_KEY:
            try:
                quote = finnhub_quote(ticker, FINNHUB_KEY)
                st.caption(
                    f'Finnhub quote: ${quote["price"]:.2f} · Day {quote["change_pct"]:+.2f}% · '
                    f'High ${quote["high"]:.2f} · Low ${quote["low"]:.2f}'
                )
            except MarketDataError as exc:
                st.caption(f"Quote note: {exc}")

elif page == "Trade Planner":
    st.title("Trade Plan")
    st.caption(f'Building a plan for the linked ticker: **{st.session_state["active_ticker"]}**')

    symbol_col, load_col = st.columns([4, 1])
    with symbol_col:
        planner_symbol = st.text_input("Ticker", value=st.session_state["active_ticker"], key="planner_symbol")
    with load_col:
        st.write("")
        st.write("")
        if st.button("Use Ticker", type="primary", use_container_width=True):
            set_active_ticker(planner_symbol)
            st.rerun()

    ticker = st.session_state["active_ticker"]
    payload = get_market_payload(ticker, "5min")
    bars = payload["bars"]
    chart_mode = payload["chart_mode"]
    ai = spider_ai_summary(payload)

    if bars.empty:
        st.error(f"No usable chart data is available for {ticker}.")
        if payload["errors"]:
            with st.expander("Technical details"):
                for error in payload["errors"]:
                    st.caption(error)
    else:
        bars = bars.sort_values("datetime").copy()
        last = bars.iloc[-1]
        recent = bars.tail(min(12, len(bars)))
        suggested_entry = float(ai["entry"] or last["high"])
        suggested_stop = float(ai["stop"] or recent["low"].min())

        left, right = st.columns([1.7, 1])
        with left:
            candlestick_chart(ticker, 560, interval="5min")
        with right:
            account = st.number_input("Account Size", min_value=0.0, value=10000.0, step=500.0)
            risk_pct = st.number_input("Risk Per Trade %", min_value=0.05, value=0.5, step=0.1)
            entry = st.number_input("Planned Entry", min_value=0.01, value=round(suggested_entry, 2), step=0.01)
            stop = st.number_input("Planned Stop", min_value=0.01, value=round(suggested_stop, 2), step=0.01)

            risk_per_share = max(0.0, entry - stop)
            dollar_risk = account * (risk_pct / 100)
            shares = int(dollar_risk // risk_per_share) if risk_per_share > 0 else 0
            target_1r = entry + risk_per_share
            target_2r = entry + (2 * risk_per_share)
            buying_power = shares * entry

            st.metric("Recommended Shares", f"{shares:,}")
            st.write(f"Risk/share: **${risk_per_share:.2f}**")
            st.write(f"Dollar risk: **${dollar_risk:.2f}**")
            st.write(f"1R target: **${target_1r:.2f}**")
            st.write(f"2R target: **${target_2r:.2f}**")
            st.write(f"Buying power: **${buying_power:,.2f}**")

        st.subheader("Pre-Trade Checklist")
        checklist_items = [
            ("Price is above VWAP", float(last["close"]) > float(last.get("vwap", last["close"]))),
            ("EMA 9 is above EMA 20", float(last.get("ema9", 0)) > float(last.get("ema20", 0))),
            ("Entry is above stop", entry > stop),
            ("At least 2R target is defined", target_2r > entry),
            ("Catalyst/news reviewed", not payload["news"].empty if isinstance(payload["news"], pd.DataFrame) else False),
            ("Pullback confirmed; not anticipating", False),
            ("Spread and liquidity acceptable", False),
            ("Daily risk limit checked", False),
        ]
        checked = []
        cols = st.columns(2)
        for idx, (label, suggested) in enumerate(checklist_items):
            with cols[idx % 2]:
                checked.append(st.checkbox(label, value=suggested, key=f"plan_check_{ticker}_{idx}"))

        completion = sum(checked) / len(checked)
        score = int(round(completion * 100))
        grade = "A" if score >= 88 else "B" if score >= 75 else "C" if score >= 60 else "NO TRADE"

        a, b, c, d = st.columns(4)
        a.metric("Plan Completion", f"{score}%")
        b.metric("Trade Grade", grade)
        c.metric("Spider Score", f'{ai["score"]}/100')
        d.metric("Data Mode", chart_mode)

        plan_frame = pd.DataFrame([{
            "ticker": ticker,
            "entry": entry,
            "stop": stop,
            "target_1r": target_1r,
            "target_2r": target_2r,
            "shares": shares,
            "dollar_risk": dollar_risk,
            "plan_grade": grade,
            "spider_score": ai["score"],
            "chart_mode": chart_mode,
        }])
        st.download_button(
            "Download Trade Plan",
            plan_frame.to_csv(index=False),
            f"{ticker}_trade_plan.csv",
            mime="text/csv",
        )
        if grade == "A":
            st.success("Plan complete. Wait for the actual trigger and honor the stop.")
        else:
            st.warning("Plan incomplete. Resolve unchecked items before considering an entry.")

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
    st.caption("Demo journal analytics until your own trades are added.")
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

    st.subheader("Visual Performance")
    if not journal.empty:
        jv = journal.copy()
        jv["date"] = pd.to_datetime(jv["date"], errors="coerce")
        jv = jv.sort_values("date")
        jv["equity"] = pd.to_numeric(jv["pnl"], errors="coerce").fillna(0).cumsum()

        equity_fig = go.Figure()
        equity_fig.add_trace(go.Scatter(
            x=jv["date"], y=jv["equity"], mode="lines+markers", name="Cumulative P/L"
        ))
        equity_fig.update_layout(
            height=330, margin=dict(l=8, r=8, t=25, b=8),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(8,18,32,.55)"
        )
        st.plotly_chart(equity_fig, use_container_width=True, config={"displaylogo": False})

        setup_chart = jv.groupby("setup", as_index=False)["pnl"].sum().sort_values("pnl", ascending=False)
        bar_fig = go.Figure(go.Bar(x=setup_chart["setup"], y=setup_chart["pnl"]))
        bar_fig.update_layout(
            height=320, margin=dict(l=8, r=8, t=25, b=8),
            xaxis_title="", yaxis_title="Net P/L",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(8,18,32,.55)"
        )
        st.plotly_chart(bar_fig, use_container_width=True, config={"displaylogo": False})

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
    st.caption("Filter a focused watchlist, then select a row to link that ticker across the app.")

    filter_cols = st.columns(5)
    with filter_cols[0]:
        max_price = st.number_input("Max price", min_value=1.0, value=50.0, step=5.0)
    with filter_cols[1]:
        min_change = st.number_input("Min day %", value=0.0, step=1.0)
    with filter_cols[2]:
        min_score = st.slider("Min Spider Score", 0, 100, 40)
    with filter_cols[3]:
        news_only = st.checkbox("News only")
    with filter_cols[4]:
        positive_only = st.checkbox("Green only")
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
                good = good.sort_values("spider_score", ascending=False).reset_index(drop=True)
                if "price" in good.columns:
                    good = good[pd.to_numeric(good["price"], errors="coerce") <= max_price]
                if "change_pct" in good.columns:
                    good = good[pd.to_numeric(good["change_pct"], errors="coerce") >= min_change]
                    if positive_only:
                        good = good[pd.to_numeric(good["change_pct"], errors="coerce") > 0]
                if "spider_score" in good.columns:
                    good = good[pd.to_numeric(good["spider_score"], errors="coerce") >= min_score]
                if news_only and "latest_headline" in good.columns:
                    good = good[good["latest_headline"].astype(str).str.len() > 8]
                selection = st.dataframe(
                    good,
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row",
                    key="live_scanner_table",
                    column_config={
                        "price": st.column_config.NumberColumn(format="$%.2f"),
                        "change_pct": st.column_config.NumberColumn("Day %", format="%.2f%%"),
                        "spider_score": st.column_config.ProgressColumn("Spider Score", min_value=0, max_value=100),
                    },
                )
                selected_rows = selection.selection.rows if selection is not None else []
                if selected_rows:
                    selected_symbol = str(good.iloc[selected_rows[0]]["symbol"])
                    set_active_ticker(selected_symbol)
                    st.success(f"{selected_symbol} is now linked to Charts, News, and Trade Plan.")
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
    with a:
        if fmp_key:
            st.success("FMP connected")
        else:
            st.warning("FMP not connected")
    with b:
        if finnhub_key:
            st.success("Finnhub connected")
        else:
            st.warning("Finnhub not connected")

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
                st.caption(f"Data note: {error}")
            if combined.empty:
                st.info("No headlines were returned by the available free-plan endpoints.")
            else:
                c_filter, c_count = st.columns([3, 1])
                with c_filter:
                    sentiment_filter = st.multiselect(
                        "Sentiment",
                        ["Bullish", "Neutral", "Bearish"],
                        default=["Bullish", "Neutral", "Bearish"],
                    )
                with c_count:
                    headline_count = st.selectbox("Show", [10, 25, 50], index=1)

                view = combined[combined["sentiment"].isin(sentiment_filter)].head(headline_count).copy()
                st.dataframe(
                    view[["published", "symbol", "headline", "source", "sentiment", "catalyst_score"]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "published": st.column_config.DatetimeColumn("Time", format="MMM D, h:mm a"),
                        "symbol": st.column_config.TextColumn("Ticker", width="small"),
                        "headline": st.column_config.TextColumn("Headline", width="large"),
                        "source": st.column_config.TextColumn("Source", width="medium"),
                        "sentiment": st.column_config.TextColumn("Signal", width="small"),
                        "catalyst_score": st.column_config.NumberColumn("Score", width="small"),
                    },
                )
                with st.expander("Article links and full catalyst details"):
                    st.dataframe(
                        view[["headline", "provider", "catalyst_reason", "url"]],
                        use_container_width=True,
                        hide_index=True,
                        column_config={"url": st.column_config.LinkColumn("Open article")},
                    )

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
                st.caption(f"Data note: {error}")
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
        st.caption("Working means the endpoint returned usable data. Restricted means the API plan does not include that endpoint.")
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
