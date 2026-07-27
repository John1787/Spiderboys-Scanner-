# Spiderboys Trading Pro v3 — Full Workstation

## Included
- Morning command center
- Market intelligence dashboard
- Live-style momentum scanner
- Professional candlestick charts
- Spider Score component grading
- Trade planner
- Rule-based AI trade coach
- Replay academy
- Risk command center
- Demo journal
- Performance analytics
- Alert center
- Daily process checklist
- Integration roadmap

## Deploy
Upload everything inside this folder directly to the root of your GitHub repository.

Main file path in Streamlit Community Cloud:

app.py

All market data, news, alerts, and outcomes in this version are simulated for training.


## Version 4 live-data foundation
Adds optional Alpaca paper-account balances, positions, ticker snapshots, and recent bars. Add credentials through Streamlit Secrets only. Live order submission remains disabled.

## Version 5 — Live News and Watchlist Scanner

Version 5 connects to the FMP and Finnhub keys stored in Streamlit Secrets.

```toml
[fmp]
api_key = "YOUR_FMP_API_KEY"

[finnhub]
api_key = "YOUR_FINNHUB_API_KEY"
```

New workspaces:

- Live Scanner: focused watchlist quotes, company profiles, headlines, and Spider Score
- Live News Center: combined market headlines, ticker research, duplicate removal, catalyst classification
- Connection status and graceful fallback when a free-plan endpoint is unavailable
- Rate-limit and provider error messages that do not crash the app

Important: free API plans are suitable for a limited watchlist and research workflow. They are not a full-exchange, millisecond real-time scanner. Live order submission remains disabled.
