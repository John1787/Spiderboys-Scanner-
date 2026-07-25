import math
import pandas as pd
from core.risk import calculate_position_size

SETUP_WEIGHTS = {
    "gap": 16,
    "volume": 18,
    "float": 12,
    "catalyst": 15,
    "trend": 12,
    "structure": 15,
    "liquidity": 6,
    "room": 6,
}


def _clamp(value, low=0, high=100):
    return max(low, min(high, value))


def component_scores(row):
    gap = _clamp((float(row["gap_pct"]) / 30) * 100)
    volume = _clamp((float(row["relative_volume"]) / 8) * 100)
    float_score = _clamp(110 - float(row["float_m"]) * 2.2)
    cq = str(row.get("catalyst_quality", ""))
    catalyst = 100 if cq == "Strong" else 72 if cq == "Medium" else 35
    trend = 95 if bool(row.get("above_vwap", False)) else 35
    pq = str(row.get("pullback_quality", ""))
    structure = 100 if pq == "Excellent" else 78 if pq == "Good" else 48
    spread = float(row.get("spread_pct", 1.0))
    liquidity = _clamp(100 - spread * 160)
    room = _clamp((float(row.get("room_to_resistance_r", 0)) / 3) * 100)
    raw = {
        "Gap": round(gap), "Volume": round(volume), "Float": round(float_score),
        "Catalyst": round(catalyst), "Trend": round(trend), "Structure": round(structure),
        "Liquidity": round(liquidity), "Room": round(room)
    }
    weighted = sum(raw[k.capitalize()] * w for k, w in SETUP_WEIGHTS.items()) / sum(SETUP_WEIGHTS.values())
    raw["Overall"] = round(weighted)
    return raw


def quality_from_score(score):
    if score >= 90: return "A+"
    if score >= 82: return "A"
    if score >= 74: return "B"
    if score >= 65: return "C"
    return "Avoid"


def scan_setups(market, min_price=1.0, max_price=20.0, min_gap=10, max_float=75,
                min_pm=250000, min_rvol=1.5, min_score=60, max_spread=1.0,
                require_catalyst=True, require_vwap=False, setup_filter="All"):
    latest = market.sort_values("datetime").groupby("ticker").tail(1).copy()
    scored = latest.apply(component_scores, axis=1, result_type="expand")
    latest["elite_score"] = scored["Overall"].values
    latest["elite_grade"] = latest["elite_score"].map(quality_from_score)
    latest["price"] = latest["close"]
    latest["risk_per_share"] = (latest["entry"] - latest["stop"]).abs()
    latest["reward_2r"] = (latest["target_2r"] - latest["entry"]).abs()
    latest["rr"] = latest["reward_2r"] / latest["risk_per_share"].replace(0, pd.NA)
    latest["news_confirmed"] = latest["catalyst"].fillna("").astype(str).str.strip().ne("")
    latest["tradability"] = latest.apply(
        lambda r: "READY" if r["elite_score"] >= 82 and r["above_vwap"] and r["spread_pct"] <= .5
        else "WATCH" if r["elite_score"] >= 70 else "PASS", axis=1)

    mask = (
        latest["price"].between(min_price, max_price) &
        (latest["gap_pct"] >= min_gap) &
        (latest["float_m"] <= max_float) &
        (latest["premarket_volume"] >= min_pm) &
        (latest["relative_volume"] >= min_rvol) &
        (latest["elite_score"] >= min_score) &
        (latest["spread_pct"] <= max_spread)
    )
    if require_catalyst:
        mask &= latest["news_confirmed"]
    if require_vwap:
        mask &= latest["above_vwap"]
    if setup_filter != "All":
        mask &= latest["setup_status"].astype(str).str.contains(setup_filter, case=False, na=False)

    cols = [
        "ticker","price","gap_pct","float_m","premarket_volume","relative_volume",
        "spread_pct","above_vwap","catalyst","catalyst_quality","pullback_quality",
        "elite_score","elite_grade","tradability","setup_status","entry","stop",
        "target_1r","target_2r","rr","room_to_resistance_r","coach_note"
    ]
    return latest.loc[mask, cols].sort_values(
        ["elite_score","relative_volume","premarket_volume"], ascending=False
    ).reset_index(drop=True)


def build_trade_plan(row, account, risk_pct, buying_power=None):
    sizing = calculate_position_size(account, risk_pct, row["entry"], row["stop"])
    shares = sizing["shares"]
    if buying_power is not None and row["entry"] > 0:
        shares = min(shares, int(buying_power // row["entry"]))
    risk_per_share = abs(row["entry"] - row["stop"])
    return {
        **sizing,
        "shares": shares,
        "entry": row["entry"], "stop": row["stop"],
        "target_1r": row["target_1r"], "target_2r": row["target_2r"],
        "position_value": shares * row["entry"],
        "planned_loss": shares * risk_per_share,
        "potential_2r": shares * abs(row["target_2r"] - row["entry"]),
    }


def setup_explanation(row):
    positives, risks = [], []
    if row["gap_pct"] >= 20: positives.append("large gap")
    if row["relative_volume"] >= 5: positives.append("exceptional RVOL")
    elif row["relative_volume"] >= 2: positives.append("healthy RVOL")
    if row["float_m"] <= 20: positives.append("low float")
    if row["above_vwap"]: positives.append("above VWAP")
    if row["catalyst_quality"] == "Strong": positives.append("strong catalyst")
    if row["room_to_resistance_r"] >= 2: positives.append("2R+ room")
    if row["spread_pct"] > .5: risks.append("wide spread")
    if not row["above_vwap"]: risks.append("below VWAP")
    if row["float_m"] > 50: risks.append("heavier float")
    if row["room_to_resistance_r"] < 1.5: risks.append("limited room")
    return positives, risks


def replay_grade(g, reveal, decision, entry, stop):
    future = g.iloc[reveal:].copy()
    risk = entry - stop
    if decision == "No Trade":
        return {"result":"No Trade","message":"You chose to skip the setup.","mfe_r":0.0,"mae_r":0.0,
                "coach_review":"Skipping is correct when your rules are absent, even if price later rises."}
    if risk <= 0 or future.empty:
        return {"result":"Invalid","message":"Entry must be above stop.","mfe_r":0.0,"mae_r":0.0,
                "coach_review":"Define the technical stop first."}
    mfe = (future["high"].max()-entry)/risk
    mae = (entry-future["low"].min())/risk
    stop_hits = future.index[future["low"] <= stop].tolist()
    target = entry + 2*risk
    target_hits = future.index[future["high"] >= target].tolist()
    stop_idx = stop_hits[0] if stop_hits else None
    target_idx = target_hits[0] if target_hits else None
    if target_idx is not None and (stop_idx is None or target_idx < stop_idx):
        return {"result":"Win","message":"2R target reached before stop.","mfe_r":mfe,"mae_r":mae,
                "coach_review":"The process worked because risk was defined before the outcome."}
    if stop_idx is not None:
        return {"result":"Loss","message":"Stop reached before 2R.","mfe_r":mfe,"mae_r":mae,
                "coach_review":"A planned loss is acceptable. Grade the decision by rule quality."}
    return {"result":"Open","message":"Neither 2R nor stop was reached.","mfe_r":mfe,"mae_r":mae,
            "coach_review":"Define time exits and management rules."}


def coach_trade(ticker, setup, emotion, entry, stop, exit_price, shares,
                followed_plan, chased, averaged_down, moved_stop):
    risk = abs(entry-stop)*shares
    pnl = (exit_price-entry)*shares
    r = pnl/risk if risk else 0
    score, feedback = 100, []
    for condition, penalty, note in [
        (not followed_plan,25,"You deviated from the written trade plan."),
        (chased,20,"The entry was extended. Wait for a cleaner trigger."),
        (averaged_down,30,"Averaging down increased risk and violated the playbook."),
        (moved_stop,25,"Moving the stop farther away invalidated the original risk."),
        (emotion in ["FOMO","Revenge","Tired"],10,f"Your emotional state ({emotion}) increased decision risk."),
    ]:
        if condition: score -= penalty; feedback.append(note)
    if followed_plan: feedback.append("You followed the planned entry and stop.")
    score = max(0, score)
    grade = "A" if score>=90 else "B" if score>=75 else "C" if score>=60 else "F"
    return {"grade":grade,"r_multiple":r,"rule_score":score,"feedback":feedback,
            "next_action":"Repeat this process." if grade=="A" else "Eliminate one execution mistake next session."}
