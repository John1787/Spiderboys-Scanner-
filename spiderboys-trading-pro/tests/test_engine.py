from pathlib import Path

from core.data import load_market
from core.engine import component_scores, scan_setups

BASE_DIR = Path(__file__).resolve().parents[1]


def test_demo_market_loads():
    market = load_market(BASE_DIR)
    assert not market.empty
    assert {"ticker", "datetime", "close", "entry", "stop"}.issubset(market.columns)


def test_scanner_returns_ranked_candidates():
    market = load_market(BASE_DIR)
    scan = scan_setups(
        market,
        min_price=1,
        max_price=50,
        min_gap=0,
        max_float=500,
        min_pm=0,
        min_rvol=0,
        min_score=0,
        max_spread=10,
        require_catalyst=False,
        require_vwap=False,
        setup_filter="All",
    )
    assert not scan.empty
    assert scan["elite_score"].between(0, 100).all()
    assert scan["elite_score"].is_monotonic_decreasing


def test_component_score_has_visible_factors():
    market = load_market(BASE_DIR)
    row = market.sort_values("datetime").groupby("ticker").tail(1).iloc[0]
    result = component_scores(row)
    assert set(result) == {
        "Gap", "Volume", "Float", "Catalyst", "Trend", "Structure",
        "Liquidity", "Room", "Overall"
    }
    assert 0 <= result["Overall"] <= 100
