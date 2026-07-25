from pathlib import Path
from datetime import datetime
import math
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.data import load_market, load_journal, load_news, load_indices, load_alerts, append_journal, replace_journal
from core.engine import scan_setups, component_scores, build_trade_plan, setup_explanation, replay_grade, coach_trade
from core.risk import calculate_position_size, risk_lock_status
from core.analytics import summarize_journal, grouped_stats
from core.tradingview import chart_url, load_webhook_events, webhook_summary

BASE_DIR = Path(__file__).resolve().parent
st.set_page_config(page_title="Spiderboys Trading Pro", page_icon="🕷️", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
:root{
  --bg:#070a12;--surface:#101625;--surface2:#151d30;--line:rgba(148,163,184,.18);
  --purple:#8b5cf6;--blue:#38bdf8;--green:#22c55e;--amber:#f59e0b;--red:#fb7185;--text:#f8fafc;--muted:#9aa9bd;
}
.stApp{background:
 radial-gradient(circle at 12% 5%,rgba(139,92,246,.16),transparent 27%),
 radial-gradient(circle at 88% 8%,rgba(56,189,248,.13),transparent 24%),
 linear-gradient(180deg,#080b13 0%,#070a12 100%);color:var(--text)}
.block-container{padding-top:1.1rem;max-width:1700px;padding-bottom:3rem}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#11182a 0%,#0a0f1b 100%);border-right:1px solid var(--line)}
[data-testid="stSidebar"] .stRadio label{padding:.43rem .55rem;border-radius:10px;margin:.08rem 0;transition:.18s ease}
[data-testid="stSidebar"] .stRadio label:hover{background:rgba(139,92,246,.12)}
.brand-shell{padding:1rem 1rem .85rem;border-radius:18px;background:linear-gradient(135deg,rgba(139,92,246,.22),rgba(56,189,248,.12));border:1px solid rgba(139,92,246,.33);box-shadow:0 16px 40px rgba(0,0,0,.22);margin-bottom:1rem}
.brand-mark{width:44px;height:44px;display:flex;align-items:center;justify-content:center;border-radius:14px;background:linear-gradient(135deg,var(--purple),#ec4899);font-size:1.45rem;box-shadow:0 10px 24px rgba(139,92,246,.32)}
.brand-title{font-size:1.12rem;font-weight:800;line-height:1.1;margin-top:.7rem}.brand-sub{color:#b8c4d5;font-size:.78rem;margin-top:.2rem}
.hero{position:relative;overflow:hidden;padding:27px 28px;border:1px solid rgba(139,92,246,.28);border-radius:24px;background:linear-gradient(135deg,rgba(28,38,65,.96),rgba(12,18,31,.97) 58%,rgba(34,19,57,.94));margin-bottom:18px;box-shadow:0 22px 60px rgba(0,0,0,.24)}
.hero:after{content:"";position:absolute;width:260px;height:260px;right:-80px;top:-110px;border-radius:50%;background:radial-gradient(circle,rgba(56,189,248,.30),transparent 65%)}
.hero h1{margin:0;font-size:2.28rem;letter-spacing:-.035em}.hero p{margin:.45rem 0 0;color:#b7c4d8;font-size:1rem}.eyebrow{font-size:.72rem;letter-spacing:.15em;color:#c4b5fd;font-weight:800;margin-bottom:.35rem}
.page-head{padding:.2rem 0 .65rem}.page-head h2{font-size:1.65rem;margin:0;letter-spacing:-.025em}.page-head p{color:var(--muted);margin:.25rem 0 0}
.panel,.app-card{border:1px solid var(--line);border-radius:18px;padding:16px;background:linear-gradient(145deg,rgba(21,29,48,.94),rgba(13,19,33,.96));box-shadow:0 12px 30px rgba(0,0,0,.16)}
.good{color:#4ade80}.warn{color:#fbbf24}.bad{color:#fb7185}.small{font-size:.82rem;color:var(--muted)}
[data-testid="stMetric"]{border:1px solid var(--line);background:linear-gradient(145deg,rgba(22,31,52,.92),rgba(13,19,33,.96));padding:.9rem 1rem;border-radius:16px;box-shadow:0 10px 24px rgba(0,0,0,.13)}
[data-testid="stMetricLabel"]{color:#9eb0c8}[data-testid="stMetricValue"]{font-size:1.52rem;font-weight:800;letter-spacing:-.03em}
.stButton>button,.stLinkButton>a,.stDownloadButton>button{border-radius:12px!important;border:1px solid rgba(139,92,246,.40)!important;background:linear-gradient(135deg,#7c3aed,#2563eb)!important;color:white!important;font-weight:700!important;box-shadow:0 8px 22px rgba(37,99,235,.20)!important;transition:.18s ease!important}
.stButton>button:hover,.stLinkButton>a:hover,.stDownloadButton>button:hover{transform:translateY(-1px);filter:brightness(1.08)}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:16px;overflow:hidden;background:rgba(15,23,42,.68)}
[data-baseweb="select"]>div,[data-baseweb="input"]>div,.stNumberInput input,.stTextInput input,.stTextArea textarea{border-radius:11px!important}
.stTabs [data-baseweb="tab-list"]{gap:.35rem}.stTabs [data-baseweb="tab"]{border-radius:10px;padding:.45rem .85rem;background:rgba(30,41,59,.55)}
[data-testid="stAlert"]{border-radius:14px}
hr{border-color:var(--line)}
</style>""", unsafe_allow_html=True)

market=load_market(BASE_DIR); news=load_news(BASE_DIR); indices=load_indices(BASE_DIR); alerts=load_alerts(BASE_DIR)
if market.empty:
    st.error("Market training data is missing. Re-upload the complete ZIP contents, including the data folder."); st.stop()

with st.sidebar:
    st.markdown('<div class="brand-shell"><div class="brand-mark">🕷️</div><div class="brand-title">Spiderboys Trading</div><div class="brand-sub">PRO TERMINAL • v6.2</div></div>',unsafe_allow_html=True)
    nav_items={
        "🏠  Command Center":"Command Center","⚡  Elite Scanner":"Elite Scanner","📈  Charts & TradingView":"Charts & TradingView",
        "🎯  Trade Planner":"Trade Planner","🛡️  Risk Command":"Risk Command","📓  Trading Journal":"Trading Journal",
        "📊  Performance":"Performance","🎬  Replay Academy":"Replay Academy","🤖  AI Coach":"AI Coach",
        "📡  TradingView Radar":"TradingView Radar","⚙️  Settings & Backup":"Settings & Backup"}
    selected=st.radio("Workspace",list(nav_items.keys()),label_visibility="collapsed")
    page=nav_items[selected]
    st.divider()
    account=st.number_input("Account size",min_value=100.0,value=25000.0,step=500.0)
    risk_pct=st.number_input("Risk per trade (%)",min_value=.05,max_value=5.0,value=.5,step=.05)
    daily_loss_pct=st.number_input("Daily stop (%)",min_value=.1,max_value=10.0,value=2.0,step=.1)
    buying_power=st.number_input("Buying power",min_value=100.0,value=25000.0,step=500.0)
    st.divider(); st.success("DEMO / TRAINING MODE")
    st.caption("The included market feed is simulated. TradingView links open real charts; no broker orders are sent.")

st.markdown('<div class="hero"><div class="eyebrow">LIVE-READY MOMENTUM WORKSTATION</div><h1>Spiderboys Trading Pro</h1><p>Find momentum faster. Plan risk precisely. Build a measurable trading edge.</p></div>',unsafe_allow_html=True)

@st.cache_data(ttl=20)
def full_scan(df):
    return scan_setups(df,1,30,0,200,0,0,0,5,False,False,"All")

scan_all=full_scan(market)

def page_header(title, subtitle):
    st.markdown(f'<div class="page-head"><h2>{title}</h2><p>{subtitle}</p></div>',unsafe_allow_html=True)

def tv_button(ticker,label=None,exchange="NASDAQ"):
    st.link_button(label or f"Open {ticker} in TradingView",chart_url(ticker,exchange),use_container_width=True)

def draw_chart(ticker,height=520,reveal=None):
    g=market[market.ticker==ticker].sort_values("datetime").copy()
    if reveal is not None: g=g.iloc[:reveal]
    fig=go.Figure()
    fig.add_trace(go.Candlestick(x=g.datetime,open=g.open,high=g.high,low=g.low,close=g.close,name=ticker))
    fig.add_trace(go.Scatter(x=g.datetime,y=g.vwap,name="VWAP",line=dict(width=2.4,color="#38bdf8")))
    fig.add_trace(go.Scatter(x=g.datetime,y=g.ema9,name="EMA 9",line=dict(width=1.6,color="#a78bfa")))
    fig.add_trace(go.Scatter(x=g.datetime,y=g.ema20,name="EMA 20",line=dict(width=1.6,color="#f59e0b")))
    last=market[market.ticker==ticker].sort_values("datetime").iloc[-1]
    for y,label,dash in [(last.premarket_high,"PM High","dash"),(last.previous_day_high,"PD High","dot"),(last.entry,"Entry","dash"),(last.stop,"Stop","dot")]:
        fig.add_hline(y=y,line_dash=dash,annotation_text=label)
    fig.update_layout(height=height,margin=dict(l=8,r=8,t=30,b=8),xaxis_rangeslider_visible=False,legend_orientation="h",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#0d1422",font=dict(color="#dce6f2"),xaxis=dict(gridcolor="rgba(148,163,184,.10)"),yaxis=dict(gridcolor="rgba(148,163,184,.10)"))
    st.plotly_chart(fig,use_container_width=True)

def scanner_table(df):
    cols=["ticker","price","gap_pct","float_m","premarket_volume","relative_volume","spread_pct","elite_score","elite_grade","tradability","setup_status","entry","stop","target_2r"]
    show=df[cols].copy()
    st.dataframe(show,use_container_width=True,hide_index=True,column_config={"price":st.column_config.NumberColumn("Price",format="$%.2f"),"gap_pct":st.column_config.NumberColumn("Gap",format="%.1f%%"),"premarket_volume":st.column_config.NumberColumn("PM Volume",format="%d"),"relative_volume":st.column_config.NumberColumn("RVOL",format="%.1fx"),"spread_pct":st.column_config.NumberColumn("Spread",format="%.2f%%"),"elite_score":st.column_config.ProgressColumn("Elite Score",min_value=0,max_value=100),"entry":st.column_config.NumberColumn(format="$%.2f"),"stop":st.column_config.NumberColumn(format="$%.2f"),"target_2r":st.column_config.NumberColumn("2R Target",format="$%.2f")})

if page=="Command Center":
    journal=load_journal(BASE_DIR); stats=summarize_journal(journal); top=scan_all.iloc[0]; qualified=scan_all[scan_all.elite_score>=74]
    bias=indices.iloc[-1].market_bias if not indices.empty else "Unknown"
    cols=st.columns(6)
    for c,(label,value) in zip(cols,[("Top Setup",top.ticker),("Elite Score",f"{top.elite_score}/100"),("Qualified",len(qualified)),("Market Bias",bias),("Win Rate",f"{stats['win_rate']:.1f}%"),("Daily Stop",f"${account*daily_loss_pct/100:,.0f}")]): c.metric(label,value)
    st.subheader("Priority Watchlist"); scanner_table(scan_all.head(8))
    left,right=st.columns([2.1,1])
    with left: st.subheader(f"Featured Setup — {top.ticker}"); draw_chart(top.ticker,470)
    with right:
        plan=build_trade_plan(top,account,risk_pct,buying_power); pos,risks=setup_explanation(top)
        st.subheader("Execution Brief"); st.metric("Grade",top.elite_grade,top.tradability); st.write(f"**Catalyst:** {top.catalyst}"); st.write(f"**Entry / Stop:** ${top.entry:.2f} / ${top.stop:.2f}"); st.write(f"**Shares:** {plan['shares']:,}"); st.write(f"**Planned loss:** ${plan['planned_loss']:,.2f}"); st.write(f"**2R potential:** ${plan['potential_2r']:,.2f}")
        if pos: st.success("Strengths: "+", ".join(pos))
        if risks: st.warning("Risks: "+", ".join(risks))
        st.info(top.coach_note); tv_button(top.ticker)
    st.subheader("Catalyst Feed"); st.dataframe(news,use_container_width=True,hide_index=True)

elif page=="Elite Scanner":
    page_header("⚡ Elite Momentum Scanner","Filter, rank and inspect the strongest momentum candidates.")
    with st.expander("Scanner Controls",expanded=True):
        a,b,c,d=st.columns(4); min_price=a.number_input("Minimum price",value=1.0); max_price=b.number_input("Maximum price",value=20.0); min_gap=c.slider("Minimum gap %",0,100,10); max_float=d.slider("Maximum float (M)",5,200,75)
        a,b,c,d=st.columns(4); min_pm=a.number_input("Minimum PM volume",value=250000,step=100000); min_rvol=b.slider("Minimum RVOL",0.0,15.0,1.5,.5); min_score=c.slider("Minimum score",0,100,65); max_spread=d.slider("Maximum spread %",.1,5.0,1.0,.1)
        a,b,c=st.columns(3); require_news=a.checkbox("Require catalyst",True); require_vwap=b.checkbox("Require above VWAP",False); setup=c.selectbox("Setup filter",["All","Pullback","Breakout","VWAP","Reclaim"])
    scan=scan_setups(market,min_price,max_price,min_gap,max_float,min_pm,min_rvol,min_score,max_spread,require_news,require_vwap,setup)
    if scan.empty: st.warning("No candidates match those rules. Loosen one filter at a time.")
    else:
        scanner_table(scan); st.download_button("Download scanner CSV",scan.to_csv(index=False),"spiderboys_flagship_scan.csv","text/csv")
        ticker=st.selectbox("Inspect candidate",scan.ticker.tolist()); row=scan[scan.ticker==ticker].iloc[0]
        c=st.columns(5)
        for x,(a,b) in zip(c,[("Elite Score",row.elite_score),("Grade",row.elite_grade),("RVOL",f"{row.relative_volume:.1f}x"),("Float",f"{row.float_m:.1f}M"),("Status",row.tradability)]): x.metric(a,b)
        tv_button(ticker); draw_chart(ticker); st.subheader("Score Breakdown"); st.dataframe(pd.DataFrame([component_scores(row)]),use_container_width=True,hide_index=True)

elif page=="Charts & TradingView":
    page_header("📈 Charts & TradingView","Analyze structure here, then launch the live ticker in TradingView.")
    ticker=st.selectbox("Ticker",sorted(market.ticker.unique())); tv_button(ticker); draw_chart(ticker,650)
    row=scan_all[scan_all.ticker==ticker].iloc[0]; c=st.columns(6)
    vals=[("PM High",f"${market[market.ticker==ticker].iloc[-1].premarket_high:.2f}"),("Entry",f"${row.entry:.2f}"),("Stop",f"${row.stop:.2f}"),("1R",f"${row.target_1r:.2f}"),("2R",f"${row.target_2r:.2f}"),("Score",row.elite_score)]
    for x,(a,b) in zip(c,vals): x.metric(a,b)

elif page=="Trade Planner":
    page_header("🎯 Risk-First Trade Planner","Build the trade around defined risk—not emotion.")
    a,b=st.columns(2)
    with a:
        ticker=st.text_input("Ticker","SOUN").upper().strip(); side=st.selectbox("Side",["Long","Short"]); setup=st.selectbox("Setup",["First Pullback","HOD Break","ORB","VWAP Reclaim","Red-to-Green","Other"]); entry=st.number_input("Entry",value=5.50,step=.01); stop=st.number_input("Stop",value=5.30,step=.01); target=st.number_input("Target",value=6.00,step=.01)
    with b:
        sizing=calculate_position_size(account,risk_pct,entry,stop); shares=min(sizing["shares"],int(buying_power//entry) if entry>0 else 0); risk=abs(entry-stop); reward=abs(target-entry); rr=reward/risk if risk else 0
        for label,value in [("Maximum shares",f"{shares:,}"),("Position value",f"${shares*entry:,.2f}"),("Planned loss",f"${shares*risk:,.2f}"),("Potential reward",f"${shares*reward:,.2f}"),("Reward / Risk",f"{rr:.2f}R")]: st.metric(label,value)
    st.subheader("Six-Point Gate"); cols=st.columns(3); checks=[cols[0].checkbox("Verified catalyst"),cols[0].checkbox("RVOL ≥ 2x"),cols[1].checkbox("Above VWAP"),cols[1].checkbox("Clean technical stop"),cols[2].checkbox("Acceptable spread"),cols[2].checkbox("Not extended")]; passed=sum(checks); st.progress(passed/6)
    if passed==6 and rr>=2: st.success("A-quality plan. Execute only on the trigger.")
    elif passed>=4: st.warning("Watch only. Wait for remaining confirmation.")
    else: st.error("No trade.")
    if ticker: tv_button(ticker)

elif page=="Risk Command":
    page_header("🛡️ Risk Command Center","Know when to size down, stop, or lock the platform."); max_loss=account*daily_loss_pct/100
    a,b,c=st.columns(3); realized=a.number_input("Realized P/L today",value=0.0,step=25.0); losses=b.number_input("Consecutive losses",min_value=0,value=0); open_risk=c.number_input("Current open risk",min_value=0.0,value=0.0,step=25.0)
    status=risk_lock_status(max_loss,realized,losses,open_risk); c=st.columns(4)
    for x,(a,b) in zip(c,[("Daily loss limit",f"${max_loss:,.2f}"),("Risk per trade",f"${account*risk_pct/100:,.2f}"),("Open risk",f"${open_risk:,.2f}"),("Trading lock","ON" if status["locked"] else "OFF")]): x.metric(a,b)
    (st.error if status["locked"] else st.warning if status["warning"] else st.success)(status["message"])

elif page=="Trading Journal":
    page_header("📓 Trading Journal","Record execution, behavior and lessons from every trade.")
    with st.expander("Add completed trade",expanded=True):
        c=st.columns(5); ticker=c[0].text_input("Ticker","SOUN",key="j_ticker").upper().strip(); side=c[1].selectbox("Side",["Long","Short"]); setup=c[2].selectbox("Setup",["First Pullback","HOD Break","ORB","VWAP Reclaim","Red-to-Green","Other"]); entry=c[3].number_input("Entry",value=5.50,step=.01,key="j_entry"); exitp=c[4].number_input("Exit",value=5.80,step=.01,key="j_exit")
        c=st.columns(5); stop=c[0].number_input("Initial stop",value=5.30,step=.01,key="j_stop"); shares=c[1].number_input("Shares",min_value=1,value=500); emotion=c[2].selectbox("Emotion",["Calm","Focused","FOMO","Revenge","Tired","Overconfident"]); grade=c[3].selectbox("Execution grade",["A","B","C","F"]); catalyst=c[4].text_input("Catalyst")
        c=st.columns(3); followed=c[0].checkbox("Followed plan",True); chased=c[1].checkbox("Chased entry"); moved=c[2].checkbox("Moved stop farther away")
        mistake=st.text_input("Primary mistake"); lesson=st.text_area("Lesson / next-action rule"); screenshot=st.text_input("TradingView chart or screenshot link")
        if ticker: tv_button(ticker,label="Open ticker in TradingView")
        if st.button("Save completed trade",type="primary"):
            direction=1 if side=="Long" else -1; pnl=(exitp-entry)*shares*direction; dollar_risk=abs(entry-stop)*shares; r=pnl/dollar_risk if dollar_risk else 0; now=datetime.now()
            append_journal(BASE_DIR,{"date":now.date().isoformat(),"weekday":now.strftime("%A"),"ticker":ticker,"side":side,"setup":setup,"entry":entry,"exit":exitp,"stop":stop,"shares":shares,"pnl":pnl,"r_multiple":r,"win":pnl>0,"execution_grade":grade,"emotion":emotion,"time_bucket":now.strftime("%H:%M"),"catalyst":catalyst,"followed_plan":followed,"chased":chased,"moved_stop":moved,"mistake":mistake,"lesson":lesson,"screenshot_url":screenshot})
            st.success(f"Saved: ${pnl:,.2f} ({r:.2f}R)")
    journal=load_journal(BASE_DIR); st.dataframe(journal,use_container_width=True,hide_index=True); st.download_button("Download journal backup",journal.to_csv(index=False),"spiderboys_journal_backup.csv","text/csv")

elif page=="Performance":
    page_header("📊 Performance Analytics","Turn your trade history into actionable patterns."); journal=load_journal(BASE_DIR); stats=summarize_journal(journal); c=st.columns(6)
    for x,(a,b) in zip(c,[("Trades",stats["trades"]),("Net P/L",f"${stats['net_pnl']:,.2f}"),("Win Rate",f"{stats['win_rate']:.1f}%"),("Expectancy",f"{stats['expectancy_r']:.2f}R"),("Profit Factor",f"{stats['profit_factor']:.2f}"),("Compliance",f"{stats['rule_compliance']:.0f}%")]): x.metric(a,b)
    if not journal.empty:
        j=journal.copy(); j["date"]=pd.to_datetime(j.date,errors="coerce"); j["pnl"]=pd.to_numeric(j.pnl,errors="coerce").fillna(0); j["Equity"]=j.pnl.cumsum(); fig=go.Figure(go.Scatter(x=j.date,y=j.Equity,mode="lines+markers")); fig.update_layout(height=410,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#0d1422",font=dict(color="#dce6f2"),xaxis=dict(gridcolor="rgba(148,163,184,.10)"),yaxis=dict(gridcolor="rgba(148,163,184,.10)"),title="Equity Curve"); st.plotly_chart(fig,use_container_width=True)
        a,b=st.columns(2); a.dataframe(grouped_stats(journal,"setup"),use_container_width=True,hide_index=True); b.dataframe(grouped_stats(journal,"emotion"),use_container_width=True,hide_index=True)
    st.info(stats["coach_summary"])

elif page=="Replay Academy":
    page_header("🎬 Replay Academy","Practice decision-making candle by candle without risking capital."); ticker=st.selectbox("Replay ticker",sorted(market.ticker.unique())); g=market[market.ticker==ticker].sort_values("datetime"); reveal=st.slider("Reveal candles",10,max(10,len(g)-1),min(25,max(10,len(g)-1))); draw_chart(ticker,530,reveal)
    c=st.columns(3); decision=c[0].selectbox("Decision",["Long","No Trade"]); current=float(g.iloc[min(reveal-1,len(g)-1)].close); entry=c[1].number_input("Replay entry",value=current,step=.01); stop=c[2].number_input("Replay stop",value=current*.97,step=.01)
    if st.button("Grade decision"):
        out=replay_grade(g,reveal,decision,entry,stop); st.metric("Result",out["result"]); st.write(out["message"]); st.write(f"MFE: {out['mfe_r']:.2f}R • MAE: {out['mae_r']:.2f}R"); st.info(out["coach_review"])

elif page=="AI Coach":
    page_header("🤖 AI Execution Coach","Grade rule-following and identify the next behavior to improve."); c=st.columns(4); ticker=c[0].text_input("Ticker","SOUN",key="coach_ticker"); setup=c[1].selectbox("Setup",["First Pullback","HOD Break","ORB","VWAP Reclaim"],key="coach_setup"); emotion=c[2].selectbox("State",["Calm","Focused","FOMO","Revenge","Tired"],key="coach_emotion"); shares=c[3].number_input("Shares",1,100000,500,key="coach_shares")
    c=st.columns(3); entry=c[0].number_input("Entry price",value=5.50,step=.01,key="coach_entry"); stop=c[1].number_input("Stop price",value=5.30,step=.01,key="coach_stop"); exitp=c[2].number_input("Exit price",value=5.80,step=.01,key="coach_exit")
    c=st.columns(4); followed=c[0].checkbox("Followed plan",True,key="coach_followed"); chased=c[1].checkbox("Chased entry",key="coach_chased"); averaged=c[2].checkbox("Averaged down",key="coach_averaged"); moved=c[3].checkbox("Moved stop",key="coach_moved")
    if st.button("Coach this trade",type="primary"):
        out=coach_trade(ticker,setup,emotion,entry,stop,exitp,shares,followed,chased,averaged,moved); c=st.columns(3); c[0].metric("Execution grade",out["grade"]); c[1].metric("Rule score",out["rule_score"]); c[2].metric("Result",f"{out['r_multiple']:.2f}R"); [st.write("• "+note) for note in out["feedback"]]; st.success(out["next_action"])

elif page=="TradingView Radar":
    page_header("📡 TradingView Radar","Send your best watchlist into a focused TradingView monitoring workflow.")
    st.success("Use `tradingview/Spiderboys_Watchlist_Radar.pine` in TradingView's Pine Editor.")
    left,right=st.columns(2)
    with left:
        st.markdown("**Radar evaluates**\n- Price versus VWAP\n- EMA 9 versus EMA 20\n- Relative volume\n- RSI momentum\n- VWAP reclaim and volume expansion")
    with right:
        st.markdown("**Install**\n1. Copy the Pine script.\n2. Paste into Pine Editor.\n3. Add to chart.\n4. Set your 12 symbols.\n5. Create an alert using **Any alert() function call**.")
    watch=scan_all.head(12)[["ticker","elite_score","tradability","entry","stop","target_2r"]].copy(); watch["TradingView symbol"]="NASDAQ:"+watch.ticker.astype(str); st.dataframe(watch,use_container_width=True,hide_index=True); st.download_button("Download radar watchlist",watch.to_csv(index=False),"spiderboys_radar_watchlist.csv","text/csv")

else:
    page_header("⚙️ Settings & Backup","Manage deployment status, journal recovery and optional integrations.")
    st.subheader("Streamlit deployment status"); st.success("This package uses `app.py` as the only Streamlit entry point. No API keys are required for demo mode.")
    st.markdown("**Main file path:** `app.py`  \n**Python dependencies:** Streamlit, pandas, NumPy and Plotly  \n**TradingView scripts:** optional and stored in the `tradingview` folder")
    st.subheader("Restore a journal backup")
    uploaded=st.file_uploader("Upload a prior Spiderboys journal CSV",type=["csv"])
    if uploaded is not None and st.button("Replace journal with uploaded backup"):
        try: restored=replace_journal(BASE_DIR,uploaded); st.success(f"Restored {len(restored)} journal records.")
        except Exception as exc: st.error(f"Could not restore the journal: {exc}")
    st.warning("Streamlit Community Cloud storage can reset during redeployments. Download a journal backup regularly or connect a cloud database in a future live release.")
    st.subheader("Optional TradingView webhook bridge")
    st.info("The webhook receiver is intentionally not started by Streamlit. Deploy it separately only when you are ready to receive TradingView alerts through a public HTTPS endpoint.")
