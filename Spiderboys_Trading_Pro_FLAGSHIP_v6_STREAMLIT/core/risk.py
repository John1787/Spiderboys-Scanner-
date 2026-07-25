def calculate_position_size(account, risk_pct, entry, stop):
    risk_per_share = abs(float(entry)-float(stop))
    dollar_risk = float(account)*float(risk_pct)/100
    shares = int(dollar_risk//risk_per_share) if risk_per_share>0 else 0
    return {"shares":shares,"dollar_risk":dollar_risk,"risk_per_share":risk_per_share,"buying_power":shares*float(entry)}


def risk_lock_status(max_loss, realized, losses, open_risk):
    combined = abs(min(realized,0))+open_risk
    if realized <= -abs(max_loss): return {"locked":True,"warning":False,"message":"Daily loss limit reached. No new trades."}
    if losses >= 3: return {"locked":True,"warning":False,"message":"Three consecutive losses reached. Stop and review."}
    if combined >= abs(max_loss): return {"locked":True,"warning":False,"message":"Combined realized and open risk exceeds the daily limit."}
    if combined >= abs(max_loss)*0.7 or losses==2: return {"locked":False,"warning":True,"message":"Near the daily risk limit. Reduce exposure or stop."}
    return {"locked":False,"warning":False,"message":"Risk controls are within limits."}
