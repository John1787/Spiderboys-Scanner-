import pandas as pd
from core.risk import calculate_position_size

def scan_setups(market,min_gap=20,max_float=50,min_pm=500000,min_rvol=2,min_score=65,require_catalyst=True,require_vwap=True):
    latest = market.sort_values("datetime").groupby("ticker").tail(1).copy()
    cols = [
        "ticker","close","gap_pct","float_m","premarket_volume","relative_volume",
        "above_vwap","catalyst","catalyst_quality","pullback_quality","spider_score",
        "quality","setup_status","entry","stop","target_1r","target_2r",
        "room_to_resistance_r","coach_note","spread_pct"
    ]
    latest = latest[cols].rename(columns={"close":"price"})
    mask = (
        (latest["gap_pct"]>=min_gap)&(latest["float_m"]<=max_float)&
        (latest["premarket_volume"]>=min_pm)&(latest["relative_volume"]>=min_rvol)&
        (latest["spider_score"]>=min_score)
    )
    if require_catalyst:
        mask &= latest["catalyst"].astype(str).str.len()>0
    if require_vwap:
        mask &= latest["above_vwap"]
    return latest[mask].sort_values(["spider_score","relative_volume"],ascending=False).reset_index(drop=True)

def component_scores(row):
    return {
        "Momentum":min(100,round(row["gap_pct"]*2)),
        "Volume":min(100,round(row["relative_volume"]*10)),
        "Float":max(0,round(100-row["float_m"]*1.5)),
        "Catalyst":95 if row["catalyst_quality"]=="Strong" else 75 if row["catalyst_quality"]=="Medium" else 40,
        "Trend":90 if row["above_vwap"] else 45,
        "Risk":90 if row["room_to_resistance_r"]>=2 else 55,
        "Overall":round(row["spider_score"]),
    }

def build_trade_plan(row,account,risk_pct):
    sizing=calculate_position_size(account,risk_pct,row["entry"],row["stop"])
    return {**sizing,"entry":row["entry"],"stop":row["stop"],"target_1r":row["target_1r"],"target_2r":row["target_2r"]}

def replay_grade(g,reveal,decision,entry,stop):
    future=g.iloc[reveal:].copy()
    risk=entry-stop
    if decision=="No Trade":
        return {"result":"No Trade","message":"You chose to skip the setup.","mfe_r":0.0,"mae_r":0.0,
                "coach_review":"Skipping is correct when your rules are absent, even if price later rises."}
    if risk<=0 or future.empty:
        return {"result":"Invalid","message":"Entry must be above stop.","mfe_r":0.0,"mae_r":0.0,
                "coach_review":"Define the technical stop first."}
    mfe=(future["high"].max()-entry)/risk
    mae=(entry-future["low"].min())/risk
    stop_idx=next((i for i,r in future.iterrows() if r["low"]<=stop),None)
    target=entry+2*risk
    target_idx=next((i for i,r in future.iterrows() if r["high"]>=target),None)
    if target_idx is not None and (stop_idx is None or target_idx<stop_idx):
        return {"result":"Win","message":"2R target reached before stop.","mfe_r":mfe,"mae_r":mae,
                "coach_review":"The process worked because risk was defined before the outcome."}
    if stop_idx is not None:
        return {"result":"Loss","message":"Stop reached before 2R.","mfe_r":mfe,"mae_r":mae,
                "coach_review":"A planned loss is acceptable. Grade the decision by rule quality."}
    return {"result":"Open","message":"Neither 2R nor stop was reached.","mfe_r":mfe,"mae_r":mae,
            "coach_review":"Define time exits and management rules."}

def coach_trade(ticker,setup,emotion,entry,stop,exit_price,shares,followed_plan,chased,averaged_down,moved_stop):
    risk=abs(entry-stop)*shares
    pnl=(exit_price-entry)*shares
    r=pnl/risk if risk else 0
    score=100
    feedback=[]
    if not followed_plan:
        score-=25; feedback.append("You deviated from the written trade plan.")
    else:
        feedback.append("You followed the planned entry and stop.")
    if chased:
        score-=20; feedback.append("The entry was extended. Wait for a cleaner trigger.")
    if averaged_down:
        score-=30; feedback.append("Averaging down increased risk and violated the playbook.")
    if moved_stop:
        score-=25; feedback.append("Moving the stop farther away invalidated the original risk.")
    if emotion in ["FOMO","Revenge","Tired"]:
        score-=10; feedback.append(f"Your emotional state ({emotion}) increased decision risk.")
    else:
        feedback.append(f"Your emotional state ({emotion}) supported disciplined execution.")
    score=max(0,score)
    grade="A" if score>=90 else "B" if score>=75 else "C" if score>=60 else "F"
    next_action="Repeat this process." if grade=="A" else "Choose one execution mistake to eliminate on the next session."
    return {"grade":grade,"r_multiple":r,"rule_score":score,"feedback":feedback,"next_action":next_action}
