from datetime import datetime, timedelta, timezone
import requests
import pandas as pd
TRADING_PAPER_URL="https://paper-api.alpaca.markets"
DATA_URL="https://data.alpaca.markets"
class AlpacaError(RuntimeError): pass
def _headers(k,s): return {"APCA-API-KEY-ID":k,"APCA-API-SECRET-KEY":s,"Accept":"application/json"}
def _get(url,k,s,params=None,timeout=20):
    try: r=requests.get(url,headers=_headers(k,s),params=params or {},timeout=timeout)
    except requests.RequestException as e: raise AlpacaError(f"Connection failed: {e}") from e
    if r.status_code>=400: raise AlpacaError(f"Alpaca returned HTTP {r.status_code}: {r.text[:300]}")
    try: return r.json()
    except ValueError as e: raise AlpacaError("Alpaca returned an invalid response.") from e
def get_account(k,s):
    d=_get(f"{TRADING_PAPER_URL}/v2/account",k,s)
    return {"status":d.get("status",""),"cash":float(d.get("cash",0) or 0),"portfolio_value":float(d.get("portfolio_value",0) or 0),"buying_power":float(d.get("buying_power",0) or 0),"equity":float(d.get("equity",0) or 0),"pattern_day_trader":bool(d.get("pattern_day_trader",False)),"trading_blocked":bool(d.get("trading_blocked",False))}
def get_positions(k,s):
    data=_get(f"{TRADING_PAPER_URL}/v2/positions",k,s); rows=[]
    for x in data: rows.append({"symbol":x.get("symbol"),"qty":float(x.get("qty",0) or 0),"side":x.get("side"),"avg_entry_price":float(x.get("avg_entry_price",0) or 0),"current_price":float(x.get("current_price",0) or 0),"market_value":float(x.get("market_value",0) or 0),"unrealized_pl":float(x.get("unrealized_pl",0) or 0),"unrealized_plpc":float(x.get("unrealized_plpc",0) or 0)*100})
    return pd.DataFrame(rows)
def get_latest_snapshot(symbol,k,s,feed="iex"):
    symbol=symbol.upper().strip(); d=_get(f"{DATA_URL}/v2/stocks/{symbol}/snapshot",k,s,{"feed":feed}); lt=d.get("latestTrade") or {}; db=d.get("dailyBar") or {}; prev=d.get("prevDailyBar") or {}; pc=float(prev.get("c",0) or 0); p=float(lt.get("p",db.get("c",0)) or 0)
    return {"symbol":symbol,"price":p,"change_pct":((p/pc)-1)*100 if pc else 0,"day_high":float(db.get("h",0) or 0),"day_low":float(db.get("l",0) or 0),"day_volume":int(db.get("v",0) or 0),"previous_close":pc}
def get_bars(symbol,k,s,timeframe="1Min",limit=120,feed="iex"):
    end=datetime.now(timezone.utc); start=end-timedelta(days=5); symbol=symbol.upper().strip(); d=_get(f"{DATA_URL}/v2/stocks/{symbol}/bars",k,s,{"timeframe":timeframe,"start":start.isoformat(),"end":end.isoformat(),"limit":int(limit),"adjustment":"raw","feed":feed,"sort":"asc"}); rows=[]
    for b in d.get("bars",[]): rows.append({"datetime":pd.to_datetime(b.get("t")),"open":float(b.get("o",0) or 0),"high":float(b.get("h",0) or 0),"low":float(b.get("l",0) or 0),"close":float(b.get("c",0) or 0),"volume":int(b.get("v",0) or 0),"vwap":float(b.get("vw",0) or 0)})
    return pd.DataFrame(rows)
