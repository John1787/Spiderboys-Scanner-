# Spiderboys Trading Pro v11 — Scanner Terminal

Version 11 changes the workstation to a scanner-first workflow.

## Scanner views

- High of Day Momentum
- Top Gappers
- Volume Surge
- Low Float
- News Catalysts

The scanner includes alert time, symbol/news flame, price, volume, float, daily RVOL, five-minute RVOL, gap, change, five-minute change, distance from high of day, Spider Score, and setup status.

## Linked workflow

Selecting a scanner row links the ticker to:

- Command Center
- Multi-timeframe charts
- Live News
- Trade Plan
- Spider AI

## Data labeling

Scanner momentum metrics are derived from the included training dataset in this build. Finnhub quotes, profiles, and news are live when the endpoints respond. Intraday candles are live only when the connected provider plan includes historical bars; otherwise the app clearly labels the chart as demo or unavailable.

## Deployment

Upload the contents of this folder directly to the GitHub repository root.

Streamlit main file:

```text
app.py
```
