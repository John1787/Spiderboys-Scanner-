from core.risk import calculate_position_size, risk_lock_status


def test_position_size_respects_dollar_risk():
    result = calculate_position_size(25_000, 0.5, 5.50, 5.30)
    assert result["dollar_risk"] == 125
    assert result["shares"] == 625
    assert round(result["risk_per_share"], 2) == 0.2


def test_daily_loss_lock():
    status = risk_lock_status(max_loss=500, realized=-500, losses=1, open_risk=0)
    assert status["locked"] is True
