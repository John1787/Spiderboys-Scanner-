from pathlib import Path
import re
import json
from datetime import datetime, date, time
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
    page_title="Spiderboys Trading Pro v12 Pro Scanner + Journal",
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


.workspace-kicker{font-size:.7rem;letter-spacing:.16em;color:#63dcff!important;font-weight:900}
.workspace-heading{font-size:1.55rem;color:#fff!important;font-weight:900}
.panel-label{color:#7fe6ff!important;font-size:.72rem;font-weight:900;letter-spacing:.12em;padding:.35rem 0 .45rem;border-bottom:1px solid rgba(79,175,255,.25);margin-bottom:.55rem}
.ai-panel{min-height:260px}
.grade-row{display:flex;justify-content:space-between;padding:.45rem .6rem;margin:.55rem 0;border-radius:9px;background:rgba(24,83,133,.35);font-weight:850}
.level-grid{display:grid;grid-template-columns:1fr 1fr;gap:.55rem}
.level-grid.one-col{grid-template-columns:1fr}
.level-grid>div{background:rgba(7,20,34,.55);border:1px solid rgba(74,144,226,.18);border-radius:9px;padding:.55rem .6rem}
.level-grid small{display:block;color:#9fdcff!important;font-size:.68rem;text-transform:uppercase;letter-spacing:.08em}
.level-grid b{display:block;color:#fff!important;margin-top:.12rem}
.dock-divider{height:1px;background:linear-gradient(90deg,transparent,rgba(61,199,255,.55),transparent);margin:1rem 0 .65rem}
[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"]{display:flex!important;visibility:visible!important;opacity:1!important}
[data-testid="stSidebarCollapsedControl"]{background:#1468c9!important;border:1px solid #6de4ff!important;border-radius:0 10px 10px 0!important}


/* v11 scanner terminal */
.block-container {
    max-width: 1880px;
    padding-left: 1rem;
    padding-right: 1rem;
}
.workspace-subtitle {
    color: #a9c8e7 !important;
    font-size: .82rem;
    margin-top: .15rem;
}
.terminal-panel-title {
    background: linear-gradient(90deg, rgba(17,64,105,.95), rgba(11,38,66,.72));
    border: 1px solid rgba(72,177,240,.34);
    border-radius: 7px 7px 0 0;
    color: #8fdfff !important;
    font-size: .73rem;
    font-weight: 900;
    letter-spacing: .11em;
    padding: .48rem .6rem;
    margin: .25rem 0 .35rem 0;
}
.scanner-status-row {
    display: flex;
    gap: .55rem;
    flex-wrap: wrap;
    margin: .45rem 0 .65rem 0;
}
.scanner-status-row span {
    background: rgba(17,54,89,.92);
    border: 1px solid rgba(67,170,235,.34);
    border-radius: 999px;
    padding: .3rem .68rem;
    color: #d9f2ff !important;
    font-size: .7rem;
    font-weight: 850;
    letter-spacing: .04em;
}
.stock-card {
    position: relative;
    background: linear-gradient(145deg, rgba(18,45,76,.98), rgba(7,25,44,.98));
    border: 1px solid rgba(66,177,243,.34);
    border-radius: 12px;
    padding: .8rem .85rem;
    margin-bottom: .55rem;
}
.stock-symbol {
    color: #ffffff !important;
    font-size: 1.35rem;
    font-weight: 950;
}
.stock-name {
    color: #9fc5e8 !important;
    font-size: .8rem;
    padding-right: 3rem;
}
.stock-change {
    position: absolute;
    top: .85rem;
    right: .8rem;
    color: #55f38d !important;
    font-weight: 900;
}
.mini-empty {
    min-height: 210px;
    display: grid;
    place-items: center;
    text-align: center;
    background: rgba(8,24,42,.78);
    border: 1px solid rgba(74,144,226,.24);
    border-radius: 10px;
    color: #dbeeff !important;
    padding: 1rem;
}
[data-testid="stDataFrame"] {
    border-radius: 7px !important;
    border: 1px solid rgba(77,169,225,.42) !important;
}
[data-testid="stDataFrame"] * {
    font-size: .78rem !important;
}
[data-testid="stDataFrame"] [role="columnheader"] {
    background: #153754 !important;
    color: #c9eaff !important;
    font-weight: 850 !important;
}
@media (max-width: 1200px) {
    .block-container {
        max-width: 100%;
    }
    [data-testid="stDataFrame"] * {
        font-size: .72rem !important;
    }
}


/* v12 premium scanner and journal */
.scanner-description {
    background: linear-gradient(90deg, rgba(19,58,96,.86), rgba(9,31,55,.72));
    border: 1px solid rgba(81,180,239,.28);
    border-radius: 10px;
    color: #dff4ff !important;
    font-size: .84rem;
    padding: .62rem .78rem;
    margin: .35rem 0 .6rem 0;
}
.journal-section-title {
    background: linear-gradient(90deg, rgba(26,87,139,.95), rgba(10,42,72,.72));
    border-left: 4px solid #42dcff;
    border-radius: 7px;
    color: #ffffff !important;
    font-size: .76rem;
    font-weight: 950;
    letter-spacing: .13em;
    padding: .55rem .72rem;
    margin: .35rem 0 .75rem 0;
}
[data-testid="stForm"] {
    background: linear-gradient(145deg, rgba(14,34,57,.96), rgba(8,24,42,.94));
    border: 1px solid rgba(71,159,222,.30);
    border-radius: 14px;
    padding: 1rem 1rem .85rem 1rem;
    box-shadow: 0 12px 28px rgba(0,0,0,.18);
}
[data-testid="stFileUploader"] {
    background: rgba(12,31,52,.72);
    border: 1px solid rgba(71,159,222,.24);
    border-radius: 12px;
    padding: .55rem;
}
[data-baseweb="tab-list"] {
    gap: .3rem;
}
[data-baseweb="tab"] {
    border-radius: 9px 9px 0 0;
    font-weight: 800;
}
[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, rgba(34,111,211,.9), rgba(20,151,173,.78));
}
@media (max-width: 1100px) {
    [data-testid="stForm"] {
        padding: .75rem;
    }
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
if "scanner_panel_open" not in st.session_state:
    st.session_state["scanner_panel_open"] = True
if "right_panel_open" not in st.session_state:
    st.session_state["right_panel_open"] = True
if "scanner_view" not in st.session_state:
    st.session_state["scanner_view"] = "HOD Momentum"
if "scanner_data_mode" not in st.session_state:
    st.session_state["scanner_data_mode"] = "Training + Live Quotes"

JOURNAL_COLUMNS = [
    "trade_id", "date", "time", "ticker", "side", "setup", "entry", "exit", "stop",
    "shares", "fees", "pnl", "risk_amount", "r_multiple", "win", "execution_grade",
    "emotion", "followed_plan", "catalyst", "mistake", "lesson", "notes",
]
if "user_trade_journal" not in st.session_state:
    st.session_state["user_trade_journal"] = pd.DataFrame(columns=JOURNAL_COLUMNS)
if "journal_prefill_ticker" not in st.session_state:
    st.session_state["journal_prefill_ticker"] = st.session_state["active_ticker"]
if "journal_import_mode" not in st.session_state:
    st.session_state["journal_import_mode"] = "Append"
if "daily_journal_notes" not in st.session_state:
    st.session_state["daily_journal_notes"] = {}



def empty_user_journal() -> pd.DataFrame:
    return pd.DataFrame(columns=JOURNAL_COLUMNS)


def normalize_user_journal(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize imported or edited journal data to the Version 12 schema."""
    if not isinstance(frame, pd.DataFrame):
        return empty_user_journal()

    result = frame.copy()
    for col in JOURNAL_COLUMNS:
        if col not in result.columns:
            result[col] = None

    result = result[JOURNAL_COLUMNS].copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce").dt.date.astype("string")
    result["time"] = result["time"].astype("string").fillna("")
    result["ticker"] = result["ticker"].astype("string").str.upper().str.strip()
    result["side"] = result["side"].fillna("Long").astype("string")
    result["setup"] = result["setup"].fillna("First Pullback").astype("string")

    for col in ["entry", "exit", "stop", "shares", "fees", "pnl", "risk_amount", "r_multiple"]:
        result[col] = pd.to_numeric(result[col], errors="coerce")

    result["shares"] = result["shares"].fillna(0).astype(int)
    result["fees"] = result["fees"].fillna(0.0)

    def parse_bool(value):
        if isinstance(value, bool):
            return value
        if pd.isna(value):
            return False
        return str(value).strip().lower() in {"true", "1", "yes", "y", "win"}

    result["win"] = result["win"].map(parse_bool)
    result["followed_plan"] = result["followed_plan"].map(parse_bool)

    missing_ids = result["trade_id"].isna() | result["trade_id"].astype(str).str.strip().eq("")
    if missing_ids.any():
        generated = [
            f"T{datetime.now().strftime('%Y%m%d%H%M%S')}-{idx+1:03d}"
            for idx in range(int(missing_ids.sum()))
        ]
        result.loc[missing_ids, "trade_id"] = generated

    return result.reset_index(drop=True)


def calculate_trade_result(
    side: str,
    entry: float,
    exit_price: float,
    stop: float,
    shares: int,
    fees: float,
) -> dict:
    direction = 1 if side == "Long" else -1
    gross_pnl = (exit_price - entry) * shares * direction
    pnl = gross_pnl - fees
    risk_per_share = abs(entry - stop)
    risk_amount = risk_per_share * shares
    r_multiple = pnl / risk_amount if risk_amount > 0 else 0.0
    return {
        "pnl": round(float(pnl), 2),
        "risk_amount": round(float(risk_amount), 2),
        "r_multiple": round(float(r_multiple), 2),
        "win": bool(pnl > 0),
    }


def user_journal_stats(frame: pd.DataFrame) -> dict:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return {
            "trades": 0, "win_rate": 0.0, "net_pnl": 0.0, "avg_r": 0.0,
            "profit_factor": 0.0, "best_trade": 0.0, "worst_trade": 0.0,
        }

    pnl = pd.to_numeric(frame["pnl"], errors="coerce").fillna(0)
    r_values = pd.to_numeric(frame["r_multiple"], errors="coerce").fillna(0)
    gross_profit = float(pnl[pnl > 0].sum())
    gross_loss = abs(float(pnl[pnl < 0].sum()))
    wins = int((pnl > 0).sum())

    return {
        "trades": int(len(frame)),
        "win_rate": wins / len(frame) * 100 if len(frame) else 0.0,
        "net_pnl": float(pnl.sum()),
        "avg_r": float(r_values.mean()) if len(frame) else 0.0,
        "profit_factor": gross_profit / gross_loss if gross_loss > 0 else gross_profit,
        "best_trade": float(pnl.max()) if len(frame) else 0.0,
        "worst_trade": float(pnl.min()) if len(frame) else 0.0,
    }


def journal_equity_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return pd.DataFrame(columns=["timestamp", "pnl", "equity"])

    result = frame.copy()
    result["timestamp"] = pd.to_datetime(
        result["date"].astype(str) + " " + result["time"].astype(str),
        errors="coerce",
    )
    result["pnl"] = pd.to_numeric(result["pnl"], errors="coerce").fillna(0)
    result = result.sort_values(["timestamp", "trade_id"], na_position="last")
    result["equity"] = result["pnl"].cumsum()
    return result


def journal_display_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return empty_user_journal()

    columns = [
        "date", "time", "ticker", "side", "setup", "entry", "exit", "stop",
        "shares", "pnl", "r_multiple", "execution_grade", "emotion",
        "followed_plan", "mistake", "lesson",
    ]
    return frame[[col for col in columns if col in frame.columns]].copy()



def resample_ohlcv(frame: pd.DataFrame, interval: str) -> pd.DataFrame:
    """Resample minute bars for demo/training charts."""
    if not isinstance(frame, pd.DataFrame) or frame.empty or interval == "1min":
        return frame.copy() if isinstance(frame, pd.DataFrame) else pd.DataFrame()

    rule_map = {"5min": "5min", "15min": "15min", "30min": "30min"}
    rule = rule_map.get(interval)
    if not rule:
        return frame.copy()

    source = frame.copy().sort_values("datetime")
    source["datetime"] = pd.to_datetime(source["datetime"], errors="coerce")
    source = source.dropna(subset=["datetime"]).set_index("datetime")

    aggregations = {
        "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"
    }
    result = source.resample(rule).agg(aggregations).dropna(subset=["open", "high", "low", "close"])

    if result.empty:
        return frame.copy()

    typical = (result["high"] + result["low"] + result["close"]) / 3
    cumulative_volume = result["volume"].cumsum().replace(0, pd.NA)
    result["vwap"] = ((typical * result["volume"]).cumsum() / cumulative_volume).fillna(result["close"])
    result["ema9"] = result["close"].ewm(span=9, adjust=False).mean()
    result["ema20"] = result["close"].ewm(span=20, adjust=False).mean()

    # Carry stable metadata/levels forward.
    for col in [
        "ticker", "day_change_pct", "gap_pct", "float_m", "premarket_volume",
        "relative_volume", "above_vwap", "catalyst", "spider_score", "quality",
        "setup_status", "entry", "stop", "target_1r", "target_2r",
        "premarket_high", "previous_day_high",
    ]:
        if col in source.columns:
            result[col] = source[col].dropna().iloc[-1] if not source[col].dropna().empty else None

    return result.reset_index()


def _five_minute_metrics(group: pd.DataFrame) -> dict:
    g = group.sort_values("datetime").copy()
    volume = pd.to_numeric(g["volume"], errors="coerce").fillna(0)
    five_volume = float(volume.tail(5).sum())

    rolling = volume.rolling(5).sum().dropna()
    baseline = float(rolling.iloc[:-1].mean()) if len(rolling) > 1 else float(rolling.mean() or 0)
    rvol_5m = five_volume / baseline if baseline > 0 else 0.0

    last_close = float(g["close"].iloc[-1])
    earlier_close = float(g["close"].iloc[-6]) if len(g) >= 6 else float(g["open"].iloc[0])
    change_5m = ((last_close / earlier_close) - 1) * 100 if earlier_close else 0.0
    day_high = float(g["high"].max())
    hod_distance = ((day_high - last_close) / last_close) * 100 if last_close else 0.0

    return {
        "alert_time": pd.to_datetime(g["datetime"].iloc[-1]).strftime("%H:%M:%S"),
        "volume": float(volume.sum()),
        "rvol_5m": rvol_5m,
        "change_5m_pct": change_5m,
        "hod_distance_pct": hod_distance,
        "day_change_pct": float(g["day_change_pct"].iloc[-1]) if "day_change_pct" in g else 0.0,
    }


SCANNER_OPTIONS = [
    "Premarket Gap",
    "HOD Momentum",
    "Top Gappers",
    "5-Min Surge",
    "Close to High",
    "Low Float Leaders",
    "News Catalysts",
    "First Pullback Ready",
    "Continuation",
    "Reversal Watch",
    "After-Hours Movers",
]

SCANNER_DESCRIPTIONS = {
    "Premarket Gap": "Morning watchlist builder: positive gaps, meaningful premarket volume, manageable price, and catalyst context.",
    "HOD Momentum": "Stocks closest to the high of day with strong Spider Score and five-minute momentum.",
    "Top Gappers": "Largest gaps ranked with momentum, relative volume, float, and setup quality.",
    "5-Min Surge": "Largest recent five-minute volume and price acceleration.",
    "Close to High": "Stocks pressing near the high of day without being deeply extended.",
    "Low Float Leaders": "Float at or below 20M shares, ranked by score and relative volume.",
    "News Catalysts": "Tickers with a recorded catalyst and strong supporting momentum.",
    "First Pullback Ready": "First Pullback candidates ranked by confirmation, score, and room to resistance.",
    "Continuation": "Strong trend candidates holding VWAP/EMA structure after an initial move.",
    "Reversal Watch": "Weak or extended names that may be stabilizing near VWAP or recent support.",
    "After-Hours Movers": "Late-session movers ranked by price change, volume, and catalyst context.",
}


@st.cache_data(show_spinner=False)
def build_training_scanner_frame(market_frame: pd.DataFrame) -> pd.DataFrame:
    scan = scan_setups(market_frame).copy()
    metrics = []
    for ticker, group in market_frame.groupby("ticker", sort=False):
        row = {"ticker": str(ticker).upper()}
        row.update(_five_minute_metrics(group))
        metrics.append(row)

    metric_frame = pd.DataFrame(metrics)
    result = scan.merge(metric_frame, on="ticker", how="left")
    result["news"] = result["catalyst"].fillna("").astype(str).str.strip().ne("")
    result["news_badge"] = result["news"].map({True: "🔥", False: ""})
    result["symbol_news"] = result["ticker"] + " " + result["news_badge"]
    result["distance_to_hod_pct"] = pd.to_numeric(
        result.get("hod_distance_pct", 0), errors="coerce"
    ).fillna(0)

    result["signal"] = np.select(
        [
            pd.to_numeric(result["spider_score"], errors="coerce").fillna(0) >= 85,
            pd.to_numeric(result["spider_score"], errors="coerce").fillna(0) >= 70,
            pd.to_numeric(result["spider_score"], errors="coerce").fillna(0) >= 55,
        ],
        ["🟢 A+", "🟢 A", "🟡 B"],
        default="🔴 WATCH",
    )
    result["momentum_flag"] = np.select(
        [
            (pd.to_numeric(result["rvol_5m"], errors="coerce").fillna(0) >= 5)
            & (pd.to_numeric(result["change_5m_pct"], errors="coerce").fillna(0) > 0),
            pd.to_numeric(result["relative_volume"], errors="coerce").fillna(0) >= 5,
        ],
        ["⚡", "●"],
        default="",
    )
    result["symbol_news"] = (
        result["ticker"].astype(str)
        + " "
        + result["news_badge"].astype(str)
        + result["momentum_flag"].astype(str)
    ).str.strip()
    result["context_note"] = np.select(
        [
            pd.to_numeric(result["float_m"], errors="coerce").fillna(999) <= 5,
            pd.to_numeric(result["gap_pct"], errors="coerce").fillna(0) >= 20,
            pd.to_numeric(result["relative_volume"], errors="coerce").fillna(0) >= 8,
            result["news"],
        ],
        [
            "Ultra-low float",
            "Big-gap runner profile",
            "High-RVOL runner profile",
            "Fresh catalyst",
        ],
        default="Developing setup",
    )
    result["data_source"] = "Training-derived scanner metrics"
    return result


def scanner_view_frame(scanner_name: str) -> pd.DataFrame:
    frame = build_training_scanner_frame(market).copy()

    if scanner_name == "Premarket Gap":
        frame = frame[
            (pd.to_numeric(frame["gap_pct"], errors="coerce").fillna(0) > 0)
            & (pd.to_numeric(frame["premarket_volume"], errors="coerce").fillna(0) > 0)
        ].sort_values(
            ["gap_pct", "premarket_volume", "relative_volume"],
            ascending=[False, False, False],
        )
    elif scanner_name == "HOD Momentum":
        frame = frame.sort_values(
            ["distance_to_hod_pct", "spider_score", "rvol_5m"],
            ascending=[True, False, False],
        )
    elif scanner_name == "Top Gappers":
        frame = frame.sort_values(
            ["gap_pct", "relative_volume", "spider_score"],
            ascending=[False, False, False],
        )
    elif scanner_name == "5-Min Surge":
        frame = frame.sort_values(
            ["rvol_5m", "change_5m_pct", "spider_score"],
            ascending=[False, False, False],
        )
    elif scanner_name == "Close to High":
        frame = frame[
            pd.to_numeric(frame["distance_to_hod_pct"], errors="coerce").fillna(999) <= 3.0
        ].sort_values(
            ["distance_to_hod_pct", "spider_score", "relative_volume"],
            ascending=[True, False, False],
        )
    elif scanner_name == "Low Float Leaders":
        frame = frame[
            pd.to_numeric(frame["float_m"], errors="coerce").fillna(999) <= 20
        ].sort_values(
            ["spider_score", "relative_volume", "gap_pct"],
            ascending=[False, False, False],
        )
    elif scanner_name == "News Catalysts":
        frame = frame[frame["news"]].sort_values(
            ["spider_score", "relative_volume", "gap_pct"],
            ascending=[False, False, False],
        )
    elif scanner_name == "First Pullback Ready":
        setup_text = frame["setup_status"].fillna("").astype(str).str.lower()
        frame = frame[
            setup_text.str.contains("pullback|confirmed|forming", regex=True)
        ].sort_values(
            ["spider_score", "room_to_resistance_r", "relative_volume"],
            ascending=[False, False, False],
        )
    elif scanner_name == "Continuation":
        frame = frame[
            frame["above_vwap"].fillna(False).astype(bool)
            & (pd.to_numeric(frame["day_change_pct"], errors="coerce").fillna(0) > 0)
        ].sort_values(
            ["spider_score", "change_5m_pct", "relative_volume"],
            ascending=[False, False, False],
        )
    elif scanner_name == "Reversal Watch":
        frame = frame[
            (pd.to_numeric(frame["day_change_pct"], errors="coerce").fillna(0) < 0)
            | (~frame["above_vwap"].fillna(False).astype(bool))
        ].sort_values(
            ["change_5m_pct", "distance_to_hod_pct", "relative_volume"],
            ascending=[False, True, False],
        )
    elif scanner_name == "After-Hours Movers":
        frame = frame.sort_values(
            ["day_change_pct", "volume", "relative_volume"],
            ascending=[False, False, False],
        )

    return frame.reset_index(drop=True)


def scanner_display_frame(frame: pd.DataFrame, compact: bool = False) -> pd.DataFrame:
    columns = [
        "alert_time", "symbol_news", "price", "volume", "premarket_volume", "float_m",
        "relative_volume", "rvol_5m", "gap_pct", "day_change_pct",
        "change_5m_pct", "distance_to_hod_pct", "spider_score", "signal", "context_note", "setup_status",
    ]
    if compact:
        columns = [
            "alert_time", "symbol_news", "price", "float_m",
            "relative_volume", "gap_pct", "spider_score", "signal",
        ]

    display = frame[[col for col in columns if col in frame.columns]].copy()
    rename = {
        "alert_time": "Time",
        "symbol_news": "Symbol / News",
        "price": "Price",
        "volume": "Volume",
        "premarket_volume": "PM Volume",
        "float_m": "Float M",
        "relative_volume": "RVOL Daily",
        "rvol_5m": "RVOL 5m",
        "gap_pct": "Gap %",
        "day_change_pct": "Change %",
        "change_5m_pct": "5m %",
        "distance_to_hod_pct": "From HOD %",
        "spider_score": "Spider Score",
        "signal": "Grade",
        "context_note": "Context",
        "setup_status": "Setup",
    }
    return display.rename(columns=rename)


def style_scanner_table(display: pd.DataFrame):
    def pct_color(value):
        try:
            number = float(value)
        except Exception:
            return ""
        if number >= 20:
            return "background-color:#00d936;color:#001f08;font-weight:900;"
        if number >= 8:
            return "background-color:#63de70;color:#06250b;font-weight:850;"
        if number > 0:
            return "background-color:#b9efb9;color:#09270c;"
        if number <= -10:
            return "background-color:#f75b63;color:#2b0003;font-weight:850;"
        if number < 0:
            return "background-color:#ff9ca1;color:#320408;"
        return ""

    def rvol_color(value):
        try:
            number = float(value)
        except Exception:
            return ""
        if number >= 10:
            return "background-color:#00e6e6;color:#002a2a;font-weight:900;"
        if number >= 5:
            return "background-color:#62f1f1;color:#043030;font-weight:850;"
        if number >= 2:
            return "background-color:#fff0a8;color:#2b2300;"
        return ""

    def float_color(value):
        try:
            number = float(value)
        except Exception:
            return ""
        if number <= 5:
            return "background-color:#00e4ea;color:#00272a;font-weight:900;"
        if number <= 20:
            return "background-color:#83f4d1;color:#062d23;font-weight:850;"
        if number <= 50:
            return "background-color:#f3ffd6;color:#1f2600;"
        return ""

    styler = display.style
    for col in ["Gap %", "Change %", "5m %"]:
        if col in display.columns:
            styler = styler.map(pct_color, subset=[col])
    for col in ["RVOL Daily", "RVOL 5m"]:
        if col in display.columns:
            styler = styler.map(rvol_color, subset=[col])
    if "Float M" in display.columns:
        styler = styler.map(float_color, subset=["Float M"])
    def score_color(value):
        try:
            number = float(value)
        except Exception:
            return ""
        if number >= 85:
            return "background-color:#00d936;color:#001f08;font-weight:950;"
        if number >= 70:
            return "background-color:#65df72;color:#06250b;font-weight:900;"
        if number >= 55:
            return "background-color:#f2dc63;color:#2c2300;font-weight:850;"
        if number >= 40:
            return "background-color:#f2a65a;color:#321600;font-weight:850;"
        return "background-color:#e95f67;color:#2d0004;font-weight:900;"

    if "Spider Score" in display.columns:
        styler = styler.map(score_color, subset=["Spider Score"])

    formats = {
        "Price": "${:.2f}",
        "Volume": "{:,.0f}",
        "PM Volume": "{:,.0f}",
        "Float M": "{:.2f}",
        "RVOL Daily": "{:.2f}",
        "RVOL 5m": "{:.2f}",
        "Gap %": "{:.2f}",
        "Change %": "{:.2f}",
        "5m %": "{:.2f}",
        "From HOD %": "{:.2f}",
        "Spider Score": "{:.0f}",
    }
    active_formats = {col: fmt for col, fmt in formats.items() if col in display.columns}
    return styler.format(active_formats, na_rep="—")


def render_scanner_terminal(
    scanner_name: str,
    *,
    compact: bool = False,
    height: int = 420,
    key: str = "scanner_terminal",
) -> pd.DataFrame:
    frame = scanner_view_frame(scanner_name)
    display = scanner_display_frame(frame, compact=compact)

    try:
        styled = style_scanner_table(display)
        event = st.dataframe(
            styled,
            use_container_width=True,
            hide_index=True,
            height=height,
            on_select="rerun",
            selection_mode="single-row",
            key=key,
        )
    except (ImportError, ModuleNotFoundError, ValueError, TypeError) as exc:
        st.caption(f"Scanner color styling fallback: {type(exc).__name__}. Data remains available.")
        event = st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            height=height,
            on_select="rerun",
            selection_mode="single-row",
            key=f"{key}_plain",
            column_config={
                "Price": st.column_config.NumberColumn(format="$%.2f"),
                "Volume": st.column_config.NumberColumn(format="compact"),
                "Float M": st.column_config.NumberColumn(format="%.2f"),
                "RVOL Daily": st.column_config.NumberColumn(format="%.2f"),
                "RVOL 5m": st.column_config.NumberColumn(format="%.2f"),
                "Gap %": st.column_config.NumberColumn(format="%.2f%%"),
                "Change %": st.column_config.NumberColumn(format="%.2f%%"),
                "5m %": st.column_config.NumberColumn(format="%.2f%%"),
                "From HOD %": st.column_config.NumberColumn(format="%.2f%%"),
                "Spider Score": st.column_config.ProgressColumn(min_value=0, max_value=100),
            },
        )
    selected_rows = event.selection.rows if hasattr(event, "selection") else []
    if selected_rows:
        position = int(selected_rows[0])
        if 0 <= position < len(frame):
            selected_symbol = str(frame.iloc[position]["ticker"])
            set_active_ticker(selected_symbol)
            st.session_state["scanner_last_selected"] = selected_symbol

    return frame


def mini_candlestick_chart(ticker: str, interval: str, height: int, key: str):
    bars, mode, note = get_chart_frame(ticker, interval)
    if bars.empty:
        st.markdown(
            f'<div class="mini-empty">{ticker} · {interval}<br><small>{note}</small></div>',
            unsafe_allow_html=True,
        )
        return

    bars = bars.sort_values("datetime").copy()
    fig = go.Figure(
        go.Candlestick(
            x=bars["datetime"],
            open=bars["open"],
            high=bars["high"],
            low=bars["low"],
            close=bars["close"],
            name=ticker,
        )
    )
    if "vwap" in bars:
        fig.add_trace(go.Scatter(x=bars["datetime"], y=bars["vwap"], mode="lines", name="VWAP"))
    if "ema9" in bars:
        fig.add_trace(go.Scatter(x=bars["datetime"], y=bars["ema9"], mode="lines", name="EMA 9"))

    fig.update_layout(
        height=height,
        margin=dict(l=4, r=4, t=24, b=4),
        xaxis_rangeslider_visible=False,
        showlegend=False,
        title=dict(text=f"{ticker} · {interval} · {mode}", font=dict(size=12)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(7,17,31,.72)",
    )
    st.plotly_chart(fig, use_container_width=True, key=key, config={"displaylogo": False})


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
        demo = resample_ohlcv(demo, interval)
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
  <div style="font-size:.78rem;color:#ffffff;margin-top:.2rem;">Pro Scanner + Journal v12.0</div>
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
st.sidebar.info("Use the top-left arrow to collapse or restore the navigation sidebar.")

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
    layout_mode = st.session_state.get("layout_mode", "Desk")
    payload = get_market_payload(active, "5min")
    ai = spider_ai_summary(payload)
    quote = payload.get("quote", {}) or {}
    profile = payload.get("profile", {}) or {}
    session = market_session_label()

    st.markdown(
        """
        <div class="workspace-title">
          <div class="workspace-kicker">SPIDERBOYS TRADING PRO</div>
          <div class="workspace-heading">Scanner Command Center</div>
          <div class="workspace-subtitle">Scanner-first momentum workstation</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Market", session)
    m2.metric("Active", active)
    m3.metric(
        "Last",
        f'${float(quote.get("price")):.2f}' if quote.get("price") else "—",
        f'{float(quote.get("change_pct", 0)):+.2f}%' if quote else None,
    )
    m4.metric("Spider Score", f'{ai["score"]}/100')
    m5.metric("Grade", ai["grade"])
    m6.metric("Chart Data", payload["chart_mode"])

    tool_a, tool_b, tool_c, tool_d = st.columns([1.35, 2.2, 2.0, 1.35])
    with tool_a:
        if st.session_state["scanner_panel_open"]:
            if st.button("◀ Collapse Scanner", use_container_width=True, key="v11_hide_scanner"):
                st.session_state["scanner_panel_open"] = False
                st.rerun()
        else:
            if st.button("▶ Restore Scanner", type="primary", use_container_width=True, key="v11_show_scanner"):
                st.session_state["scanner_panel_open"] = True
                st.rerun()

    with tool_b:
        scanner_name = st.selectbox(
            "Scanner",
            SCANNER_OPTIONS,
            index=SCANNER_OPTIONS.index(
                st.session_state.get("scanner_view", "HOD Momentum")
                if st.session_state.get("scanner_view", "HOD Momentum") in SCANNER_OPTIONS
                else "HOD Momentum"
            ),
            label_visibility="collapsed",
            key="command_scanner_select",
        )
        st.session_state["scanner_view"] = scanner_name

    with tool_c:
        timeframe = st.segmented_control(
            "Primary timeframe",
            ["1min", "5min", "15min", "30min"],
            default="5min",
            label_visibility="collapsed",
            key="v12_primary_timeframe",
        )

    with tool_d:
        if st.session_state["right_panel_open"]:
            if st.button("Collapse Intel ▶", use_container_width=True, key="v12_hide_intel"):
                st.session_state["right_panel_open"] = False
                st.rerun()
        else:
            if st.button("Restore Intel ◀", type="primary", use_container_width=True, key="v12_show_intel"):
                st.session_state["right_panel_open"] = True
                st.rerun()

    scanner_open = st.session_state["scanner_panel_open"]
    intel_open = st.session_state["right_panel_open"]

    if layout_mode == "Compact":
        st.markdown('<div class="terminal-panel-title">MOMENTUM SCANNER</div>', unsafe_allow_html=True)
        render_scanner_terminal(
            scanner_name,
            compact=True,
            height=320,
            key=f"compact_scanner_{scanner_name}",
        )
        selected = st.session_state.get("scanner_last_selected")
        if selected and selected != active:
            set_active_ticker(selected)
            st.rerun()

        st.markdown(f'<div class="terminal-panel-title">{active} PRIMARY CHART</div>', unsafe_allow_html=True)
        candlestick_chart(active, 520, interval=timeframe)

        compact_left, compact_right = st.columns(2)
        with compact_left:
            mini_candlestick_chart(active, "1min", 280, "compact_1m")
        with compact_right:
            mini_candlestick_chart(active, "15min", 280, "compact_15m")

    else:
        if scanner_open and intel_open:
            scanner_col, chart_col, intel_col = st.columns([1.38, 2.35, 1.15], gap="small")
        elif scanner_open:
            scanner_col, chart_col = st.columns([1.4, 3.6], gap="small")
            intel_col = None
        elif intel_open:
            chart_col, intel_col = st.columns([3.7, 1.25], gap="small")
            scanner_col = None
        else:
            chart_col = st.container()
            scanner_col = intel_col = None

        if scanner_col is not None:
            with scanner_col:
                st.markdown(
                    f'<div class="terminal-panel-title">{scanner_name.upper()}</div>',
                    unsafe_allow_html=True,
                )
                st.caption("Colored cells are training-derived momentum metrics; quote/news panels use live providers when available.")
                render_scanner_terminal(
                    scanner_name,
                    compact=True,
                    height=555,
                    key=f"desk_scanner_{scanner_name}",
                )
                selected = st.session_state.get("scanner_last_selected")
                if selected and selected != active:
                    set_active_ticker(selected)
                    st.rerun()

        with chart_col:
            st.markdown(
                f'<div class="terminal-panel-title">{active} · SYNCHRONIZED CHARTS</div>',
                unsafe_allow_html=True,
            )
            main_chart, mini_chart = st.columns([1.45, 1])
            with main_chart:
                candlestick_chart(active, 555, interval=timeframe)
            with mini_chart:
                mini_candlestick_chart(active, "1min", 268, "desk_1m")
                mini_candlestick_chart(active, "15min", 268, "desk_15m")

        if intel_col is not None:
            with intel_col:
                st.markdown('<div class="terminal-panel-title">STOCK INTELLIGENCE</div>', unsafe_allow_html=True)
                company_name = profile.get("name") or active
                industry = profile.get("industry") or "—"
                shares = profile.get("shares_outstanding_m")
                market_cap = profile.get("market_cap_m") or profile.get("market_cap")

                st.markdown(
                    f"""
                    <div class="stock-card">
                      <div class="stock-symbol">{active}</div>
                      <div class="stock-name">{company_name}</div>
                      <div class="stock-change">{float(quote.get("change_pct", 0)):+.2f}%</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                i1, i2 = st.columns(2)
                i1.metric("Last", f'${float(quote.get("price")):.2f}' if quote.get("price") else "—")
                i2.metric("Day High", f'${float(quote.get("high")):.2f}' if quote.get("high") else "—")
                st.write(f"**Industry:** {industry}")
                st.write(f"**Shares Out:** {float(shares):,.2f}M" if shares else "**Shares Out:** —")
                if market_cap:
                    cap = float(market_cap)
                    cap_text = f"${cap:,.2f}M" if cap < 10_000_000 else f"${cap/1_000_000_000:,.2f}B"
                    st.write(f"**Market Cap:** {cap_text}")
                else:
                    st.write("**Market Cap:** —")

                st.markdown('<div class="terminal-panel-title">SPIDER AI</div>', unsafe_allow_html=True)
                st.markdown(
                    f"""
                    <div class="sb-card ai-panel">
                      <div class="sb-ai-score">{ai["score"]}/100</div>
                      <div class="grade-row"><span>{ai["grade"]}</span><span>{ai["confidence"]}</span></div>
                      <div class="level-grid one-col">
                        <div><small>Trend</small><b>{ai["trend"]}</b></div>
                        <div><small>Entry</small><b>{"$"+format(ai["entry"], ".2f") if ai["entry"] else "—"}</b></div>
                        <div><small>Stop</small><b>{"$"+format(ai["stop"], ".2f") if ai["stop"] else "—"}</b></div>
                        <div><small>2R Target</small><b>{"$"+format(ai["target_2r"], ".2f") if ai["target_2r"] else "—"}</b></div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                for reason in ai["reasons"][:5]:
                    st.write(f"✓ {reason}")

                st.markdown('<div class="terminal-panel-title">LATEST NEWS</div>', unsafe_allow_html=True)
                news_view = compact_news_view(payload.get("news"), 3)
                if news_view.empty:
                    st.caption("No recent company news returned.")
                else:
                    for _, item in news_view.iterrows():
                        st.markdown(f"🔥 **{item.get('headline', '')}**")
                        st.caption(str(item.get("source", "")))

    st.markdown('<div class="dock-divider"></div>', unsafe_allow_html=True)
    dock_scanner, dock_plan, dock_news, dock_journal, dock_stats, dock_diag = st.tabs(
        ["Scanners", "Trade Card", "News", "Journal", "Performance", "Diagnostics"]
    )

    with dock_scanner:
        sub1, sub2 = st.columns(2)
        with sub1:
            st.markdown('<div class="terminal-panel-title">TOP GAPPERS</div>', unsafe_allow_html=True)
            render_scanner_terminal("Top Gappers", compact=True, height=330, key="dock_gappers")
        with sub2:
            st.markdown('<div class="terminal-panel-title">VOLUME SURGE</div>', unsafe_allow_html=True)
            render_scanner_terminal("5-Min Surge", compact=True, height=330, key="dock_volume")

    with dock_plan:
        plan1, plan2, plan3, plan4, plan5 = st.columns(5)
        plan1.metric("Entry", "$"+format(ai["entry"], ".2f") if ai["entry"] else "—")
        plan2.metric("Stop", "$"+format(ai["stop"], ".2f") if ai["stop"] else "—")
        plan3.metric("1R", "$"+format(ai["entry"] + (ai["entry"]-ai["stop"]), ".2f") if ai["entry"] and ai["stop"] else "—")
        plan4.metric("2R", "$"+format(ai["target_2r"], ".2f") if ai["target_2r"] else "—")
        plan5.metric("Grade", ai["grade"])
        st.caption("Open Trade Plan for account risk and exact share sizing.")

    with dock_news:
        news_view = compact_news_view(payload.get("news"), 12)
        if news_view.empty:
            st.info("No recent company news returned.")
        else:
            st.dataframe(
                news_view,
                use_container_width=True,
                hide_index=True,
                column_config={"url": st.column_config.LinkColumn("Article")},
            )

    with dock_journal:
        st.dataframe(journal.tail(10), use_container_width=True, hide_index=True)

    with dock_stats:
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Trades", len(journal))
        s2.metric("Win Rate", f"{journal['win'].mean()*100:.1f}%" if len(journal) else "—")
        s3.metric("Average R", f"{journal['r_multiple'].mean():.2f}R" if len(journal) else "—")
        s4.metric("Net P/L", f"${journal['pnl'].sum():,.2f}" if len(journal) else "—")

    with dock_diag:
        st.write(f"FMP key: {'Detected' if FMP_KEY else 'Missing'}")
        st.write(f"Finnhub key: {'Detected' if FINNHUB_KEY else 'Missing'}")
        st.write(f"Chart mode: {payload['chart_mode']}")
        st.write("Scanner derived metrics: Training dataset")
        for error in payload["errors"]:
            st.caption(error)

    st.subheader("Scanner Watchlist")
    watch_text = st.text_input(
        "Tickers separated by commas",
        value=", ".join(st.session_state["saved_watchlist"]),
        key="watchlist_editor_v11",
    )
    if st.button("Save Scanner Watchlist", type="primary"):
        parsed = [normalize_symbol(x) for x in watch_text.split(",")]
        st.session_state["saved_watchlist"] = list(dict.fromkeys([x for x in parsed if x]))[:20]
        st.success("Scanner watchlist saved for this session.")

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
    st.title("Daily Trading Journal")
    st.caption("Log each trade in under a minute, review the day, and export a clean permanent record.")

    user_journal = normalize_user_journal(st.session_state["user_trade_journal"])
    st.session_state["user_trade_journal"] = user_journal

    today_string = date.today().isoformat()
    today_frame = user_journal[user_journal["date"].astype(str) == today_string].copy()
    today_stats = user_journal_stats(today_frame)
    all_stats = user_journal_stats(user_journal)

    j1, j2, j3, j4, j5, j6 = st.columns(6)
    j1.metric("Today's Trades", today_stats["trades"])
    j2.metric("Today's P/L", f'${today_stats["net_pnl"]:,.2f}')
    j3.metric("Today's Win Rate", f'{today_stats["win_rate"]:.1f}%')
    j4.metric("All Trades", all_stats["trades"])
    j5.metric("Average R", f'{all_stats["avg_r"]:.2f}R')
    j6.metric("Profit Factor", f'{all_stats["profit_factor"]:.2f}')

    add_tab, daily_tab, review_tab, data_tab = st.tabs(
        ["＋ Add Trade", "Daily Log", "Review & Analytics", "Import / Export"]
    )

    with add_tab:
        st.markdown('<div class="journal-section-title">NEW TRADE</div>', unsafe_allow_html=True)
        default_ticker = normalize_symbol(
            st.session_state.get("journal_prefill_ticker")
            or st.session_state.get("active_ticker")
            or "SPY"
        )

        with st.form("daily_trade_entry_form", clear_on_submit=False):
            row1 = st.columns([1.2, 1, 1, 1.4, 1.4])
            with row1[0]:
                trade_date = st.date_input("Date", value=date.today())
            with row1[1]:
                trade_time = st.time_input("Time", value=datetime.now().time().replace(second=0, microsecond=0))
            with row1[2]:
                ticker_value = st.text_input("Ticker", value=default_ticker).upper().strip()
            with row1[3]:
                side = st.selectbox("Side", ["Long", "Short"])
            with row1[4]:
                setup = st.selectbox(
                    "Setup",
                    [
                        "First Pullback",
                        "HOD Break",
                        "VWAP Reclaim",
                        "Premarket High Break",
                        "Opening Range Break",
                        "Red-to-Green",
                        "News Momentum",
                        "Other",
                    ],
                )

            row2 = st.columns(6)
            with row2[0]:
                entry = st.number_input("Entry", min_value=0.0, value=0.0, step=0.01, format="%.4f")
            with row2[1]:
                exit_price = st.number_input("Exit", min_value=0.0, value=0.0, step=0.01, format="%.4f")
            with row2[2]:
                stop = st.number_input("Stop", min_value=0.0, value=0.0, step=0.01, format="%.4f")
            with row2[3]:
                shares = st.number_input("Shares", min_value=0, value=0, step=10)
            with row2[4]:
                fees = st.number_input("Fees", min_value=0.0, value=0.0, step=0.10, format="%.2f")
            with row2[5]:
                execution_grade = st.selectbox("Execution Grade", ["A+", "A", "B", "C", "D"])

            row3 = st.columns([1.2, 1.2, 1, 1.6])
            with row3[0]:
                emotion = st.selectbox(
                    "Emotion",
                    ["Calm", "Confident", "Focused", "Hesitant", "FOMO", "Frustrated", "Tired"],
                )
            with row3[1]:
                followed_plan = st.checkbox("Followed my plan", value=True)
            with row3[2]:
                catalyst = st.text_input("Catalyst", placeholder="Earnings, contract, FDA...")
            with row3[3]:
                mistake = st.text_input("Mistake", placeholder="None, chased, early entry...")

            lesson = st.text_area(
                "Lesson",
                placeholder="What should I repeat or change on the next trade?",
                height=85,
            )
            notes = st.text_area(
                "Trade Notes",
                placeholder="Entry trigger, tape behavior, partial exits, market context...",
                height=100,
            )

            submitted = st.form_submit_button("Save Trade", type="primary", use_container_width=True)

        if submitted:
            errors = []
            if not ticker_value:
                errors.append("Enter a ticker.")
            if entry <= 0 or exit_price <= 0 or stop <= 0:
                errors.append("Entry, exit, and stop must be greater than zero.")
            if shares <= 0:
                errors.append("Shares must be greater than zero.")
            if side == "Long" and stop >= entry:
                errors.append("For a long trade, the stop should be below the entry.")
            if side == "Short" and stop <= entry:
                errors.append("For a short trade, the stop should be above the entry.")

            if errors:
                for error in errors:
                    st.error(error)
            else:
                calculations = calculate_trade_result(
                    side, float(entry), float(exit_price), float(stop), int(shares), float(fees)
                )
                new_trade = {
                    "trade_id": f"T{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                    "date": trade_date.isoformat(),
                    "time": trade_time.strftime("%H:%M"),
                    "ticker": normalize_symbol(ticker_value),
                    "side": side,
                    "setup": setup,
                    "entry": float(entry),
                    "exit": float(exit_price),
                    "stop": float(stop),
                    "shares": int(shares),
                    "fees": float(fees),
                    "pnl": calculations["pnl"],
                    "risk_amount": calculations["risk_amount"],
                    "r_multiple": calculations["r_multiple"],
                    "win": calculations["win"],
                    "execution_grade": execution_grade,
                    "emotion": emotion,
                    "followed_plan": bool(followed_plan),
                    "catalyst": catalyst.strip(),
                    "mistake": mistake.strip() or "None",
                    "lesson": lesson.strip(),
                    "notes": notes.strip(),
                }
                updated = pd.concat(
                    [st.session_state["user_trade_journal"], pd.DataFrame([new_trade])],
                    ignore_index=True,
                )
                st.session_state["user_trade_journal"] = normalize_user_journal(updated)
                st.session_state["journal_prefill_ticker"] = normalize_symbol(ticker_value)
                st.success(
                    f'Saved {new_trade["ticker"]}: '
                    f'${calculations["pnl"]:,.2f} · {calculations["r_multiple"]:.2f}R'
                )
                st.rerun()

        st.markdown('<div class="journal-section-title">QUICK CALCULATOR</div>', unsafe_allow_html=True)
        qc1, qc2, qc3, qc4 = st.columns(4)
        qc1.metric("Gross Move", f"${abs(exit_price-entry):.4f}" if entry and exit_price else "—")
        qc2.metric("Risk / Share", f"${abs(entry-stop):.4f}" if entry and stop else "—")
        preview = (
            calculate_trade_result(side, entry, exit_price, stop, int(shares), fees)
            if entry > 0 and exit_price > 0 and stop > 0 and shares > 0
            else None
        )
        qc3.metric("Estimated P/L", f'${preview["pnl"]:,.2f}' if preview else "—")
        qc4.metric("Estimated R", f'{preview["r_multiple"]:.2f}R' if preview else "—")

    with daily_tab:
        selected_day = st.date_input("Journal Date", value=date.today(), key="journal_daily_date")
        day_string = selected_day.isoformat()
        day_frame = st.session_state["user_trade_journal"][
            st.session_state["user_trade_journal"]["date"].astype(str) == day_string
        ].copy()
        day_stats = user_journal_stats(day_frame)

        d1, d2, d3, d4, d5 = st.columns(5)
        d1.metric("Trades", day_stats["trades"])
        d2.metric("Net P/L", f'${day_stats["net_pnl"]:,.2f}')
        d3.metric("Win Rate", f'{day_stats["win_rate"]:.1f}%')
        d4.metric("Average R", f'{day_stats["avg_r"]:.2f}R')
        d5.metric("Best Trade", f'${day_stats["best_trade"]:,.2f}')

        if day_frame.empty:
            st.info("No trades are logged for this date.")
        else:
            editable_columns = [
                "trade_id", "date", "time", "ticker", "side", "setup", "entry", "exit",
                "stop", "shares", "fees", "execution_grade", "emotion", "followed_plan",
                "catalyst", "mistake", "lesson", "notes",
            ]
            edited_day = st.data_editor(
                day_frame[editable_columns],
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                disabled=["trade_id", "date"],
                key=f"daily_editor_{day_string}",
                column_config={
                    "entry": st.column_config.NumberColumn(format="$%.4f"),
                    "exit": st.column_config.NumberColumn(format="$%.4f"),
                    "stop": st.column_config.NumberColumn(format="$%.4f"),
                    "fees": st.column_config.NumberColumn(format="$%.2f"),
                    "followed_plan": st.column_config.CheckboxColumn("Plan Followed"),
                },
            )
            if st.button("Save Edited Daily Log", type="primary"):
                recalculated_rows = []
                for _, row in edited_day.iterrows():
                    calculations = calculate_trade_result(
                        str(row["side"]),
                        float(row["entry"]),
                        float(row["exit"]),
                        float(row["stop"]),
                        int(row["shares"]),
                        float(row["fees"] or 0),
                    )
                    record = row.to_dict()
                    record.update(calculations)
                    recalculated_rows.append(record)

                other_days = st.session_state["user_trade_journal"][
                    st.session_state["user_trade_journal"]["date"].astype(str) != day_string
                ].copy()
                st.session_state["user_trade_journal"] = normalize_user_journal(
                    pd.concat([other_days, pd.DataFrame(recalculated_rows)], ignore_index=True)
                )
                st.success("Daily log updated and P/L recalculated.")
                st.rerun()

            delete_options = day_frame["trade_id"].astype(str).tolist()
            delete_id = st.selectbox(
                "Delete a trade",
                delete_options,
                format_func=lambda value: (
                    f'{value} · '
                    f'{day_frame.loc[day_frame["trade_id"].astype(str)==value, "ticker"].iloc[0]} · '
                    f'${float(day_frame.loc[day_frame["trade_id"].astype(str)==value, "pnl"].iloc[0]):,.2f}'
                ),
            )
            if st.button("Delete Selected Trade"):
                st.session_state["user_trade_journal"] = st.session_state["user_trade_journal"][
                    st.session_state["user_trade_journal"]["trade_id"].astype(str) != str(delete_id)
                ].reset_index(drop=True)
                st.warning("Trade deleted.")
                st.rerun()

        st.markdown('<div class="journal-section-title">DAILY REVIEW</div>', unsafe_allow_html=True)
        existing_daily_note = st.session_state["daily_journal_notes"].get(day_string, {})
        with st.form(f"daily_review_form_{day_string}"):
            nr1, nr2 = st.columns(2)
            with nr1:
                daily_focus = st.text_input(
                    "Trading Focus",
                    value=existing_daily_note.get("focus", ""),
                    placeholder="Wait for confirmation; only A setups...",
                )
            with nr2:
                daily_loss_limit = st.number_input(
                    "Daily Loss Limit",
                    min_value=0.0,
                    value=float(existing_daily_note.get("loss_limit", 0.0) or 0.0),
                    step=25.0,
                )
            best_decision = st.text_area(
                "Best Decision",
                value=existing_daily_note.get("best_decision", ""),
                height=75,
            )
            biggest_mistake = st.text_area(
                "Biggest Mistake",
                value=existing_daily_note.get("biggest_mistake", ""),
                height=75,
            )
            tomorrow_focus = st.text_area(
                "Next-Session Focus",
                value=existing_daily_note.get("tomorrow_focus", ""),
                height=75,
            )
            save_daily_review = st.form_submit_button("Save Daily Review", use_container_width=True)

        if save_daily_review:
            st.session_state["daily_journal_notes"][day_string] = {
                "focus": daily_focus.strip(),
                "loss_limit": float(daily_loss_limit),
                "best_decision": best_decision.strip(),
                "biggest_mistake": biggest_mistake.strip(),
                "tomorrow_focus": tomorrow_focus.strip(),
            }
            st.success("Daily review saved for this session.")

    with review_tab:
        if user_journal.empty:
            st.info("Add or import trades to unlock analytics.")
        else:
            filter1, filter2, filter3 = st.columns(3)
            dates = pd.to_datetime(user_journal["date"], errors="coerce")
            min_date = dates.min().date() if dates.notna().any() else date.today()
            max_date = dates.max().date() if dates.notna().any() else date.today()

            with filter1:
                review_range = st.date_input(
                    "Date Range",
                    value=(min_date, max_date),
                    key="journal_review_range",
                )
            with filter2:
                ticker_options = ["All"] + sorted(user_journal["ticker"].dropna().astype(str).unique().tolist())
                ticker_filter = st.selectbox("Ticker", ticker_options)
            with filter3:
                setup_options = ["All"] + sorted(user_journal["setup"].dropna().astype(str).unique().tolist())
                setup_filter = st.selectbox("Setup", setup_options)

            filtered = user_journal.copy()
            filtered_dates = pd.to_datetime(filtered["date"], errors="coerce").dt.date
            if isinstance(review_range, (tuple, list)) and len(review_range) == 2:
                start_date, end_date = review_range
                filtered = filtered[(filtered_dates >= start_date) & (filtered_dates <= end_date)]
            elif isinstance(review_range, date):
                filtered = filtered[filtered_dates == review_range]
            if ticker_filter != "All":
                filtered = filtered[filtered["ticker"].astype(str) == ticker_filter]
            if setup_filter != "All":
                filtered = filtered[filtered["setup"].astype(str) == setup_filter]

            stats = user_journal_stats(filtered)
            r1, r2, r3, r4, r5, r6 = st.columns(6)
            r1.metric("Trades", stats["trades"])
            r2.metric("Win Rate", f'{stats["win_rate"]:.1f}%')
            r3.metric("Net P/L", f'${stats["net_pnl"]:,.2f}')
            r4.metric("Average R", f'{stats["avg_r"]:.2f}R')
            r5.metric("Profit Factor", f'{stats["profit_factor"]:.2f}')
            r6.metric("Worst Trade", f'${stats["worst_trade"]:,.2f}')

            equity = journal_equity_frame(filtered)
            if not equity.empty:
                equity_fig = go.Figure()
                equity_fig.add_trace(
                    go.Scatter(
                        x=equity["timestamp"],
                        y=equity["equity"],
                        mode="lines+markers",
                        name="Cumulative P/L",
                    )
                )
                equity_fig.update_layout(
                    height=360,
                    margin=dict(l=8, r=8, t=30, b=8),
                    title="Equity Curve",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(8,18,32,.55)",
                )
                st.plotly_chart(equity_fig, use_container_width=True, config={"displaylogo": False})

            chart_left, chart_right = st.columns(2)
            with chart_left:
                setup_pnl = (
                    filtered.assign(pnl=pd.to_numeric(filtered["pnl"], errors="coerce").fillna(0))
                    .groupby("setup", as_index=False)["pnl"].sum()
                    .sort_values("pnl", ascending=False)
                )
                setup_fig = go.Figure(go.Bar(x=setup_pnl["setup"], y=setup_pnl["pnl"]))
                setup_fig.update_layout(
                    height=330,
                    title="P/L by Setup",
                    margin=dict(l=8, r=8, t=35, b=8),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(8,18,32,.55)",
                )
                st.plotly_chart(setup_fig, use_container_width=True, config={"displaylogo": False})

            with chart_right:
                daily_pnl = filtered.copy()
                daily_pnl["pnl"] = pd.to_numeric(daily_pnl["pnl"], errors="coerce").fillna(0)
                daily_pnl = daily_pnl.groupby("date", as_index=False)["pnl"].sum()
                daily_fig = go.Figure(go.Bar(x=daily_pnl["date"], y=daily_pnl["pnl"]))
                daily_fig.update_layout(
                    height=330,
                    title="Daily P/L",
                    margin=dict(l=8, r=8, t=35, b=8),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(8,18,32,.55)",
                )
                st.plotly_chart(daily_fig, use_container_width=True, config={"displaylogo": False})

            st.markdown('<div class="journal-section-title">P/L CALENDAR</div>', unsafe_allow_html=True)
            calendar_source = filtered.copy()
            calendar_source["date_dt"] = pd.to_datetime(calendar_source["date"], errors="coerce")
            calendar_source["pnl"] = pd.to_numeric(calendar_source["pnl"], errors="coerce").fillna(0)
            calendar_daily = (
                calendar_source.dropna(subset=["date_dt"])
                .groupby("date_dt", as_index=False)["pnl"].sum()
            )
            if not calendar_daily.empty:
                first_day = calendar_daily["date_dt"].min().normalize()
                calendar_daily["week"] = (
                    (calendar_daily["date_dt"] - first_day).dt.days // 7
                )
                calendar_daily["weekday"] = calendar_daily["date_dt"].dt.weekday
                calendar_daily["label"] = calendar_daily.apply(
                    lambda row: f'{row["date_dt"].strftime("%b %d")}<br>${row["pnl"]:,.2f}',
                    axis=1,
                )
                pivot = calendar_daily.pivot_table(
                    index="weekday", columns="week", values="pnl", aggfunc="sum"
                ).reindex(range(7))
                text_pivot = calendar_daily.pivot_table(
                    index="weekday", columns="week", values="label", aggfunc="first"
                ).reindex(range(7))

                calendar_fig = go.Figure(
                    go.Heatmap(
                        z=pivot.values,
                        x=[f"Week {int(col)+1}" for col in pivot.columns],
                        y=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                        text=text_pivot.values,
                        hovertemplate="%{text}<extra></extra>",
                        colorscale=[
                            [0.0, "#8b1e2d"],
                            [0.49, "#321d27"],
                            [0.50, "#14243a"],
                            [0.51, "#173c36"],
                            [1.0, "#19a65a"],
                        ],
                        zmid=0,
                        showscale=False,
                        xgap=4,
                        ygap=4,
                    )
                )
                calendar_fig.update_layout(
                    height=300,
                    margin=dict(l=8, r=8, t=20, b=8),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    yaxis_autorange="reversed",
                )
                st.plotly_chart(
                    calendar_fig,
                    use_container_width=True,
                    config={"displaylogo": False},
                )

            st.markdown('<div class="journal-section-title">TRADE REVIEW</div>', unsafe_allow_html=True)
            if not filtered.empty:
                review_ids = filtered["trade_id"].astype(str).tolist()
                review_id = st.selectbox("Select Trade", review_ids)
                trade = filtered[filtered["trade_id"].astype(str) == review_id].iloc[0]
                rv1, rv2, rv3, rv4 = st.columns(4)
                rv1.metric("Ticker", trade["ticker"])
                rv2.metric("P/L", f'${float(trade["pnl"]):,.2f}')
                rv3.metric("Result", f'{float(trade["r_multiple"]):.2f}R')
                rv4.metric("Grade", trade["execution_grade"])
                st.write(f'**Setup:** {trade["setup"]} · **Side:** {trade["side"]}')
                st.write(f'**Emotion:** {trade["emotion"]} · **Plan Followed:** {"Yes" if trade["followed_plan"] else "No"}')
                st.write(f'**Catalyst:** {trade["catalyst"] or "—"}')
                st.write(f'**Mistake:** {trade["mistake"] or "None"}')
                st.write(f'**Lesson:** {trade["lesson"] or "—"}')
                st.write(f'**Notes:** {trade["notes"] or "—"}')

    with data_tab:
        st.markdown('<div class="journal-section-title">IMPORT</div>', unsafe_allow_html=True)
        upload = st.file_uploader("Import Journal CSV", type=["csv"])
        import_mode = st.radio("Import Mode", ["Append", "Replace"], horizontal=True)
        if upload is not None:
            try:
                imported = normalize_user_journal(pd.read_csv(upload))
                st.dataframe(imported.head(20), use_container_width=True, hide_index=True)
                if st.button("Apply Import", type="primary"):
                    if import_mode == "Replace":
                        st.session_state["user_trade_journal"] = imported
                    else:
                        st.session_state["user_trade_journal"] = normalize_user_journal(
                            pd.concat(
                                [st.session_state["user_trade_journal"], imported],
                                ignore_index=True,
                            ).drop_duplicates(subset=["trade_id"], keep="last")
                        )
                    st.success(f"Imported {len(imported)} trades.")
                    st.rerun()
            except Exception as exc:
                st.error(f"Could not import that CSV: {exc}")

        st.markdown('<div class="journal-section-title">EXPORT</div>', unsafe_allow_html=True)
        export1, export2, export3 = st.columns(3)
        with export1:
            st.download_button(
                "Download Full Journal",
                st.session_state["user_trade_journal"].to_csv(index=False),
                f"spiderboys_trading_journal_{date.today().isoformat()}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with export2:
            current_today = st.session_state["user_trade_journal"][
                st.session_state["user_trade_journal"]["date"].astype(str) == date.today().isoformat()
            ]
            st.download_button(
                "Download Today's Trades",
                current_today.to_csv(index=False),
                f"spiderboys_trades_{date.today().isoformat()}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with export3:
            st.download_button(
                "Download Blank Template",
                empty_user_journal().to_csv(index=False),
                "spiderboys_journal_template.csv",
                mime="text/csv",
                use_container_width=True,
            )

        st.download_button(
            "Download Daily Review Notes",
            json.dumps(st.session_state["daily_journal_notes"], indent=2),
            f"spiderboys_daily_reviews_{date.today().isoformat()}.json",
            mime="application/json",
        )

        st.info(
            "Your journal is stored in this active Streamlit session. Download the CSV regularly "
            "for a permanent backup. Database persistence can be connected as the next production step."
        )

        with st.expander("Demo and reset tools"):
            if st.button("Load Demo Trades Into My Journal"):
                converted = pd.DataFrame({
                    "trade_id": [f"DEMO-{idx+1:03d}" for idx in range(len(journal))],
                    "date": journal["date"],
                    "time": "09:45",
                    "ticker": journal["ticker"],
                    "side": "Long",
                    "setup": journal["setup"],
                    "entry": journal["entry"],
                    "exit": journal["exit"],
                    "stop": journal["stop"],
                    "shares": journal["shares"],
                    "fees": 0.0,
                    "pnl": journal["pnl"],
                    "risk_amount": (journal["entry"] - journal["stop"]).abs() * journal["shares"],
                    "r_multiple": journal["r_multiple"],
                    "win": journal["win"],
                    "execution_grade": journal["execution_grade"],
                    "emotion": journal["emotion"],
                    "followed_plan": journal["execution_grade"].isin(["A+", "A", "B"]),
                    "catalyst": "",
                    "mistake": journal["mistake"].fillna("None"),
                    "lesson": journal["lesson"].fillna(""),
                    "notes": "Imported demo trade",
                })
                st.session_state["user_trade_journal"] = normalize_user_journal(converted)
                st.success("Demo trades loaded.")
                st.rerun()

            confirm_clear = st.checkbox("I understand this clears the active session journal.")
            if st.button("Clear Active Journal", disabled=not confirm_clear):
                st.session_state["user_trade_journal"] = empty_user_journal()
                st.warning("Active journal cleared.")
                st.rerun()

elif page == "Performance Analytics":
    st.title("Performance Center")

    performance_source = normalize_user_journal(st.session_state["user_trade_journal"])
    using_demo = performance_source.empty

    if using_demo:
        st.info("Your personal journal is empty, so this page is showing demo analytics.")
        converted_demo = pd.DataFrame({
            "trade_id": [f"DEMO-{idx+1:03d}" for idx in range(len(journal))],
            "date": journal["date"],
            "time": "09:45",
            "ticker": journal["ticker"],
            "side": "Long",
            "setup": journal["setup"],
            "entry": journal["entry"],
            "exit": journal["exit"],
            "stop": journal["stop"],
            "shares": journal["shares"],
            "fees": 0.0,
            "pnl": journal["pnl"],
            "risk_amount": (journal["entry"] - journal["stop"]).abs() * journal["shares"],
            "r_multiple": journal["r_multiple"],
            "win": journal["win"],
            "execution_grade": journal["execution_grade"],
            "emotion": journal["emotion"],
            "followed_plan": journal["execution_grade"].isin(["A+", "A", "B"]),
            "catalyst": "",
            "mistake": journal["mistake"].fillna("None"),
            "lesson": journal["lesson"].fillna(""),
            "notes": "Demo trade",
        })
        performance_source = normalize_user_journal(converted_demo)
    else:
        st.success("Analytics are calculated from your active personal journal.")

    stats = user_journal_stats(performance_source)
    p1, p2, p3, p4, p5, p6 = st.columns(6)
    p1.metric("Trades", stats["trades"])
    p2.metric("Win Rate", f'{stats["win_rate"]:.1f}%')
    p3.metric("Net P/L", f'${stats["net_pnl"]:,.2f}')
    p4.metric("Average R", f'{stats["avg_r"]:.2f}R')
    p5.metric("Profit Factor", f'{stats["profit_factor"]:.2f}')
    p6.metric("Best Trade", f'${stats["best_trade"]:,.2f}')

    equity = journal_equity_frame(performance_source)
    if not equity.empty:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=equity["timestamp"],
                y=equity["equity"],
                mode="lines+markers",
                name="Cumulative P/L",
                fill="tozeroy",
            )
        )
        fig.update_layout(
            height=390,
            title="Equity Curve",
            margin=dict(l=8, r=8, t=40, b=8),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(8,18,32,.55)",
        )
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

    left_chart, right_chart = st.columns(2)
    with left_chart:
        by_setup = performance_source.copy()
        by_setup["pnl"] = pd.to_numeric(by_setup["pnl"], errors="coerce").fillna(0)
        by_setup = by_setup.groupby("setup", as_index=False).agg(
            trades=("trade_id", "count"),
            net_pnl=("pnl", "sum"),
            average_r=("r_multiple", "mean"),
            win_rate=("win", "mean"),
        )
        by_setup["win_rate"] = by_setup["win_rate"] * 100
        st.subheader("By Setup")
        st.dataframe(
            by_setup.sort_values("net_pnl", ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "net_pnl": st.column_config.NumberColumn(format="$%.2f"),
                "average_r": st.column_config.NumberColumn(format="%.2fR"),
                "win_rate": st.column_config.NumberColumn(format="%.1f%%"),
            },
        )

    with right_chart:
        by_emotion = performance_source.copy()
        by_emotion["pnl"] = pd.to_numeric(by_emotion["pnl"], errors="coerce").fillna(0)
        by_emotion = by_emotion.groupby("emotion", as_index=False).agg(
            trades=("trade_id", "count"),
            net_pnl=("pnl", "sum"),
            average_r=("r_multiple", "mean"),
        )
        st.subheader("By Emotion")
        st.dataframe(
            by_emotion.sort_values("net_pnl", ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "net_pnl": st.column_config.NumberColumn(format="$%.2f"),
                "average_r": st.column_config.NumberColumn(format="%.2fR"),
            },
        )

    st.subheader("Rule and Mistake Review")
    rleft, rright = st.columns(2)
    with rleft:
        plan_stats = performance_source.groupby("followed_plan", as_index=False).agg(
            trades=("trade_id", "count"),
            net_pnl=("pnl", "sum"),
            average_r=("r_multiple", "mean"),
        )
        plan_stats["followed_plan"] = plan_stats["followed_plan"].map({True: "Followed Plan", False: "Broke Plan"})
        st.dataframe(
            plan_stats,
            use_container_width=True,
            hide_index=True,
            column_config={
                "net_pnl": st.column_config.NumberColumn(format="$%.2f"),
                "average_r": st.column_config.NumberColumn(format="%.2fR"),
            },
        )
    with rright:
        mistakes = (
            performance_source["mistake"].fillna("None").replace("", "None")
            .value_counts().rename_axis("mistake").reset_index(name="count")
        )
        st.dataframe(mistakes, use_container_width=True, hide_index=True)

    if not using_demo:
        st.download_button(
            "Download Performance Data",
            performance_source.to_csv(index=False),
            f"spiderboys_performance_{date.today().isoformat()}.csv",
            mime="text/csv",
        )

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
    st.title("Spider Pro Scanner")
    st.caption("Dense momentum scanning, linked ticker analysis, multi-timeframe charts, and one-click journal preparation.")

    control1, control2, control3 = st.columns([2.2, 1.2, 1.4])
    with control1:
        scanner_name = st.selectbox(
            "Select Scanner",
            SCANNER_OPTIONS,
            index=SCANNER_OPTIONS.index(
                st.session_state.get("scanner_view", "HOD Momentum")
                if st.session_state.get("scanner_view", "HOD Momentum") in SCANNER_OPTIONS
                else "HOD Momentum"
            ),
        )
        st.session_state["scanner_view"] = scanner_name
    with control2:
        preset = st.selectbox(
            "Preset",
            ["Custom", "Under $10", "Under $20", "Low Float", "A Setups", "Catalyst Only"],
        )
    with control3:
        table_height = st.selectbox("Table Size", ["Compact", "Standard", "Tall"], index=1)

    st.markdown(
        f'<div class="scanner-description">{SCANNER_DESCRIPTIONS.get(scanner_name, "")}</div>',
        unsafe_allow_html=True,
    )

    with st.expander("Scanner Filters", expanded=True):
        f1, f2, f3, f4, f5, f6 = st.columns(6)
        with f1:
            min_price = st.number_input("Min Price", min_value=0.01, value=0.50, step=0.50)
        with f2:
            max_price_default = 10.0 if preset == "Under $10" else 20.0 if preset == "Under $20" else 50.0
            max_price = st.number_input("Max Price", min_value=1.0, value=max_price_default, step=5.0)
        with f3:
            max_float_default = 20.0 if preset == "Low Float" else 100.0
            max_float = st.number_input("Max Float M", min_value=1.0, value=max_float_default, step=5.0)
        with f4:
            min_rvol = st.number_input("Min Daily RVOL", min_value=0.0, value=1.0, step=0.5)
        with f5:
            min_gap = st.number_input("Min Gap %", value=0.0, step=1.0)
        with f6:
            score_default = 70 if preset == "A Setups" else 40
            min_score = st.slider("Min Spider Score", 0, 100, score_default)

        f7, f8, f9, f10 = st.columns(4)
        with f7:
            catalyst_only = st.checkbox("Catalyst only", value=preset == "Catalyst Only")
        with f8:
            green_only = st.checkbox("Positive movers only")
        with f9:
            close_to_hod_only = st.checkbox("Within 3% of HOD")
        with f10:
            first_pullback_only = st.checkbox("First Pullback only")

    frame = scanner_view_frame(scanner_name).copy()
    numeric_filters = {
        "price": pd.to_numeric(frame["price"], errors="coerce"),
        "float_m": pd.to_numeric(frame["float_m"], errors="coerce"),
        "relative_volume": pd.to_numeric(frame["relative_volume"], errors="coerce"),
        "gap_pct": pd.to_numeric(frame["gap_pct"], errors="coerce"),
        "spider_score": pd.to_numeric(frame["spider_score"], errors="coerce"),
        "day_change_pct": pd.to_numeric(frame["day_change_pct"], errors="coerce"),
        "distance_to_hod_pct": pd.to_numeric(frame["distance_to_hod_pct"], errors="coerce"),
    }
    frame = frame[
        numeric_filters["price"].between(min_price, max_price, inclusive="both")
        & (numeric_filters["float_m"] <= max_float)
        & (numeric_filters["relative_volume"] >= min_rvol)
        & (numeric_filters["gap_pct"] >= min_gap)
        & (numeric_filters["spider_score"] >= min_score)
    ].copy()

    if catalyst_only:
        frame = frame[frame["news"]]
    if green_only:
        frame = frame[pd.to_numeric(frame["day_change_pct"], errors="coerce").fillna(0) > 0]
    if close_to_hod_only:
        frame = frame[pd.to_numeric(frame["distance_to_hod_pct"], errors="coerce").fillna(999) <= 3]
    if first_pullback_only:
        frame = frame[
            frame["setup_status"].fillna("").astype(str).str.lower().str.contains("pullback|confirmed|forming")
        ]

    frame = frame.reset_index(drop=True)
    strongest = frame.iloc[0]["ticker"] if not frame.empty else "—"
    median_rvol = (
        float(pd.to_numeric(frame["relative_volume"], errors="coerce").median())
        if not frame.empty else 0.0
    )
    low_float_count = (
        int((pd.to_numeric(frame["float_m"], errors="coerce") <= 20).sum())
        if not frame.empty else 0
    )
    catalyst_count = int(frame["news"].sum()) if not frame.empty else 0

    sm1, sm2, sm3, sm4, sm5 = st.columns(5)
    sm1.metric("Matches", len(frame))
    sm2.metric("Top Symbol", strongest)
    sm3.metric("Median RVOL", f"{median_rvol:.2f}")
    sm4.metric("Low Float", low_float_count)
    sm5.metric("Catalysts", catalyst_count)

    st.markdown(
        f"""
        <div class="scanner-status-row">
          <span>{scanner_name.upper()}</span>
          <span>{preset.upper()}</span>
          <span>TRAINING-DERIVED SCANNER METRICS</span>
          <span>LIVE QUOTE / NEWS WHEN AVAILABLE</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if frame.empty:
        st.warning("No scanner rows match the current filters.")
        event = None
    else:
        display = scanner_display_frame(frame, compact=False)
        height_map = {"Compact": 360, "Standard": 560, "Tall": 760}
        try:
            styled = style_scanner_table(display)
            event = st.dataframe(
                styled,
                use_container_width=True,
                hide_index=True,
                height=height_map[table_height],
                on_select="rerun",
                selection_mode="single-row",
                key=f"pro_scanner_{scanner_name}_{preset}",
            )
        except (ImportError, ModuleNotFoundError, ValueError, TypeError) as exc:
            st.caption(f"Color styling fallback: {type(exc).__name__}. Scanner data remains available.")
            event = st.dataframe(
                display,
                use_container_width=True,
                hide_index=True,
                height=height_map[table_height],
                on_select="rerun",
                selection_mode="single-row",
                key=f"pro_scanner_{scanner_name}_{preset}_plain",
                column_config={
                    "Price": st.column_config.NumberColumn(format="$%.2f"),
                    "Volume": st.column_config.NumberColumn(format="compact"),
                    "Float M": st.column_config.NumberColumn(format="%.2f"),
                    "RVOL Daily": st.column_config.NumberColumn(format="%.2f"),
                    "RVOL 5m": st.column_config.NumberColumn(format="%.2f"),
                    "Gap %": st.column_config.NumberColumn(format="%.2f%%"),
                    "Change %": st.column_config.NumberColumn(format="%.2f%%"),
                    "5m %": st.column_config.NumberColumn(format="%.2f%%"),
                    "From HOD %": st.column_config.NumberColumn(format="%.2f%%"),
                    "Spider Score": st.column_config.ProgressColumn(min_value=0, max_value=100),
                },
            )

    selected_rows = event.selection.rows if event is not None and hasattr(event, "selection") else []
    if selected_rows and not frame.empty:
        position = int(selected_rows[0])
        if 0 <= position < len(frame):
            selected_symbol = str(frame.iloc[position]["ticker"])
            set_active_ticker(selected_symbol)
            st.session_state["scanner_last_selected"] = selected_symbol

    selected_symbol = st.session_state.get("scanner_last_selected", st.session_state["active_ticker"])
    if selected_symbol:
        st.markdown('<div class="terminal-panel-title">LINKED TICKER WORKSPACE</div>', unsafe_allow_html=True)
        st.success(f"{selected_symbol} is linked to Charts, News, Trade Plan, Command Center, and Journal prefill.")

        payload = get_market_payload(selected_symbol, "5min")
        ai = spider_ai_summary(payload)
        quote = payload.get("quote", {}) or {}
        profile = payload.get("profile", {}) or {}

        action1, action2, action3 = st.columns([1, 1, 3])
        with action1:
            if st.button("Prepare Journal Entry", type="primary", use_container_width=True):
                st.session_state["journal_prefill_ticker"] = selected_symbol
                st.success(f"{selected_symbol} is ready in the Journal page.")
        with action2:
            st.download_button(
                "Export Scanner",
                frame.to_csv(index=False),
                f"spiderboys_{scanner_name.lower().replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with action3:
            st.caption("Select a different scanner row to update every panel below.")

        info_col, chart_col, ai_col = st.columns([1.15, 2.35, 1.15], gap="small")
        with info_col:
            st.markdown('<div class="terminal-panel-title">STOCK INTELLIGENCE</div>', unsafe_allow_html=True)
            st.metric(
                selected_symbol,
                f'${float(quote.get("price")):.2f}' if quote.get("price") else "—",
                f'{float(quote.get("change_pct", 0)):+.2f}%' if quote else None,
            )
            st.write(f"**Company:** {profile.get('name') or '—'}")
            st.write(f"**Industry:** {profile.get('industry') or '—'}")
            st.write(f"**Exchange:** {profile.get('exchange') or '—'}")
            st.write(
                f"**Shares Out:** {float(profile.get('shares_outstanding_m')):,.2f}M"
                if profile.get("shares_outstanding_m") else "**Shares Out:** —"
            )

            selected_training = build_training_scanner_frame(market)
            selected_training = selected_training[
                selected_training["ticker"].astype(str) == selected_symbol
            ]
            if not selected_training.empty:
                row = selected_training.iloc[0]
                st.write(f'**Float:** {float(row["float_m"]):.2f}M')
                st.write(f'**Gap:** {float(row["gap_pct"]):.2f}%')
                st.write(f'**Daily RVOL:** {float(row["relative_volume"]):.2f}')
                st.write(f'**5m RVOL:** {float(row["rvol_5m"]):.2f}')
                st.write(f'**Setup:** {row["setup_status"]}')

            news_view = compact_news_view(payload.get("news"), 5)
            st.markdown('<div class="terminal-panel-title">LATEST NEWS</div>', unsafe_allow_html=True)
            if news_view.empty:
                st.caption("No recent company news returned.")
            else:
                for _, item in news_view.iterrows():
                    st.markdown(f"🔥 **{item.get('headline', '')}**")
                    st.caption(str(item.get("source", "")))

        with chart_col:
            st.markdown('<div class="terminal-panel-title">SYNCHRONIZED CHARTS</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                mini_candlestick_chart(selected_symbol, "5min", 355, f"pro_scanner_5m_{selected_symbol}")
            with c2:
                mini_candlestick_chart(selected_symbol, "1min", 355, f"pro_scanner_1m_{selected_symbol}")
            mini_candlestick_chart(selected_symbol, "15min", 315, f"pro_scanner_15m_{selected_symbol}")

        with ai_col:
            st.markdown('<div class="terminal-panel-title">SPIDER AI TRADE CARD</div>', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="sb-card ai-panel">
                  <div class="sb-ai-score">{ai["score"]}/100</div>
                  <div class="grade-row"><span>{ai["grade"]}</span><span>{ai["confidence"]}</span></div>
                  <div class="level-grid one-col">
                    <div><small>Trend</small><b>{ai["trend"]}</b></div>
                    <div><small>Entry</small><b>{"$"+format(ai["entry"], ".2f") if ai["entry"] else "—"}</b></div>
                    <div><small>Stop</small><b>{"$"+format(ai["stop"], ".2f") if ai["stop"] else "—"}</b></div>
                    <div><small>2R Target</small><b>{"$"+format(ai["target_2r"], ".2f") if ai["target_2r"] else "—"}</b></div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            for reason in ai["reasons"][:6]:
                st.write(f"✓ {reason}")
            st.caption("Rule-based setup review—not a prediction or trade recommendation.")

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
