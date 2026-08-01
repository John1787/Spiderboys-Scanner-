# Spiderboys Trading Pro v12.1

## AI Intelligence + UI Fix

### Interface fixes

- Removed the custom **Collapse Scanner** and **Collapse Intel** buttons.
- Desk mode now always shows the scanner, synchronized charts, and intelligence panel.
- Compact mode keeps the stacked responsive layout.
- Timeframe controls now use dark navy, blue, and cyan instead of white.
- Minute-chart panels and unavailable-data placeholders now use the dark terminal theme.
- Restricted provider messages are shortened to clear user-facing explanations.

### AI Trade Plan

The Trade Plan now combines:

- Recent daily price structure
- Three-session and five-session movement
- Higher highs / higher lows
- Recent support and resistance
- Volume acceleration
- Current quote movement
- Recent company-news sentiment
- Positive catalyst terms and risk terms
- Intraday VWAP and EMA structure when candle data is available

It produces a scenario-based:

- Bullish, bearish, neutral, or insufficient-data bias
- Low, moderate, or high confidence label
- Confirmation level
- Invalidation level
- Evidence list
- Caution list
- Long or short position plan
- Share sizing, stop, 1R, and 2R targets

The directional read is not a prediction or guarantee. It is a transparent summary of the available price and news evidence.

### Recent-history sources

The app tries, in order:

1. Alpaca daily bars when Alpaca credentials are configured
2. FMP light/full end-of-day history
3. Clearly labeled bundled training data for demo tickers

### Optional Alpaca Secrets

```toml
[alpaca]
api_key = "YOUR_ALPACA_KEY"
secret_key = "YOUR_ALPACA_SECRET"
feed = "iex"
```

### Deployment

Upload the contents of this folder directly to the GitHub repository root.

Main file:

```text
app.py
```
