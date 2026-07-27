# Spiderboys Trading Pro v6

Clean, single-root Streamlit deployment package.

## Correct GitHub layout

Upload the **contents** of this folder directly to the root of the repository:

```text
app.py
requirements.txt
README.md
VERSION.json
.streamlit/
core/
data/
```

Do not upload the outer `Spiderboys_Trading_Pro_v6_CLEAN_COLOR` folder.

## Streamlit main file path

```text
app.py
```

## Streamlit Secrets

```toml
[fmp]
api_key = "YOUR_FMP_API_KEY"

[finnhub]
api_key = "YOUR_FINNHUB_API_KEY"

# Optional
[alpaca]
api_key = "YOUR_ALPACA_KEY"
secret_key = "YOUR_ALPACA_SECRET"
feed = "iex"
```

## Version 6 highlights

- New navy, electric-blue, cyan, teal, and gold interface
- Clean root-level project structure
- Live FMP and Finnhub news/quote integrations
- Focused live watchlist scanner
- Catalyst scoring and Spider Score
- First Pullback planning tools
- Risk controls, journal, analytics, replay, alerts
- Safe fallbacks when a free API endpoint is unavailable
- Live order submission remains disabled
