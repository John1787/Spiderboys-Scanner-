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
    finnhub_profile, finnhub_quote, fmp_daily_history, fmp_intraday, fmp_profile, fmp_stock_news, catalyst_score
)

BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Spiderboys Trading Pro v12.2 Dark Decision Engine",
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


/* v12.1 fixed timeframe controls and AI directional intelligence */
[data-testid="stSegmentedControl"],
div[data-baseweb="button-group"] {
    background: #081523 !important;
    border: 1px solid rgba(80,176,235,.34) !important;
    border-radius: 10px !important;
    padding: 3px !important;
}
[data-testid="stSegmentedControl"] button,
div[data-baseweb="button-group"] button {
    background: #10253d !important;
    color: #e8f6ff !important;
    border: 1px solid rgba(86,157,211,.22) !important;
    box-shadow: none !important;
}
[data-testid="stSegmentedControl"] button:hover,
div[data-baseweb="button-group"] button:hover {
    background: #17456d !important;
    color: #ffffff !important;
}
[data-testid="stSegmentedControl"] button[aria-pressed="true"],
div[data-baseweb="button-group"] button[aria-pressed="true"] {
    background: linear-gradient(135deg, #1c6fd1, #119bb2) !important;
    color: #ffffff !important;
    border-color: #6de6ff !important;
}
[data-testid="stSegmentedControl"] button p,
div[data-baseweb="button-group"] button p {
    color: inherit !important;
    font-weight: 850 !important;
}
.stPlotlyChart,
.stPlotlyChart > div,
.js-plotly-plot,
.plot-container {
    background: #081523 !important;
}
.mini-empty {
    background: linear-gradient(145deg, #0b1c2f, #081523) !important;
    color: #eef8ff !important;
}
.direction-card {
    border: 1px solid rgba(83,177,236,.34);
    border-radius: 14px;
    padding: 1rem;
    background: linear-gradient(145deg, rgba(15,37,62,.98), rgba(7,23,40,.98));
    box-shadow: 0 12px 30px rgba(0,0,0,.18);
}
.direction-card.bias-bullish {
    border-left: 5px solid #22d89c;
}
.direction-card.bias-bearish {
    border-left: 5px solid #ff6378;
}
.direction-card.bias-neutral {
    border-left: 5px solid #f1c75b;
}
.direction-kicker {
    color: #8be5ff !important;
    font-size: .68rem;
    font-weight: 900;
    letter-spacing: .13em;
}
.direction-bias {
    color: #ffffff !important;
    font-size: 1.65rem;
    font-weight: 950;
    margin: .25rem 0;
}
.direction-confidence {
    color: #c7def3 !important;
    font-size: .82rem;
    margin-bottom: .7rem;
}
.direction-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: .55rem;
}
.direction-grid > div {
    background: rgba(4,18,31,.62);
    border: 1px solid rgba(80,160,215,.18);
    border-radius: 9px;
    padding: .55rem .62rem;
}
.direction-grid small {
    display: block;
    color: #98d9ff !important;
    text-transform: uppercase;
    font-size: .64rem;
    letter-spacing: .08em;
}
.direction-grid b {
    display: block;
    color: #ffffff !important;
    margin-top: .12rem;
}
.compact-ai {
    min-height: 0 !important;
}
@media (max-width: 900px) {
    .direction-grid {
        grid-template-columns: 1fr;
    }
}


/* v12.2 dark scanner and decision engine */
div[data-baseweb="select"] > div,
[data-testid="stSelectbox"] > div > div {
    background: #111b29 !important;
    color: #eaf4ff !important;
    border-color: #334b63 !important;
}
div[data-baseweb="select"] span,
div[data-baseweb="select"] input,
[data-testid="stSelectbox"] * {
    color: #eaf4ff !important;
}
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
    background: #111b29 !important;
    color: #f2f8ff !important;
    border-color: #334b63 !important;
}
[data-testid="stNumberInput"] button {
    background: #172638 !important;
    color: #eaf4ff !important;
    border-color: #334b63 !important;
}
[data-testid="stDataFrame"] {
    background: #0c1623 !important;
    border: 1px solid #2b4258 !important;
    box-shadow: 0 10px 26px rgba(0,0,0,.18);
}
[data-testid="stDataFrame"] [role="gridcell"] {
    background-color: #111b29;
    color: #dce9f5;
    border-color: #26384b;
}
[data-testid="stDataFrame"] [role="columnheader"] {
    background-color: #0b1725;
    color: #bfe7ff;
    border-color: #2b4258;
    font-weight: 850;
}
.scanner-decision-card {
    position: relative;
    background: linear-gradient(145deg, #101c2b, #091522);
    border: 1px solid #304962;
    border-left: 6px solid #75879a;
    border-radius: 14px;
    padding: 1rem 1.05rem;
    margin: .25rem 0 .75rem 0;
    box-shadow: 0 12px 28px rgba(0,0,0,.22);
}
.scanner-decision-card.decision-ready {
    border-left-color: #1fd29a;
}
.scanner-decision-card.decision-wait {
    border-left-color: #e1b94e;
}
.scanner-decision-card.decision-avoid {
    border-left-color: #ef5c70;
}
.decision-symbol {
    color: #9cddff !important;
    font-size: .74rem;
    font-weight: 900;
    letter-spacing: .13em;
}
.decision-status {
    color: #ffffff !important;
    font-size: 1.75rem;
    font-weight: 950;
    margin-top: .12rem;
}
.decision-note {
    color: #c5d8e8 !important;
    font-size: .84rem;
    margin: .15rem 0 .75rem 0;
}
.decision-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: .55rem;
}
.decision-grid > div {
    background: #142335;
    border: 1px solid #294058;
    border-radius: 9px;
    padding: .55rem .62rem;
}
.decision-grid small {
    display: block;
    color: #8fcaed !important;
    text-transform: uppercase;
    font-size: .63rem;
    letter-spacing: .08em;
}
.decision-grid b {
    display: block;
    color: #ffffff !important;
    margin-top: .14rem;
}
@media (max-width: 1000px) {
    .decision-grid {
        grid-template-columns: 1fr 1fr;
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
    _alpaca_cfg = st.secrets.get("alpaca", {})
    ALPACA_KEY = str(_alpaca_cfg.get("api_key", "")).strip()
    ALPACA_SECRET = str(_alpaca_cfg.get("secret_key", "")).strip()
    ALPACA_FEED = str(_alpaca_cfg.get("feed", "iex")).strip() or "iex"
except Exception:
    FMP_KEY = FINNHUB_KEY = ALPACA_KEY = ALPACA_SECRET = ""
    ALPACA_FEED = "iex"

if "active_ticker" not in st.session_state:
    st.session_state["active_ticker"] = str(market["ticker"].iloc[0]).upper()
if "layout_mode" not in st.session_state:
    st.session_state["layout_mode"] = "Compact"
if "saved_watchlist" not in st.session_state:
    st.session_state["saved_watchlist"] = ["SPY", "QQQ", "AAPL", "NVDA", st.session_state["active_ticker"]]
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
def _scanner_quality_score(row: pd.Series) -> int:
    """Transparent setup-quality score built only from available scanner fields."""
    spider = float(pd.to_numeric(row.get("spider_score", 0), errors="coerce") or 0)
    rvol = float(pd.to_numeric(row.get("relative_volume", 0), errors="coerce") or 0)
    rvol_5m = float(pd.to_numeric(row.get("rvol_5m", 0), errors="coerce") or 0)
    gap = float(pd.to_numeric(row.get("gap_pct", 0), errors="coerce") or 0)
    float_m = float(pd.to_numeric(row.get("float_m", 999), errors="coerce") or 999)
    room = float(pd.to_numeric(row.get("room_to_resistance_r", 0), errors="coerce") or 0)
    spread = float(pd.to_numeric(row.get("spread_pct", 99), errors="coerce") or 99)
    above_vwap = bool(row.get("above_vwap", False))
    catalyst = bool(str(row.get("catalyst", "") or "").strip())

    score = spider * 0.42
    score += min(rvol / 10, 1) * 12
    score += min(rvol_5m / 8, 1) * 8
    score += 10 if 8 <= gap <= 45 else 6 if 3 <= gap < 8 else 2 if gap > 45 else 0
    score += 8 if float_m <= 20 else 5 if float_m <= 50 else 1
    score += 7 if above_vwap else 0
    score += 7 if catalyst else 0
    score += 4 if room >= 2 else 2 if room >= 1.5 else 0
    score += 2 if spread <= 0.25 else 0
    return int(round(max(0, min(100, score))))


def _scanner_risk_assessment(row: pd.Series) -> tuple[int, str, str]:
    """Return risk points, label, and a concise primary warning."""
    risk = 0
    warnings: list[str] = []

    gap = float(pd.to_numeric(row.get("gap_pct", 0), errors="coerce") or 0)
    float_m = float(pd.to_numeric(row.get("float_m", 999), errors="coerce") or 999)
    rvol = float(pd.to_numeric(row.get("relative_volume", 0), errors="coerce") or 0)
    change_5m = float(pd.to_numeric(row.get("change_5m_pct", 0), errors="coerce") or 0)
    distance_hod = float(pd.to_numeric(row.get("distance_to_hod_pct", 999), errors="coerce") or 999)
    room = float(pd.to_numeric(row.get("room_to_resistance_r", 0), errors="coerce") or 0)
    spread = float(pd.to_numeric(row.get("spread_pct", 99), errors="coerce") or 99)
    setup = str(row.get("setup_status", "") or "").lower()
    catalyst_quality = str(row.get("catalyst_quality", "") or "").lower()
    above_vwap = bool(row.get("above_vwap", False))

    if "extended" in setup:
        risk += 35
        warnings.append("Extended—wait for a reset")
    if gap >= 50:
        risk += 18
        warnings.append("Large gap increases chase risk")
    if change_5m >= 8:
        risk += 18
        warnings.append("Fast 5-minute move")
    if distance_hod <= 1 and gap >= 25:
        risk += 12
        warnings.append("Near HOD after a large move")
    if float_m <= 5:
        risk += 16
        warnings.append("Ultra-low float volatility")
    elif float_m <= 10:
        risk += 8
    if spread > 0.50:
        risk += 25
        warnings.append("Spread is too wide")
    elif spread > 0.30:
        risk += 12
        warnings.append("Spread needs caution")
    if room < 1.5:
        risk += 20
        warnings.append("Limited room to resistance")
    elif room < 2:
        risk += 8
    if rvol < 2:
        risk += 15
        warnings.append("Weak relative volume")
    if not above_vwap:
        risk += 18
        warnings.append("Below VWAP")
    if catalyst_quality in {"weak", "none", ""}:
        risk += 10
        warnings.append("Weak or missing catalyst")

    risk = int(max(0, min(100, risk)))
    label = "HIGH" if risk >= 55 else "MODERATE" if risk >= 28 else "LOW"
    primary = warnings[0] if warnings else "No major structural warning"
    return risk, label, primary


def _scanner_readiness(row: pd.Series) -> tuple[str, str]:
    quality = int(row.get("momentum_quality", 0) or 0)
    risk = int(row.get("risk_score", 0) or 0)
    score = float(pd.to_numeric(row.get("spider_score", 0), errors="coerce") or 0)
    room = float(pd.to_numeric(row.get("room_to_resistance_r", 0), errors="coerce") or 0)
    spread = float(pd.to_numeric(row.get("spread_pct", 99), errors="coerce") or 99)
    setup = str(row.get("setup_status", "") or "").lower()
    above_vwap = bool(row.get("above_vwap", False))
    catalyst = bool(str(row.get("catalyst", "") or "").strip())

    confirmed = "confirmed" in setup or "break" in setup
    forming = "forming" in setup or "watch" in setup or "vwap" in setup
    extended = "extended" in setup

    if (
        quality >= 76
        and risk < 45
        and score >= 70
        and above_vwap
        and catalyst
        and room >= 1.8
        and spread <= 0.40
        and confirmed
        and not extended
    ):
        return "READY", "Structure, catalyst, volume, and risk are aligned"

    if extended or risk >= 65 or spread > 0.65 or room < 1.15:
        return "AVOID", str(row.get("primary_risk", "Risk is too high"))

    if quality >= 55 and score >= 55:
        reason = (
            "Wait for pullback confirmation"
            if forming or not confirmed
            else "Wait for cleaner risk and resistance room"
        )
        return "WAIT", reason

    return "AVOID", "Quality or confirmation is below minimum"


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
    result["distance_to_hod_pct"] = pd.to_numeric(
        result.get("hod_distance_pct", 0), errors="coerce"
    ).fillna(0)

    result["momentum_quality"] = result.apply(_scanner_quality_score, axis=1)

    risk_results = result.apply(_scanner_risk_assessment, axis=1)
    result["risk_score"] = [item[0] for item in risk_results]
    result["risk_level"] = [item[1] for item in risk_results]
    result["primary_risk"] = [item[2] for item in risk_results]

    readiness_results = result.apply(_scanner_readiness, axis=1)
    result["readiness"] = [item[0] for item in readiness_results]
    result["decision_note"] = [item[1] for item in readiness_results]

    result["signal"] = np.select(
        [
            result["readiness"].eq("READY"),
            result["readiness"].eq("WAIT"),
        ],
        ["🟢 READY", "🟡 WAIT"],
        default="🔴 AVOID",
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
            result["readiness"].eq("READY"),
            result["risk_level"].eq("HIGH"),
            pd.to_numeric(result["float_m"], errors="coerce").fillna(999) <= 5,
            pd.to_numeric(result["relative_volume"], errors="coerce").fillna(0) >= 8,
            result["news"],
        ],
        [
            "Decision engine: ready",
            result["primary_risk"],
            "Ultra-low float",
            "High-RVOL profile",
            "Catalyst present",
        ],
        default="Developing setup",
    )
    result["risk_per_share"] = (
        pd.to_numeric(result["entry"], errors="coerce")
        - pd.to_numeric(result["stop"], errors="coerce")
    ).abs()
    result["data_source"] = "Training-derived scanner intelligence"
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
        "change_5m_pct", "distance_to_hod_pct", "momentum_quality",
        "signal", "risk_level", "context_note", "setup_status",
    ]
    if compact:
        columns = [
            "alert_time", "symbol_news", "price", "float_m",
            "relative_volume", "gap_pct", "momentum_quality", "signal", "risk_level",
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
        "momentum_quality": "Quality",
        "signal": "Decision",
        "risk_level": "Risk",
        "context_note": "Context",
        "setup_status": "Setup",
    }
    return display.rename(columns=rename)


def style_scanner_table(display: pd.DataFrame):
    """Dark terminal-style table with muted colors and no white cell backgrounds."""
    base_cell = "background-color:#111b29;color:#dce9f5;border-color:#26384b;"
    neutral_cell = "background-color:#172434;color:#cbd9e6;"
    muted_green = "background-color:#174c3a;color:#d9fff0;font-weight:850;"
    strong_green = "background-color:#127048;color:#ffffff;font-weight:900;"
    muted_red = "background-color:#5b2530;color:#ffe8ec;font-weight:850;"
    strong_red = "background-color:#8e2638;color:#ffffff;font-weight:900;"
    amber = "background-color:#59481d;color:#fff2bf;font-weight:850;"
    cyan = "background-color:#124b58;color:#d9faff;font-weight:850;"
    teal = "background-color:#155447;color:#dcfff5;font-weight:850;"
    blue = "background-color:#173f69;color:#e3f3ff;font-weight:850;"

    def pct_color(value):
        try:
            number = float(value)
        except Exception:
            return neutral_cell
        if number >= 20:
            return strong_green
        if number >= 5:
            return muted_green
        if number > 0:
            return "background-color:#203d32;color:#dcf8e7;"
        if number <= -10:
            return strong_red
        if number < 0:
            return muted_red
        return neutral_cell

    def rvol_color(value):
        try:
            number = float(value)
        except Exception:
            return neutral_cell
        if number >= 10:
            return "background-color:#0d6770;color:#ffffff;font-weight:900;"
        if number >= 5:
            return cyan
        if number >= 2:
            return "background-color:#38452b;color:#edf5d0;font-weight:800;"
        return neutral_cell

    def float_color(value):
        try:
            number = float(value)
        except Exception:
            return neutral_cell
        if number <= 5:
            return "background-color:#0d6260;color:#ffffff;font-weight:900;"
        if number <= 20:
            return teal
        if number <= 50:
            return "background-color:#253b38;color:#dfeeea;"
        return neutral_cell

    def quality_color(value):
        try:
            number = float(value)
        except Exception:
            return neutral_cell
        if number >= 80:
            return strong_green
        if number >= 65:
            return muted_green
        if number >= 50:
            return amber
        return muted_red

    def decision_color(value):
        text = str(value).upper()
        if "READY" in text:
            return strong_green
        if "WAIT" in text:
            return amber
        if "AVOID" in text:
            return strong_red
        return neutral_cell

    def risk_color(value):
        text = str(value).upper()
        if "HIGH" in text:
            return strong_red
        if "MODERATE" in text:
            return amber
        if "LOW" in text:
            return muted_green
        return neutral_cell

    styler = (
        display.style
        .set_properties(**{
            "background-color": "#111b29",
            "color": "#dce9f5",
            "border-color": "#26384b",
        })
        .set_table_styles([
            {
                "selector": "th",
                "props": [
                    ("background-color", "#0b1725"),
                    ("color", "#bfe7ff"),
                    ("font-weight", "850"),
                    ("border-color", "#2b425a"),
                ],
            },
            {
                "selector": "td",
                "props": [
                    ("background-color", "#111b29"),
                    ("color", "#dce9f5"),
                    ("border-color", "#26384b"),
                ],
            },
            {
                "selector": "tbody tr:nth-child(even) td",
                "props": [("background-color", "#142131")],
            },
        ])
    )

    for col in ["Gap %", "Change %", "5m %"]:
        if col in display.columns:
            styler = styler.map(pct_color, subset=[col])
    for col in ["RVOL Daily", "RVOL 5m"]:
        if col in display.columns:
            styler = styler.map(rvol_color, subset=[col])
    if "Float M" in display.columns:
        styler = styler.map(float_color, subset=["Float M"])
    if "Quality" in display.columns:
        styler = styler.map(quality_color, subset=["Quality"])
    if "Decision" in display.columns:
        styler = styler.map(decision_color, subset=["Decision"])
    if "Risk" in display.columns:
        styler = styler.map(risk_color, subset=["Risk"])
    if "Price" in display.columns:
        styler = styler.map(lambda _: blue, subset=["Price"])

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
        "Quality": "{:.0f}",
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
        fallback_styled = (
            display.style
            .set_properties(**{
                "background-color": "#111b29",
                "color": "#dce9f5",
                "border-color": "#26384b",
            })
            .set_table_styles([{
                "selector": "th",
                "props": [
                    ("background-color", "#0b1725"),
                    ("color", "#bfe7ff"),
                    ("font-weight", "850"),
                ],
            }])
        )
        event = st.dataframe(
            fallback_styled,
            use_container_width=True,
            hide_index=True,
            height=height,
            on_select="rerun",
            selection_mode="single-row",
            key=f"{key}_plain",
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
            f'<div class="mini-empty">{ticker} · {interval}<br><small>{friendly_market_data_note(note)}</small></div>',
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



@st.cache_data(ttl=900, show_spinner=False)
def load_recent_daily_history(
    symbol: str,
    fmp_key: str,
    alpaca_key: str,
    alpaca_secret: str,
    alpaca_feed: str,
) -> tuple[pd.DataFrame, str, str]:
    """Return recent daily bars from Alpaca, FMP EOD, or labeled training fallback."""
    symbol = normalize_symbol(symbol)
    notes: list[str] = []

    if alpaca_key and alpaca_secret:
        try:
            frame = get_bars(
                symbol,
                alpaca_key,
                alpaca_secret,
                timeframe="1Day",
                limit=30,
                feed=alpaca_feed,
            )
            if isinstance(frame, pd.DataFrame) and not frame.empty:
                frame = frame.copy().sort_values("datetime").tail(30).reset_index(drop=True)
                frame = frame.rename(columns={"datetime": "date"})
                for col in ["open", "high", "low", "close", "volume"]:
                    frame[col] = pd.to_numeric(frame[col], errors="coerce")
                frame["sma3"] = frame["close"].rolling(3, min_periods=1).mean()
                frame["sma5"] = frame["close"].rolling(5, min_periods=1).mean()
                frame["sma10"] = frame["close"].rolling(10, min_periods=1).mean()
                frame["ema5"] = frame["close"].ewm(span=5, adjust=False).mean()
                frame["ema10"] = frame["close"].ewm(span=10, adjust=False).mean()
                return frame, "LIVE", f"Alpaca daily bars ({alpaca_feed.upper()} feed)"
            notes.append("Alpaca returned no daily bars.")
        except Exception as exc:
            notes.append(f"Alpaca: {type(exc).__name__}: {exc}")

    if fmp_key:
        try:
            frame = fmp_daily_history(symbol, fmp_key, lookback_days=50)
            if isinstance(frame, pd.DataFrame) and not frame.empty:
                return frame, "LIVE", str(frame["source"].iloc[-1])
            notes.append("FMP returned no daily bars.")
        except Exception as exc:
            notes.append(f"FMP: {type(exc).__name__}: {exc}")

    # Training fallback is only available for symbols bundled with the app.
    try:
        demo = market[market["ticker"].astype(str).str.upper() == symbol].copy()
    except Exception:
        demo = pd.DataFrame()

    if not demo.empty:
        demo = demo.sort_values("datetime").copy()
        demo["date"] = pd.to_datetime(demo["datetime"], errors="coerce").dt.normalize()
        daily = (
            demo.groupby("date", as_index=False)
            .agg(
                open=("open", "first"),
                high=("high", "max"),
                low=("low", "min"),
                close=("close", "last"),
                volume=("volume", "sum"),
            )
            .dropna(subset=["close"])
        )
        daily["sma3"] = daily["close"].rolling(3, min_periods=1).mean()
        daily["sma5"] = daily["close"].rolling(5, min_periods=1).mean()
        daily["sma10"] = daily["close"].rolling(10, min_periods=1).mean()
        daily["ema5"] = daily["close"].ewm(span=5, adjust=False).mean()
        daily["ema10"] = daily["close"].ewm(span=10, adjust=False).mean()
        return daily, "DEMO", "Bundled training data—not recent market history"

    return pd.DataFrame(), "UNAVAILABLE", " | ".join(notes[-3:]) or "No recent daily source is configured."


def build_directional_intelligence(payload: dict, daily_bars: pd.DataFrame) -> dict:
    """Scenario-based directional bias. It deliberately avoids certainty or probability claims."""
    quote = payload.get("quote", {}) or {}
    news = payload.get("news", pd.DataFrame())
    intraday = payload.get("bars", pd.DataFrame())

    score = 0
    evidence: list[str] = []
    cautions: list[str] = []
    data_points = 0
    three_day = None
    five_day = None
    support = None
    resistance = None
    latest_close = None
    trend_structure = "Insufficient"

    if isinstance(daily_bars, pd.DataFrame) and len(daily_bars) >= 2:
        daily = daily_bars.copy().sort_values("date")
        close = pd.to_numeric(daily["close"], errors="coerce")
        high = pd.to_numeric(daily["high"], errors="coerce")
        low = pd.to_numeric(daily["low"], errors="coerce")
        volume = pd.to_numeric(daily["volume"], errors="coerce").fillna(0)
        daily = daily.assign(close=close, high=high, low=low, volume=volume).dropna(subset=["close"])

        if not daily.empty:
            latest = daily.iloc[-1]
            latest_close = float(latest["close"])
            sma3 = float(latest.get("sma3", latest_close))
            sma5 = float(latest.get("sma5", latest_close))
            sma10 = float(latest.get("sma10", latest_close))
            data_points += 4

            if latest_close > sma3 > sma5:
                score += 24
                evidence.append("Daily close is above the 3-day and 5-day averages")
                trend_structure = "Short-term bullish"
            elif latest_close < sma3 < sma5:
                score -= 24
                evidence.append("Daily close is below the 3-day and 5-day averages")
                trend_structure = "Short-term bearish"
            else:
                evidence.append("Daily averages are mixed")
                trend_structure = "Mixed"

            if len(daily) >= 4:
                base = float(daily["close"].iloc[-4])
                three_day = ((latest_close / base) - 1) * 100 if base else None
                if three_day is not None:
                    score += 15 if three_day >= 3 else 7 if three_day > 0 else -15 if three_day <= -3 else -7
                    evidence.append(f"Three-session change is {three_day:+.2f}%")
                    data_points += 1

            if len(daily) >= 6:
                base = float(daily["close"].iloc[-6])
                five_day = ((latest_close / base) - 1) * 100 if base else None
                if five_day is not None:
                    score += 15 if five_day >= 5 else 7 if five_day > 0 else -15 if five_day <= -5 else -7
                    evidence.append(f"Five-session change is {five_day:+.2f}%")
                    data_points += 1

            recent = daily.tail(min(7, len(daily)))
            support = float(recent["low"].min()) if recent["low"].notna().any() else None
            resistance = float(recent["high"].max()) if recent["high"].notna().any() else None

            if len(daily) >= 4:
                recent_highs = daily["high"].tail(3).tolist()
                recent_lows = daily["low"].tail(3).tolist()
                if all(pd.notna(x) for x in recent_highs + recent_lows):
                    higher_highs = recent_highs[0] <= recent_highs[1] <= recent_highs[2]
                    higher_lows = recent_lows[0] <= recent_lows[1] <= recent_lows[2]
                    lower_highs = recent_highs[0] >= recent_highs[1] >= recent_highs[2]
                    lower_lows = recent_lows[0] >= recent_lows[1] >= recent_lows[2]
                    if higher_highs and higher_lows:
                        score += 16
                        evidence.append("Recent daily candles show higher highs and higher lows")
                    elif lower_highs and lower_lows:
                        score -= 16
                        evidence.append("Recent daily candles show lower highs and lower lows")
                    data_points += 1

            if len(daily) >= 6 and volume.tail(5).mean() > 0:
                latest_volume = float(volume.iloc[-1])
                average_volume = float(volume.tail(6).iloc[:-1].mean())
                if average_volume > 0:
                    volume_ratio = latest_volume / average_volume
                    if volume_ratio >= 1.5:
                        direction = float(daily["close"].iloc[-1]) - float(daily["close"].iloc[-2])
                        score += 8 if direction > 0 else -8
                        evidence.append(f"Latest daily volume is {volume_ratio:.1f}× its recent average")
                    data_points += 1

    day_change = quote.get("change_pct")
    if day_change is not None:
        try:
            day_change = float(day_change)
            score += 10 if day_change >= 2 else 4 if day_change > 0 else -10 if day_change <= -2 else -4
            evidence.append(f"Current session change is {day_change:+.2f}%")
            data_points += 1
        except Exception:
            pass

    news_tone = "No recent news"
    if isinstance(news, pd.DataFrame) and not news.empty:
        data_points += 1
        if "sentiment" in news.columns:
            values = news["sentiment"].astype(str).str.lower()
            bullish = int(values.str.contains("bull").sum())
            bearish = int(values.str.contains("bear").sum())
            if bullish > bearish:
                score += min(15, 5 + bullish * 3)
                news_tone = "Bullish-leaning"
                evidence.append("Recent headlines lean bullish")
            elif bearish > bullish:
                score -= min(15, 5 + bearish * 3)
                news_tone = "Bearish-leaning"
                evidence.append("Recent headlines lean bearish")
            else:
                news_tone = "Mixed / neutral"
                evidence.append("Recent headlines are mixed or neutral")
        else:
            news_tone = "Headlines available"
            evidence.append("Recent company headlines are available")

        headlines = " ".join(news.get("headline", pd.Series(dtype=str)).astype(str).head(10)).lower()
        risk_terms = ["offering", "dilution", "bankruptcy", "investigation", "downgrade", "misses", "lawsuit"]
        positive_terms = ["contract", "approval", "partnership", "beats", "award", "acquisition", "guidance"]
        if any(term in headlines for term in risk_terms):
            score -= 12
            cautions.append("Recent headlines contain a potential dilution, legal, downgrade, or balance-sheet risk term")
        if any(term in headlines for term in positive_terms):
            score += 10
            evidence.append("Recent headlines contain a potentially positive catalyst term")

    if isinstance(intraday, pd.DataFrame) and not intraday.empty:
        intraday = intraday.sort_values("datetime")
        last = intraday.iloc[-1]
        close = float(last.get("close", 0) or 0)
        vwap = float(last.get("vwap", close) or close)
        ema9 = float(last.get("ema9", close) or close)
        ema20 = float(last.get("ema20", close) or close)
        if close > vwap and ema9 > ema20:
            score += 15
            evidence.append("Intraday price is above VWAP with EMA 9 over EMA 20")
        elif close < vwap and ema9 < ema20:
            score -= 15
            evidence.append("Intraday price is below VWAP with EMA 9 under EMA 20")
        else:
            cautions.append("Intraday VWAP and EMA structure is mixed")
        data_points += 1

    score = int(max(-100, min(100, score)))
    if data_points < 3:
        bias = "Insufficient data"
        confidence = "Low"
    elif score >= 45:
        bias = "Bullish bias"
        confidence = "High" if data_points >= 7 else "Moderate"
    elif score >= 18:
        bias = "Slight bullish bias"
        confidence = "Moderate" if data_points >= 5 else "Low"
    elif score <= -45:
        bias = "Bearish bias"
        confidence = "High" if data_points >= 7 else "Moderate"
    elif score <= -18:
        bias = "Slight bearish bias"
        confidence = "Moderate" if data_points >= 5 else "Low"
    else:
        bias = "Neutral / mixed"
        confidence = "Moderate" if data_points >= 5 else "Low"

    if support is not None and latest_close is not None and latest_close <= support * 1.02:
        cautions.append("Price is close to recent support; a breakdown would weaken the setup")
    if resistance is not None and latest_close is not None and latest_close >= resistance * 0.98:
        cautions.append("Price is near recent resistance; confirmation is needed before assuming continuation")

    bullish_confirmation = resistance
    bearish_invalidation = support

    return {
        "score": score,
        "bias": bias,
        "confidence": confidence,
        "trend_structure": trend_structure,
        "three_day_change": three_day,
        "five_day_change": five_day,
        "support": support,
        "resistance": resistance,
        "bullish_confirmation": bullish_confirmation,
        "bearish_invalidation": bearish_invalidation,
        "news_tone": news_tone,
        "evidence": evidence[:8],
        "cautions": cautions[:5] or ["No major caution was identified from the available data"],
        "data_points": data_points,
    }


def render_daily_intelligence_chart(daily_bars: pd.DataFrame, symbol: str, mode: str, note: str) -> None:
    if not isinstance(daily_bars, pd.DataFrame) or daily_bars.empty:
        st.info(f"Recent daily chart unavailable. {note}")
        return

    frame = daily_bars.copy().sort_values("date")
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=frame["date"],
            open=frame["open"],
            high=frame["high"],
            low=frame["low"],
            close=frame["close"],
            name=symbol,
        )
    )
    for col, label in [("sma3", "SMA 3"), ("sma5", "SMA 5"), ("sma10", "SMA 10")]:
        if col in frame.columns:
            fig.add_trace(go.Scatter(x=frame["date"], y=frame[col], mode="lines", name=label))
    fig.update_layout(
        height=430,
        margin=dict(l=8, r=8, t=38, b=8),
        title=f"{symbol} · Recent Daily Structure · {mode}",
        xaxis_rangeslider_visible=False,
        paper_bgcolor="#081523",
        plot_bgcolor="#081523",
        font=dict(color="#f6fbff"),
        legend_orientation="h",
        legend_y=1.03,
    )
    fig.update_xaxes(gridcolor="rgba(112,158,198,.14)", color="#d9ecff")
    fig.update_yaxes(gridcolor="rgba(112,158,198,.14)", color="#d9ecff")
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
    st.caption(note)


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


@st.cache_data(ttl=120, show_spinner=False)
def scanner_market_regime(finnhub_key: str) -> dict:
    if not finnhub_key:
        return {
            "label": "UNAVAILABLE",
            "score": 0,
            "spy": None,
            "qqq": None,
            "note": "Connect Finnhub to add live SPY/QQQ market alignment.",
        }

    try:
        spy = finnhub_quote("SPY", finnhub_key) or {}
        qqq = finnhub_quote("QQQ", finnhub_key) or {}
        spy_change = float(spy.get("change_pct", 0) or 0)
        qqq_change = float(qqq.get("change_pct", 0) or 0)
        average = (spy_change + qqq_change) / 2

        if spy_change > 0.35 and qqq_change > 0.35:
            label = "RISK-ON"
            note = "SPY and QQQ are both positive; long momentum has broader-market support."
        elif spy_change < -0.35 and qqq_change < -0.35:
            label = "RISK-OFF"
            note = "SPY and QQQ are both negative; long momentum deserves tighter confirmation."
        else:
            label = "MIXED"
            note = "The broad market is mixed; rely more heavily on the stock-specific catalyst and tape."

        return {
            "label": label,
            "score": round(average, 2),
            "spy": round(spy_change, 2),
            "qqq": round(qqq_change, 2),
            "note": note,
        }
    except Exception as exc:
        return {
            "label": "UNAVAILABLE",
            "score": 0,
            "spy": None,
            "qqq": None,
            "note": f"Market alignment could not be loaded: {type(exc).__name__}.",
        }


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


def scanner_news_brief(news: pd.DataFrame) -> dict:
    if not isinstance(news, pd.DataFrame) or news.empty:
        return {
            "tone": "No recent news",
            "risk_terms": [],
            "positive_terms": [],
            "warning": "No fresh headline confirmation is available.",
        }

    text = " ".join(
        news.get("headline", pd.Series(dtype=str)).astype(str).head(12).tolist()
        + news.get("summary", pd.Series(dtype=str)).astype(str).head(12).tolist()
    ).lower()

    risk_dictionary = {
        "offering": "Offering / dilution",
        "dilution": "Dilution",
        "reverse split": "Reverse split",
        "bankruptcy": "Bankruptcy risk",
        "investigation": "Investigation",
        "lawsuit": "Legal risk",
        "downgrade": "Downgrade",
        "delisting": "Delisting risk",
        "warrant": "Warrant overhang",
        "going concern": "Going-concern language",
    }
    positive_dictionary = {
        "approval": "Approval",
        "contract": "Contract",
        "partnership": "Partnership",
        "award": "Award",
        "acquisition": "Acquisition",
        "beats": "Earnings beat",
        "guidance": "Guidance",
        "patent": "Patent",
        "clearance": "Regulatory clearance",
    }

    risks = [label for term, label in risk_dictionary.items() if term in text]
    positives = [label for term, label in positive_dictionary.items() if term in text]

    if risks and not positives:
        tone = "Risk-heavy"
    elif positives and not risks:
        tone = "Positive catalyst"
    elif risks and positives:
        tone = "Mixed catalyst"
    else:
        tone = "Neutral / unclassified"

    warning = (
        "Review the headline carefully before entering; risk language was detected."
        if risks
        else "No major dilution or legal-risk term was detected in the available headlines."
    )
    return {
        "tone": tone,
        "risk_terms": risks,
        "positive_terms": positives,
        "warning": warning,
    }


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


def friendly_market_data_note(note: str) -> str:
    text = str(note or "")
    lower = text.lower()
    if "402" in lower or "restricted endpoint" in lower:
        return "Intraday candles are not included in the current data plan. Live quotes and news can still work."
    if "rate limit" in lower or "429" in lower:
        return "The data provider rate limit was reached. Wait briefly and refresh."
    if "not configured" in lower or "missing" in lower:
        return "A compatible chart-data connection is not configured."
    if "no chart source" in lower or "no intraday bars" in lower:
        return "No candle data was returned for this symbol."
    return text[:220]



def candlestick_chart(ticker, height=620, show_levels=True, interval="5min"):
    g, mode, source_note = get_chart_frame(ticker, interval)
    if g.empty:
        st.warning(f"{ticker} chart unavailable — {friendly_market_data_note(source_note)}")
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
  <div style="font-size:.78rem;color:#ffffff;margin-top:.2rem;">Dark Decision Engine v12.2</div>
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
    layout_mode = st.session_state.get("layout_mode", "Compact")
    payload = get_market_payload(active, "5min")
    ai = spider_ai_summary(payload)
    quote = payload.get("quote", {}) or {}
    profile = payload.get("profile", {}) or {}
    session = market_session_label()

    home_scanner = build_training_scanner_frame(market)
    home_match = home_scanner[
        home_scanner["ticker"].astype(str) == active
    ]
    home_row = home_match.iloc[0] if not home_match.empty else None
    home_quality = int(home_row["momentum_quality"]) if home_row is not None else ai["score"]
    home_decision = str(home_row["readiness"]) if home_row is not None else ai["grade"]
    home_risk = str(home_row["risk_level"]) if home_row is not None else payload["chart_mode"]

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
    m4.metric("Setup Quality", f"{home_quality}/100")
    m5.metric("Decision", home_decision)
    m6.metric("Risk", home_risk)

    tool_b, tool_c = st.columns([2.5, 2.0])
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
            key="v12_1_primary_timeframe",
        )

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

        st.markdown('<div class="terminal-panel-title">STOCK INTELLIGENCE</div>', unsafe_allow_html=True)
        intel_left, intel_right = st.columns([1.1, 1.4])
        with intel_left:
            company_name = profile.get("name") or active
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
            st.write(f"**Industry:** {profile.get('industry') or '—'}")
            st.write(
                f"**Shares Out:** {float(profile.get('shares_outstanding_m')):,.2f}M"
                if profile.get("shares_outstanding_m") else "**Shares Out:** —"
            )
        with intel_right:
            st.markdown(
                f"""
                <div class="sb-card ai-panel compact-ai">
                  <div class="sb-ai-score">{ai["score"]}/100</div>
                  <div class="grade-row"><span>{ai["grade"]}</span><span>{ai["confidence"]}</span></div>
                  <div class="level-grid">
                    <div><small>Trend</small><b>{ai["trend"]}</b></div>
                    <div><small>Entry</small><b>{"$"+format(ai["entry"], ".2f") if ai["entry"] else "—"}</b></div>
                    <div><small>Stop</small><b>{"$"+format(ai["stop"], ".2f") if ai["stop"] else "—"}</b></div>
                    <div><small>2R Target</small><b>{"$"+format(ai["target_2r"], ".2f") if ai["target_2r"] else "—"}</b></div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            for reason in ai["reasons"][:4]:
                st.write(f"✓ {reason}")

    else:
        scanner_col, chart_col, intel_col = st.columns([1.38, 2.35, 1.15], gap="small")

        with scanner_col:
            st.markdown(
                f'<div class="terminal-panel-title">{scanner_name.upper()}</div>',
                unsafe_allow_html=True,
            )
            st.caption("Colored cells are training-derived; quotes and news use live providers when available.")
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
    st.title("AI Trade Plan")
    st.caption(
        "Scenario-based intelligence from recent daily structure, intraday chart data when available, "
        "current quote movement, and recent news. It is not a prediction or guarantee."
    )

    symbol_col, direction_col, load_col = st.columns([3.3, 1.2, 1])
    with symbol_col:
        planner_symbol = st.text_input(
            "Ticker",
            value=st.session_state["active_ticker"],
            key="planner_symbol",
        )
    with direction_col:
        trade_side = st.selectbox("Trade Side", ["Long", "Short"])
    with load_col:
        st.write("")
        st.write("")
        if st.button("Analyze Ticker", type="primary", use_container_width=True):
            set_active_ticker(planner_symbol)
            st.cache_data.clear()
            st.rerun()

    ticker = st.session_state["active_ticker"]
    payload = get_market_payload(ticker, "5min")
    intraday_bars = payload["bars"]
    chart_mode = payload["chart_mode"]
    setup_ai = spider_ai_summary(payload)

    daily_bars, daily_mode, daily_note = load_recent_daily_history(
        ticker,
        FMP_KEY,
        ALPACA_KEY,
        ALPACA_SECRET,
        ALPACA_FEED,
    )
    direction_ai = build_directional_intelligence(payload, daily_bars)

    st.markdown('<div class="journal-section-title">DIRECTIONAL INTELLIGENCE</div>', unsafe_allow_html=True)
    i1, i2, i3, i4, i5, i6 = st.columns(6)
    i1.metric("Current Bias", direction_ai["bias"])
    i2.metric("Confidence", direction_ai["confidence"])
    i3.metric(
        "3-Session",
        f'{direction_ai["three_day_change"]:+.2f}%'
        if direction_ai["three_day_change"] is not None else "—",
    )
    i4.metric(
        "5-Session",
        f'{direction_ai["five_day_change"]:+.2f}%'
        if direction_ai["five_day_change"] is not None else "—",
    )
    i5.metric("News Tone", direction_ai["news_tone"])
    i6.metric("History Data", daily_mode)

    chart_col, intelligence_col = st.columns([1.65, 1])
    with chart_col:
        render_daily_intelligence_chart(daily_bars, ticker, daily_mode, daily_note)

    with intelligence_col:
        bias_class = (
            "bias-bullish"
            if "bullish" in direction_ai["bias"].lower()
            else "bias-bearish"
            if "bearish" in direction_ai["bias"].lower()
            else "bias-neutral"
        )
        st.markdown(
            f"""
            <div class="direction-card {bias_class}">
              <div class="direction-kicker">SPIDER AI MARKET READ</div>
              <div class="direction-bias">{direction_ai["bias"]}</div>
              <div class="direction-confidence">
                {direction_ai["confidence"]} confidence · intelligence score {direction_ai["score"]:+d}
              </div>
              <div class="direction-grid">
                <div><small>Daily Structure</small><b>{direction_ai["trend_structure"]}</b></div>
                <div><small>Recent Support</small><b>{"$"+format(direction_ai["support"], ".2f") if direction_ai["support"] is not None else "—"}</b></div>
                <div><small>Recent Resistance</small><b>{"$"+format(direction_ai["resistance"], ".2f") if direction_ai["resistance"] is not None else "—"}</b></div>
                <div><small>Evidence Used</small><b>{direction_ai["data_points"]} signals</b></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("**What supports this read**")
        for reason in direction_ai["evidence"][:6]:
            st.write(f"✓ {reason}")

        st.markdown("**What could invalidate it**")
        for caution in direction_ai["cautions"][:4]:
            st.write(f"⚠ {caution}")

    level_left, level_right = st.columns(2)
    with level_left:
        confirmation = direction_ai["bullish_confirmation"]
        st.info(
            "Bullish confirmation: "
            + (
                f"a sustained move above approximately **${confirmation:.2f}** with volume."
                if confirmation is not None
                else "wait for price to reclaim resistance, VWAP, and short-term averages."
            )
        )
    with level_right:
        invalidation = direction_ai["bearish_invalidation"]
        st.warning(
            "Bearish confirmation / long invalidation: "
            + (
                f"a loss of approximately **${invalidation:.2f}**."
                if invalidation is not None
                else "a breakdown below recent support or failure to hold VWAP."
            )
        )

    news_frame = payload.get("news", pd.DataFrame())
    if isinstance(news_frame, pd.DataFrame) and not news_frame.empty:
        with st.expander("Recent headlines used in the analysis", expanded=False):
            news_cols = [col for col in ["published", "headline", "source", "sentiment", "url"] if col in news_frame.columns]
            st.dataframe(
                news_frame[news_cols].head(10),
                use_container_width=True,
                hide_index=True,
                column_config={"url": st.column_config.LinkColumn("Article")},
            )

    st.markdown('<div class="journal-section-title">TRADE CONSTRUCTION</div>', unsafe_allow_html=True)

    quote = payload.get("quote", {}) or {}
    current_price = float(quote.get("price", 0) or 0)
    if current_price <= 0 and isinstance(daily_bars, pd.DataFrame) and not daily_bars.empty:
        current_price = float(pd.to_numeric(daily_bars["close"], errors="coerce").dropna().iloc[-1])
    if current_price <= 0 and isinstance(intraday_bars, pd.DataFrame) and not intraday_bars.empty:
        current_price = float(pd.to_numeric(intraday_bars["close"], errors="coerce").dropna().iloc[-1])

    support = direction_ai["support"]
    resistance = direction_ai["resistance"]

    if trade_side == "Long":
        default_entry = (
            float(setup_ai["entry"])
            if setup_ai.get("entry")
            else float(resistance)
            if resistance is not None and current_price > 0
            else current_price
        )
        default_stop = (
            float(setup_ai["stop"])
            if setup_ai.get("stop") and float(setup_ai["stop"]) < default_entry
            else float(support)
            if support is not None and float(support) < default_entry
            else default_entry * 0.97 if default_entry > 0 else 0.01
        )
    else:
        default_entry = current_price or float(support or resistance or 0.01)
        default_stop = (
            float(resistance)
            if resistance is not None and float(resistance) > default_entry
            else max(default_entry * 1.03, default_entry + 0.01)
        )

    plan_left, plan_right = st.columns([1.5, 1])
    with plan_left:
        if not intraday_bars.empty:
            candlestick_chart(ticker, 540, interval="5min")
        else:
            st.info(
                "Intraday candle data is unavailable under the current provider plan. "
                "The plan below uses recent daily structure, quote movement, and news instead."
            )
            render_daily_intelligence_chart(daily_bars, ticker, daily_mode, daily_note)

    with plan_right:
        account = st.number_input("Account Size", min_value=0.0, value=10000.0, step=500.0)
        risk_pct = st.number_input("Risk Per Trade %", min_value=0.05, value=0.5, step=0.1)
        entry = st.number_input(
            "Planned Entry",
            min_value=0.01,
            value=round(max(default_entry, 0.01), 2),
            step=0.01,
        )
        stop = st.number_input(
            "Planned Stop",
            min_value=0.01,
            value=round(max(default_stop, 0.01), 2),
            step=0.01,
        )

        if trade_side == "Long":
            risk_per_share = max(0.0, entry - stop)
            target_1r = entry + risk_per_share
            target_2r = entry + (2 * risk_per_share)
        else:
            risk_per_share = max(0.0, stop - entry)
            target_1r = entry - risk_per_share
            target_2r = entry - (2 * risk_per_share)

        dollar_risk = account * (risk_pct / 100)
        shares = int(dollar_risk // risk_per_share) if risk_per_share > 0 else 0
        buying_power = shares * entry

        st.metric("Recommended Shares", f"{shares:,}")
        st.write(f"Risk/share: **${risk_per_share:.2f}**")
        st.write(f"Dollar risk: **${dollar_risk:.2f}**")
        st.write(f"1R target: **${target_1r:.2f}**")
        st.write(f"2R target: **${target_2r:.2f}**")
        st.write(f"Buying power: **${buying_power:,.2f}**")

    st.subheader("Pre-Trade Checklist")
    direction_alignment = (
        "bullish" in direction_ai["bias"].lower()
        if trade_side == "Long"
        else "bearish" in direction_ai["bias"].lower()
    )
    correct_stop = entry > stop if trade_side == "Long" else stop > entry
    target_valid = target_2r > entry if trade_side == "Long" else target_2r < entry

    checklist_items = [
        ("Daily directional bias agrees with trade side", direction_alignment),
        ("Entry and stop are logically ordered", correct_stop),
        ("At least 2R target is defined", target_valid),
        ("Recent news and catalyst were reviewed", isinstance(news_frame, pd.DataFrame) and not news_frame.empty),
        ("Price action confirmed; not anticipating", False),
        ("Liquidity and spread are acceptable", False),
        ("Position size respects daily risk", shares > 0 and dollar_risk > 0),
        ("Invalidation level is written down", risk_per_share > 0),
    ]
    checked = []
    columns = st.columns(2)
    for idx, (label, suggested) in enumerate(checklist_items):
        with columns[idx % 2]:
            checked.append(st.checkbox(label, value=suggested, key=f"ai_plan_check_{ticker}_{trade_side}_{idx}"))

    completion = int(round(sum(checked) / len(checked) * 100))
    plan_grade = "A" if completion >= 88 else "B" if completion >= 75 else "C" if completion >= 60 else "NO TRADE"

    p1, p2, p3, p4, p5 = st.columns(5)
    p1.metric("Plan Completion", f"{completion}%")
    p2.metric("Plan Grade", plan_grade)
    p3.metric("Directional Bias", direction_ai["bias"])
    p4.metric("Directional Confidence", direction_ai["confidence"])
    p5.metric("Intraday Data", chart_mode)

    plan_frame = pd.DataFrame([{
        "ticker": ticker,
        "side": trade_side,
        "directional_bias": direction_ai["bias"],
        "directional_confidence": direction_ai["confidence"],
        "directional_score": direction_ai["score"],
        "three_session_change_pct": direction_ai["three_day_change"],
        "five_session_change_pct": direction_ai["five_day_change"],
        "news_tone": direction_ai["news_tone"],
        "recent_support": direction_ai["support"],
        "recent_resistance": direction_ai["resistance"],
        "entry": entry,
        "stop": stop,
        "target_1r": target_1r,
        "target_2r": target_2r,
        "shares": shares,
        "dollar_risk": dollar_risk,
        "plan_grade": plan_grade,
        "daily_data_mode": daily_mode,
        "intraday_data_mode": chart_mode,
    }])
    st.download_button(
        "Download AI Trade Plan",
        plan_frame.to_csv(index=False),
        f"{ticker}_ai_trade_plan.csv",
        mime="text/csv",
    )

    if plan_grade == "A" and direction_alignment:
        st.success("The plan and directional evidence are aligned. Wait for the actual trigger and honor the stop.")
    elif plan_grade == "A":
        st.warning("The plan is complete, but the selected trade side conflicts with the current directional bias.")
    else:
        st.warning("The plan is incomplete. Resolve unchecked items before considering an entry.")

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
    st.caption(
        "Dark professional scanner with setup readiness, extension risk, catalyst checks, "
        "position sizing, and daily risk controls."
    )

    current_journal = normalize_user_journal(st.session_state["user_trade_journal"])
    today_string = date.today().isoformat()
    today_trades = current_journal[
        current_journal["date"].astype(str) == today_string
    ].copy()
    today_pnl = float(pd.to_numeric(today_trades["pnl"], errors="coerce").fillna(0).sum())

    st.markdown('<div class="terminal-panel-title">DAILY RISK GUARD</div>', unsafe_allow_html=True)
    rg1, rg2, rg3, rg4, rg5 = st.columns(5)
    with rg1:
        scanner_account = st.number_input(
            "Account Size",
            min_value=0.0,
            value=10000.0,
            step=500.0,
            key="scanner_account_size",
        )
    with rg2:
        scanner_risk_pct = st.number_input(
            "Risk / Trade %",
            min_value=0.05,
            max_value=5.0,
            value=0.50,
            step=0.05,
            key="scanner_risk_pct",
        )
    with rg3:
        daily_loss_limit = st.number_input(
            "Daily Loss Limit",
            min_value=25.0,
            value=200.0,
            step=25.0,
            key="scanner_daily_loss_limit",
        )
    with rg4:
        max_daily_trades = st.number_input(
            "Max Daily Trades",
            min_value=1,
            value=6,
            step=1,
            key="scanner_max_daily_trades",
        )
    with rg5:
        st.metric("Today's P/L", f"${today_pnl:,.2f}", f"{len(today_trades)} trades")

    loss_lock = today_pnl <= -abs(float(daily_loss_limit))
    trade_count_lock = len(today_trades) >= int(max_daily_trades)
    risk_locked = loss_lock or trade_count_lock

    if risk_locked:
        reason = (
            "daily loss limit reached"
            if loss_lock
            else "maximum daily trade count reached"
        )
        st.error(
            f"RISK LOCK ACTIVE — {reason}. The scanner remains visible, but suggested position size is set to zero."
        )
    else:
        remaining_loss_room = max(0.0, float(daily_loss_limit) + today_pnl)
        remaining_trades = max(0, int(max_daily_trades) - len(today_trades))
        st.success(
            f"Risk guard clear · ${remaining_loss_room:,.2f} remaining before the loss lock · "
            f"{remaining_trades} trades remaining."
        )

    market_regime = scanner_market_regime(FINNHUB_KEY)
    mr1, mr2, mr3, mr4 = st.columns([1.2, 1, 1, 3])
    mr1.metric("Market Regime", market_regime["label"])
    mr2.metric("SPY", f'{market_regime["spy"]:+.2f}%' if market_regime["spy"] is not None else "—")
    mr3.metric("QQQ", f'{market_regime["qqq"]:+.2f}%' if market_regime["qqq"] is not None else "—")
    mr4.info(market_regime["note"])

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
            ["Custom", "Under $10", "Under $20", "Low Float", "Ready Only", "Catalyst Only"],
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
            min_quality_default = 70 if preset == "Ready Only" else 45
            min_quality = st.slider("Min Quality", 0, 100, min_quality_default)

        f7, f8, f9, f10, f11, f12 = st.columns(6)
        with f7:
            readiness_filter = st.selectbox(
                "Decision",
                ["All", "READY", "WAIT", "AVOID"],
                index=1 if preset == "Ready Only" else 0,
            )
        with f8:
            risk_filter = st.selectbox("Risk", ["All", "LOW", "MODERATE", "HIGH"])
        with f9:
            catalyst_only = st.checkbox("Catalyst only", value=preset == "Catalyst Only")
        with f10:
            green_only = st.checkbox("Positive movers only")
        with f11:
            close_to_hod_only = st.checkbox("Within 3% of HOD")
        with f12:
            first_pullback_only = st.checkbox("First Pullback only")

    base_frame = scanner_view_frame(scanner_name).copy()
    frame = base_frame.copy()

    numeric_filters = {
        "price": pd.to_numeric(frame["price"], errors="coerce"),
        "float_m": pd.to_numeric(frame["float_m"], errors="coerce"),
        "relative_volume": pd.to_numeric(frame["relative_volume"], errors="coerce"),
        "gap_pct": pd.to_numeric(frame["gap_pct"], errors="coerce"),
        "momentum_quality": pd.to_numeric(frame["momentum_quality"], errors="coerce"),
        "day_change_pct": pd.to_numeric(frame["day_change_pct"], errors="coerce"),
        "distance_to_hod_pct": pd.to_numeric(frame["distance_to_hod_pct"], errors="coerce"),
    }
    frame = frame[
        numeric_filters["price"].between(min_price, max_price, inclusive="both")
        & (numeric_filters["float_m"] <= max_float)
        & (numeric_filters["relative_volume"] >= min_rvol)
        & (numeric_filters["gap_pct"] >= min_gap)
        & (numeric_filters["momentum_quality"] >= min_quality)
    ].copy()

    if readiness_filter != "All":
        frame = frame[frame["readiness"].astype(str) == readiness_filter]
    if risk_filter != "All":
        frame = frame[frame["risk_level"].astype(str) == risk_filter]
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

    ready_count = int((frame["readiness"] == "READY").sum()) if not frame.empty else 0
    wait_count = int((frame["readiness"] == "WAIT").sum()) if not frame.empty else 0
    avoid_count = int((frame["readiness"] == "AVOID").sum()) if not frame.empty else 0
    high_risk_count = int((frame["risk_level"] == "HIGH").sum()) if not frame.empty else 0
    average_quality = (
        float(pd.to_numeric(frame["momentum_quality"], errors="coerce").mean())
        if not frame.empty else 0.0
    )
    strongest = frame.iloc[0]["ticker"] if not frame.empty else "—"

    sm1, sm2, sm3, sm4, sm5, sm6 = st.columns(6)
    sm1.metric("Matches", len(frame))
    sm2.metric("Ready", ready_count)
    sm3.metric("Wait", wait_count)
    sm4.metric("Avoid", avoid_count)
    sm5.metric("Average Quality", f"{average_quality:.0f}/100")
    sm6.metric("Top Symbol", strongest)

    if high_risk_count:
        st.warning(f"{high_risk_count} displayed setup(s) carry HIGH structural risk.")

    st.markdown(
        f"""
        <div class="scanner-status-row">
          <span>{scanner_name.upper()}</span>
          <span>{preset.upper()}</span>
          <span>DECISION ENGINE: READY / WAIT / AVOID</span>
          <span>TRAINING-DERIVED SCANNER METRICS</span>
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
                key=f"dark_pro_scanner_{scanner_name}_{preset}",
            )
        except (ImportError, ModuleNotFoundError, ValueError, TypeError) as exc:
            st.caption(f"Color styling fallback: {type(exc).__name__}. Scanner data remains available.")
            fallback_styled = (
                display.style
                .set_properties(**{
                    "background-color": "#111b29",
                    "color": "#dce9f5",
                    "border-color": "#26384b",
                })
                .set_table_styles([{
                    "selector": "th",
                    "props": [
                        ("background-color", "#0b1725"),
                        ("color", "#bfe7ff"),
                        ("font-weight", "850"),
                    ],
                }])
            )
            event = st.dataframe(
                fallback_styled,
                use_container_width=True,
                hide_index=True,
                height=height_map[table_height],
                on_select="rerun",
                selection_mode="single-row",
                key=f"dark_pro_scanner_{scanner_name}_{preset}_plain",
            )

    selected_rows = event.selection.rows if event is not None and hasattr(event, "selection") else []
    if selected_rows and not frame.empty:
        position = int(selected_rows[0])
        if 0 <= position < len(frame):
            selected_symbol = str(frame.iloc[position]["ticker"])
            set_active_ticker(selected_symbol)
            st.session_state["scanner_last_selected"] = selected_symbol

    selected_symbol = st.session_state.get("scanner_last_selected", st.session_state["active_ticker"])
    selected_training = build_training_scanner_frame(market)
    selected_training = selected_training[
        selected_training["ticker"].astype(str) == selected_symbol
    ]

    if selected_symbol and not selected_training.empty:
        row = selected_training.iloc[0]
        payload = get_market_payload(selected_symbol, "5min")
        quote = payload.get("quote", {}) or {}
        profile = payload.get("profile", {}) or {}
        news_brief = scanner_news_brief(payload.get("news", pd.DataFrame()))

        decision = str(row["readiness"])
        decision_class = (
            "decision-ready"
            if decision == "READY"
            else "decision-wait"
            if decision == "WAIT"
            else "decision-avoid"
        )

        entry_value = float(pd.to_numeric(row.get("entry"), errors="coerce") or 0)
        stop_value = float(pd.to_numeric(row.get("stop"), errors="coerce") or 0)
        risk_per_share = abs(entry_value - stop_value)
        reference_price = float(quote.get("price", 0) or 0) or float(row.get("price", 0) or 0)

        if risk_per_share > 0 and entry_value > 0:
            trigger_distance_r = (reference_price - entry_value) / risk_per_share
            if trigger_distance_r >= 0.75:
                trigger_status = "CHASE RISK"
            elif trigger_distance_r >= 0:
                trigger_status = "TRIGGER ZONE"
            else:
                trigger_status = "BELOW TRIGGER"
        else:
            trigger_distance_r = None
            trigger_status = "UNAVAILABLE"

        dollar_risk = float(scanner_account) * (float(scanner_risk_pct) / 100)
        recommended_shares = (
            int(dollar_risk // risk_per_share)
            if risk_per_share > 0 and not risk_locked and decision != "AVOID"
            else 0
        )
        target_1r = (
            entry_value + risk_per_share if risk_per_share > 0 else None
        )
        target_2r = (
            entry_value + 2 * risk_per_share if risk_per_share > 0 else None
        )

        st.markdown('<div class="terminal-panel-title">SPIDER DECISION ENGINE</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="scanner-decision-card {decision_class}">
              <div class="decision-symbol">{selected_symbol}</div>
              <div class="decision-status">{decision}</div>
              <div class="decision-note">{row["decision_note"]}</div>
              <div class="decision-grid">
                <div><small>Momentum Quality</small><b>{int(row["momentum_quality"])}/100</b></div>
                <div><small>Risk</small><b>{row["risk_level"]} · {int(row["risk_score"])}/100</b></div>
                <div><small>Room to Resistance</small><b>{float(row["room_to_resistance_r"]):.2f}R</b></div>
                <div><small>Spread</small><b>{float(row["spread_pct"]):.2f}%</b></div>
                <div><small>Suggested Shares</small><b>{recommended_shares:,}</b></div>
                <div><small>Trigger Status</small><b>{trigger_status}</b></div>
                <div><small>News Read</small><b>{news_brief["tone"]}</b></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if trigger_status == "CHASE RISK":
            st.error(
                f"CHASE GUARD: the reference price is approximately {trigger_distance_r:.2f}R above the planned trigger. "
                "Wait for a new base or pullback instead of forcing the entry."
            )

        if market_regime["label"] == "RISK-OFF":
            st.warning("Broad-market alignment is RISK-OFF. Long momentum requires stronger stock-specific confirmation.")

        if decision == "READY" and not risk_locked and trigger_status != "CHASE RISK":
            st.success("READY means the evidence is aligned—not an automatic entry. Wait for the actual trigger and honor the stop.")
        elif decision == "WAIT":
            st.warning(f"WAIT: {row['primary_risk']}. Require confirmation before considering an entry.")
        else:
            st.error(f"AVOID: {row['primary_risk']}. Skipping weak or extended setups protects the account.")

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
            st.caption("Select another row to update the decision engine, charts, news, and position-size preview.")

        info_col, chart_col, ai_col = st.columns([1.15, 2.25, 1.25], gap="small")

        with info_col:
            st.markdown('<div class="terminal-panel-title">STOCK INTELLIGENCE</div>', unsafe_allow_html=True)
            st.metric(
                selected_symbol,
                f'${float(quote.get("price")):.2f}' if quote.get("price") else f'${float(row["price"]):.2f}',
                f'{float(quote.get("change_pct", 0)):+.2f}%' if quote else None,
            )
            st.write(f"**Company:** {profile.get('name') or '—'}")
            st.write(f"**Float:** {float(row['float_m']):.2f}M")
            st.write(f"**Gap:** {float(row['gap_pct']):.2f}%")
            st.write(f"**Daily RVOL:** {float(row['relative_volume']):.2f}")
            st.write(f"**5m RVOL:** {float(row['rvol_5m']):.2f}")
            st.write(f"**Above VWAP:** {'Yes' if bool(row['above_vwap']) else 'No'}")
            st.write(f"**Catalyst Quality:** {row['catalyst_quality']}")
            st.write(f"**Pullback Quality:** {row['pullback_quality']}")
            st.write(f"**Setup:** {row['setup_status']}")

            st.markdown('<div class="terminal-panel-title">NEWS RISK FILTER</div>', unsafe_allow_html=True)
            st.write(f"**Tone:** {news_brief['tone']}")
            if news_brief["positive_terms"]:
                st.write("**Positive terms:** " + ", ".join(news_brief["positive_terms"]))
            if news_brief["risk_terms"]:
                st.error("Risk terms: " + ", ".join(news_brief["risk_terms"]))
            else:
                st.caption(news_brief["warning"])

        with chart_col:
            st.markdown('<div class="terminal-panel-title">SYNCHRONIZED CHARTS</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                mini_candlestick_chart(selected_symbol, "5min", 355, f"v122_scanner_5m_{selected_symbol}")
            with c2:
                mini_candlestick_chart(selected_symbol, "1min", 355, f"v122_scanner_1m_{selected_symbol}")
            mini_candlestick_chart(selected_symbol, "15min", 315, f"v122_scanner_15m_{selected_symbol}")

        with ai_col:
            st.markdown('<div class="terminal-panel-title">QUICK TRADE PLAN</div>', unsafe_allow_html=True)
            q1, q2 = st.columns(2)
            q1.metric("Entry", f"${entry_value:.2f}" if entry_value else "—")
            q2.metric("Stop", f"${stop_value:.2f}" if stop_value else "—")
            q3, q4 = st.columns(2)
            q3.metric("1R", f"${target_1r:.2f}" if target_1r else "—")
            q4.metric("2R", f"${target_2r:.2f}" if target_2r else "—")
            st.metric("Position Size", f"{recommended_shares:,} shares")
            st.write(f"**Dollar risk:** ${dollar_risk:,.2f}")
            st.write(f"**Risk/share:** ${risk_per_share:.2f}")
            st.write(f"**Coach note:** {row['coach_note']}")
            st.write(f"**Primary warning:** {row['primary_risk']}")

            if risk_locked:
                st.error("Position sizing disabled by the daily risk lock.")
            elif decision == "AVOID":
                st.error("Position sizing disabled because the decision engine says AVOID.")
            elif recommended_shares <= 0:
                st.warning("A valid entry and stop are required for position sizing.")

        recent_news = compact_news_view(payload.get("news"), 6)
        if not recent_news.empty:
            with st.expander("Recent company headlines", expanded=False):
                st.dataframe(
                    recent_news,
                    use_container_width=True,
                    hide_index=True,
                    column_config={"url": st.column_config.LinkColumn("Article")},
                )

    elif selected_symbol:
        st.info(f"{selected_symbol} is not part of the bundled scanner dataset, but it remains linked across the app.")

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
