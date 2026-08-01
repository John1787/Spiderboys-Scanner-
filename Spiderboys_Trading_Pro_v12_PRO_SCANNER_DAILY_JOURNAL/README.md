# Spiderboys Trading Pro v12

## Pro Scanner + Daily Journal

Version 12 combines a professional scanner-first workflow with a clean daily trade journal.

### Scanner views

- Premarket Gap
- High of Day Momentum
- Top Gappers
- 5-Minute Surge
- Close to High
- Low Float Leaders
- News Catalysts
- First Pullback Ready
- Continuation
- Reversal Watch
- After-Hours Movers

### Scanner fields

- Alert time
- Symbol and news flame
- Price
- Total and premarket volume
- Float
- Daily and five-minute relative volume
- Gap and daily change
- Five-minute change
- Distance from high of day
- Spider Score
- Grade
- Context note
- Setup status

Selecting a scanner row links the ticker across Charts, News, Trade Plan, Command Center, Spider AI, and Journal prefill.

### Daily trading journal

- Add a trade in under a minute
- Automatic long/short P/L
- Automatic risk and R-multiple
- Daily editable log
- Daily review notes
- Equity curve
- P/L calendar
- Setup, emotion, plan-compliance, and mistake analysis
- CSV import/export and blank template

### Storage note

The journal is stored in the active Streamlit session in this build. Download the CSV regularly for permanent backup. Production database persistence can be connected later.

### Data note

Scanner metrics are derived from the included training dataset. Quotes, profiles, and news are live when Finnhub endpoints respond. Intraday candles require a provider plan that includes historical bars and are otherwise labeled demo or unavailable.

## Deployment

Upload the contents of this folder directly to the GitHub repository root.

Main file:

```text
app.py
```
