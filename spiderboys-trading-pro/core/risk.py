from decimal import Decimal, ROUND_FLOOR


def _money(value) -> Decimal:
    return Decimal(str(value))


def calculate_position_size(account, risk_pct, entry, stop):
    """Calculate a whole-share position without binary floating-point drift."""
    entry_dec = _money(entry)
    stop_dec = _money(stop)
    risk_per_share_dec = abs(entry_dec - stop_dec)
    dollar_risk_dec = _money(account) * _money(risk_pct) / Decimal("100")
    shares = (
        int((dollar_risk_dec / risk_per_share_dec).to_integral_value(rounding=ROUND_FLOOR))
        if risk_per_share_dec > 0
        else 0
    )
    return {
        "shares": shares,
        "dollar_risk": float(dollar_risk_dec),
        "risk_per_share": float(risk_per_share_dec),
        "buying_power": float(Decimal(shares) * entry_dec),
    }


def risk_lock_status(max_loss, realized, losses, open_risk):
    combined = abs(min(realized, 0)) + open_risk
    if realized <= -abs(max_loss):
        return {"locked": True, "warning": False, "message": "Daily loss limit reached. No new trades."}
    if losses >= 3:
        return {"locked": True, "warning": False, "message": "Three consecutive losses reached. Stop and review."}
    if combined >= abs(max_loss):
        return {"locked": True, "warning": False, "message": "Combined realized and open risk exceeds the daily limit."}
    if combined >= abs(max_loss) * 0.7 or losses == 2:
        return {"locked": False, "warning": True, "message": "Near the daily risk limit. Reduce exposure or stop."}
    return {"locked": False, "warning": False, "message": "Risk controls are within limits."}
