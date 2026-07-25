# Architecture

```text
app.py                       Streamlit presentation and user workflow
core/engine.py               Scanner scoring, trade plans, replay and coaching
core/risk.py                 Position sizing and trading lock controls
core/analytics.py            Journal statistics and performance analytics
core/data.py                 Normalized CSV journal and demo-data storage
core/tradingview.py          TradingView URLs and webhook-event helpers
providers/                   Replaceable market-data provider contracts
tradingview/                 Pine Script indicators and watchlist radar
webhook_server.py            Optional external TradingView webhook receiver
tests/                       Fast unit and smoke tests
.github/workflows/ci.yml     Automated validation on every GitHub change
```

The main Streamlit deployment runs only `app.py`. The webhook receiver is a separate optional service and must not be configured as the Streamlit entry point.
