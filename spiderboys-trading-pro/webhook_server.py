from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import json, os, secrets
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

BASE_DIR=Path(__file__).resolve().parent
OUT=BASE_DIR/"data"/"tradingview_webhooks.jsonl"
WEBHOOK_TOKEN=os.getenv("SPIDERBOYS_WEBHOOK_TOKEN","")
app=FastAPI(title="Spiderboys TradingView Bridge",version="1.0")

class AlertPayload(BaseModel):
    symbol: str=Field(min_length=1,max_length=40)
    signal: str=Field(min_length=1,max_length=80)
    price: float|None=None
    timeframe: str|None=None
    message: str|None=None
    token: str|None=None
    event_time: str|None=None

@app.get("/health")
def health(): return {"status":"ok","service":"spiderboys-tradingview-bridge"}

@app.post("/tradingview/webhook")
async def tradingview_webhook(request: Request):
    try: raw=await request.json()
    except Exception: raise HTTPException(400,"Webhook body must be valid JSON")
    payload=AlertPayload.model_validate(raw)
    if WEBHOOK_TOKEN and not secrets.compare_digest(payload.token or "",WEBHOOK_TOKEN):
        raise HTTPException(401,"Invalid webhook token")
    event={"received_at":datetime.now(timezone.utc).isoformat(),**payload.model_dump(exclude={"token"})}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("a",encoding="utf-8") as f: f.write(json.dumps(event,separators=(",",":"))+"\n")
    return {"accepted":True,"symbol":payload.symbol,"signal":payload.signal}
