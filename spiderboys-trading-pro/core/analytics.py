import numpy as np
import pandas as pd


def grouped_stats(journal, column):
    if journal.empty or column not in journal.columns: return pd.DataFrame()
    out=journal.groupby(column, dropna=False).agg(trades=("ticker","count"),win_rate=("win","mean"),avg_r=("r_multiple","mean"),net_pnl=("pnl","sum")).reset_index()
    out["win_rate"]*=100
    return out.sort_values("net_pnl", ascending=False)


def summarize_journal(journal):
    if journal.empty:
        return {"trades":0,"win_rate":0,"avg_r":0,"net_pnl":0,"expectancy_r":0,"profit_factor":0,"best_setup":"N/A","max_drawdown_r":0,"rule_compliance":0,"coach_summary":"Start journaling completed trades to unlock analytics."}
    j=journal.copy()
    for c in ["pnl","r_multiple"]: j[c]=pd.to_numeric(j[c],errors="coerce").fillna(0)
    j["win"]=j["win"].astype(str).str.lower().isin(["true","1","yes"])
    wins=j.loc[j["pnl"]>0,"pnl"].sum(); losses=-j.loc[j["pnl"]<0,"pnl"].sum()
    equity=j["r_multiple"].cumsum(); dd=equity-equity.cummax()
    setup_avg=j.groupby("setup")["r_multiple"].mean()
    best=setup_avg.idxmax() if not setup_avg.empty else "N/A"
    compliance=j["execution_grade"].isin(["A","B"]).mean()*100
    return {"trades":len(j),"win_rate":j["win"].mean()*100,"avg_r":j["r_multiple"].mean(),"net_pnl":j["pnl"].sum(),"expectancy_r":j["r_multiple"].mean(),"profit_factor":wins/losses if losses>0 else np.inf,"best_setup":best,"max_drawdown_r":abs(dd.min()),"rule_compliance":compliance,"coach_summary":f"Your strongest demo edge is {best}. Protect it by avoiding low-grade and emotional entries."}
