import numpy as np

def grouped_stats(journal,column):
    out=journal.groupby(column).agg(
        trades=("ticker","count"),
        win_rate=("win","mean"),
        avg_r=("r_multiple","mean"),
        net_pnl=("pnl","sum"),
    ).reset_index()
    out["win_rate"]*=100
    return out

def summarize_journal(journal):
    wins=journal.loc[journal["pnl"]>0,"pnl"].sum()
    losses=-journal.loc[journal["pnl"]<0,"pnl"].sum()
    equity=journal["r_multiple"].cumsum()
    dd=equity-equity.cummax()
    best=journal.groupby("setup")["r_multiple"].mean().idxmax()
    compliance=(journal["execution_grade"].isin(["A","B"])).mean()*100
    return {
        "trades":len(journal),
        "win_rate":journal["win"].mean()*100,
        "avg_r":journal["r_multiple"].mean(),
        "net_pnl":journal["pnl"].sum(),
        "expectancy_r":journal["r_multiple"].mean(),
        "profit_factor":wins/losses if losses>0 else np.inf,
        "best_setup":best,
        "max_drawdown_r":abs(dd.min()),
        "rule_compliance":compliance,
        "coach_summary":f"Your strongest demo edge is {best}. The biggest opportunity is improving consistency after emotional or low-quality entries."
    }
