# Spiderboys Trading Pro v7

## Integrated workstation

Version 7 links one active ticker across Home, Live Scanner, Live News, Charts, and Trade Plan.

### Live chart behavior

- Uses FMP intraday bars when the saved FMP API plan permits the endpoint.
- Supports 1-minute, 5-minute, 15-minute, and 30-minute selections.
- Clearly labels charts as LIVE, DEMO, or UNAVAILABLE.
- Never silently presents training data as live data.

### Upload

Upload the contents of this folder directly to the GitHub repository root:

```text
app.py
requirements.txt
README.md
VERSION.json
.streamlit/
core/
data/
```

Streamlit main file path:

```text
app.py
```

### Secrets

```toml
[fmp]
api_key = "YOUR_FMP_API_KEY"

[finnhub]
api_key = "YOUR_FINNHUB_API_KEY"
```

Live order submission remains disabled.
