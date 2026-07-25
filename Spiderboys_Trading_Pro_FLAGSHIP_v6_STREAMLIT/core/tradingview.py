from __future__ import annotations
from pathlib import Path
from urllib.parse import quote
import json
import pandas as pd


def normalize_exchange(exchange: str) -> str:
    value=(exchange or "NASDAQ").strip().upper()
    return {"NAS":"NASDAQ","NASDAQGS":"NASDAQ","NMS":"NASDAQ","NYSEARCA":"AMEX"}.get(value,value)

def chart_url(ticker: str, exchange: str="NASDAQ") -> str:
    symbol=f"{normalize_exchange(exchange)}:{ticker.strip().upper()}"
    return "https://www.tradingview.com/chart/?symbol="+quote(symbol,safe="")

def load_webhook_events(base_dir):
    path=Path(base_dir)/"data"/"tradingview_webhooks.jsonl"
    if not path.exists() or not path.stat().st_size:
        return pd.DataFrame(columns=["received_at","symbol","signal","price","timeframe","message"])
    rows=[]
    for line in path.read_text().splitlines():
        try: rows.append(json.loads(line))
        except json.JSONDecodeError: continue
    return pd.DataFrame(rows)

def webhook_summary(df):
    if df.empty: return {"count":0,"symbols":0,"latest_signal":"—","latest_symbol":"—"}
    row=df.sort_values("received_at").iloc[-1]
    return {"count":len(df),"symbols":df.get("symbol",pd.Series(dtype=str)).nunique(),"latest_signal":str(row.get("signal","—")),"latest_symbol":str(row.get("symbol","—"))}
