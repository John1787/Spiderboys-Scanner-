from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any
import re

import pandas as pd
import requests

FMP_BASE = "https://financialmodelingprep.com/stable"
FINNHUB_BASE = "https://finnhub.io/api/v1"


class MarketDataError(RuntimeError):
    pass


def _get_json(url: str, params: dict[str, Any], timeout: int = 15) -> Any:
    try:
        response = requests.get(url, params=params, timeout=timeout)
    except requests.RequestException as exc:
        raise MarketDataError(f"Connection failed: {exc}") from exc

    if response.status_code == 429:
        raise MarketDataError("API rate limit reached. Wait briefly, then refresh.")
    if response.status_code >= 400:
        detail = response.text[:240].strip().replace("\\u", " ").replace("\n", " ")
        raise MarketDataError(f"Provider returned HTTP {response.status_code}: {detail}")

    try:
        payload = response.json()
    except ValueError as exc:
        raise MarketDataError("Provider returned an invalid response.") from exc

    if isinstance(payload, dict):
        message = payload.get("Error Message") or payload.get("error") or payload.get("message")
        if message and len(payload) <= 3:
            raise MarketDataError(str(message))
    return payload


def finnhub_quote(symbol: str, api_key: str) -> dict[str, Any]:
    data = _get_json(
        f"{FINNHUB_BASE}/quote",
        {"symbol": symbol.upper().strip(), "token": api_key},
    )
    price = float(data.get("c", 0) or 0)
    previous_close = float(data.get("pc", 0) or 0)
    change_pct = float(data.get("dp", 0) or 0)
    if not change_pct and previous_close:
        change_pct = ((price / previous_close) - 1) * 100
    return {
        "symbol": symbol.upper().strip(),
        "price": price,
        "change": float(data.get("d", 0) or 0),
        "change_pct": change_pct,
        "high": float(data.get("h", 0) or 0),
        "low": float(data.get("l", 0) or 0),
        "open": float(data.get("o", 0) or 0),
        "previous_close": previous_close,
        "timestamp": int(data.get("t", 0) or 0),
        "source": "Finnhub",
    }


def finnhub_profile(symbol: str, api_key: str) -> dict[str, Any]:
    data = _get_json(
        f"{FINNHUB_BASE}/stock/profile2",
        {"symbol": symbol.upper().strip(), "token": api_key},
    )
    return {
        "symbol": data.get("ticker", symbol.upper().strip()),
        "name": data.get("name", ""),
        "exchange": data.get("exchange", ""),
        "industry": data.get("finnhubIndustry", ""),
        "market_cap_m": float(data.get("marketCapitalization", 0) or 0),
        "shares_outstanding_m": float(data.get("shareOutstanding", 0) or 0),
        "website": data.get("weburl", ""),
        "logo": data.get("logo", ""),
        "source": "Finnhub",
    }


def finnhub_company_news(symbol: str, api_key: str, lookback_days: int = 5) -> pd.DataFrame:
    end = date.today()
    start = end - timedelta(days=int(lookback_days))
    payload = _get_json(
        f"{FINNHUB_BASE}/company-news",
        {
            "symbol": symbol.upper().strip(),
            "from": start.isoformat(),
            "to": end.isoformat(),
            "token": api_key,
        },
    )
    rows: list[dict[str, Any]] = []
    for item in payload if isinstance(payload, list) else []:
        ts = item.get("datetime")
        published = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None
        rows.append({
            "published": published,
            "symbol": symbol.upper().strip(),
            "headline": item.get("headline", ""),
            "summary": item.get("summary", ""),
            "source": item.get("source", "Finnhub"),
            "url": item.get("url", ""),
            "provider": "Finnhub",
        })
    return _score_news(pd.DataFrame(rows))


def finnhub_market_news(api_key: str, category: str = "general") -> pd.DataFrame:
    payload = _get_json(
        f"{FINNHUB_BASE}/news",
        {"category": category, "token": api_key},
    )
    rows: list[dict[str, Any]] = []
    for item in payload if isinstance(payload, list) else []:
        ts = item.get("datetime")
        published = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None
        rows.append({
            "published": published,
            "symbol": item.get("related", ""),
            "headline": item.get("headline", ""),
            "summary": item.get("summary", ""),
            "source": item.get("source", "Finnhub"),
            "url": item.get("url", ""),
            "provider": "Finnhub",
        })
    return _score_news(pd.DataFrame(rows))



def fmp_intraday(symbol: str, api_key: str, interval: str = "5min") -> pd.DataFrame:
    """Retrieve FMP intraday OHLCV bars and calculate VWAP/EMAs."""
    supported = {"1min", "5min", "15min", "30min", "1hour", "4hour"}
    if interval not in supported:
        raise MarketDataError(f"Unsupported interval: {interval}")

    payload = _get_json(
        f"{FMP_BASE}/historical-chart/{interval}",
        {"symbol": symbol.upper().strip(), "apikey": api_key},
    )
    rows = payload if isinstance(payload, list) else []
    if not rows:
        raise MarketDataError(f"No intraday bars were returned for {symbol.upper().strip()}.")

    frame = pd.DataFrame(rows).copy()
    date_col = "date" if "date" in frame.columns else "datetime" if "datetime" in frame.columns else None
    if date_col is None:
        raise MarketDataError("Intraday response did not include timestamps.")

    rename = {
        date_col: "datetime",
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
    }
    frame = frame.rename(columns=rename)
    needed = ["datetime", "open", "high", "low", "close", "volume"]
    missing = [col for col in needed if col not in frame.columns]
    if missing:
        raise MarketDataError(f"Intraday response is missing: {', '.join(missing)}")

    frame = frame[needed].copy()
    frame["datetime"] = pd.to_datetime(frame["datetime"], errors="coerce")
    for col in ["open", "high", "low", "close", "volume"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame.dropna(subset=["datetime", "open", "high", "low", "close"])
    frame = frame.sort_values("datetime").drop_duplicates("datetime").tail(500).reset_index(drop=True)

    typical = (frame["high"] + frame["low"] + frame["close"]) / 3
    volume = frame["volume"].fillna(0).clip(lower=0)
    cumulative_volume = volume.cumsum().replace(0, pd.NA)
    frame["vwap"] = (typical * volume).cumsum() / cumulative_volume
    frame["vwap"] = frame["vwap"].fillna(frame["close"].expanding().mean())
    frame["ema9"] = frame["close"].ewm(span=9, adjust=False).mean()
    frame["ema20"] = frame["close"].ewm(span=20, adjust=False).mean()
    frame["source"] = "FMP Live Intraday"
    frame["ticker"] = symbol.upper().strip()
    return frame


def fmp_profile(symbol: str, api_key: str) -> dict[str, Any]:
    payload = _get_json(
        f"{FMP_BASE}/profile",
        {"symbol": symbol.upper().strip(), "apikey": api_key},
    )
    item = payload[0] if isinstance(payload, list) and payload else payload if isinstance(payload, dict) else {}
    return {
        "symbol": item.get("symbol", symbol.upper().strip()),
        "name": item.get("companyName", item.get("name", "")),
        "exchange": item.get("exchange", item.get("exchangeShortName", "")),
        "industry": item.get("industry", ""),
        "sector": item.get("sector", ""),
        "market_cap": float(item.get("marketCap", 0) or 0),
        "price": float(item.get("price", 0) or 0),
        "beta": float(item.get("beta", 0) or 0),
        "website": item.get("website", ""),
        "description": item.get("description", ""),
        "source": "FMP",
    }


def fmp_stock_news(api_key: str, symbol: str | None = None, limit: int = 50) -> pd.DataFrame:
    params: dict[str, Any] = {"limit": int(limit), "apikey": api_key}
    endpoint = "news/stock-latest"
    params["page"] = 0
    if symbol:
        endpoint = "news/stock"
        params["symbols"] = symbol.upper().strip()
    payload = _get_json(f"{FMP_BASE}/{endpoint}", params)
    rows: list[dict[str, Any]] = []
    for item in payload if isinstance(payload, list) else []:
        published_raw = item.get("publishedDate") or item.get("published_date")
        rows.append({
            "published": pd.to_datetime(published_raw, utc=True, errors="coerce"),
            "symbol": item.get("symbol", symbol or ""),
            "headline": item.get("title", item.get("headline", "")),
            "summary": item.get("text", item.get("summary", "")),
            "source": item.get("site", item.get("publisher", "FMP")),
            "url": item.get("url", ""),
            "provider": "FMP",
        })
    return _score_news(pd.DataFrame(rows))


POSITIVE_TERMS = {
    "approval": 18, "approved": 18, "fda": 15, "contract": 12, "award": 12,
    "partnership": 10, "acquisition": 8, "merger": 8, "record revenue": 12,
    "beats": 10, "beat estimates": 12, "raises guidance": 15, "upgrade": 8,
    "breakthrough": 14, "patent": 7, "launch": 6, "expands": 6,
}
NEGATIVE_TERMS = {
    "offering": -18, "public offering": -22, "direct offering": -25,
    "dilution": -25, "bankruptcy": -30, "delisting": -25, "investigation": -15,
    "lawsuit": -10, "misses": -10, "cuts guidance": -15, "downgrade": -8,
    "reverse split": -15, "going concern": -25, "recall": -12,
}


def catalyst_score(headline: str, summary: str = "") -> tuple[int, str, str]:
    text = f"{headline} {summary}".lower()
    score = 0
    matched: list[str] = []
    for term, weight in POSITIVE_TERMS.items():
        if term in text:
            score += weight
            matched.append(term)
    for term, weight in NEGATIVE_TERMS.items():
        if term in text:
            score += weight
            matched.append(term)
    score = max(-40, min(40, score))
    label = "Bullish" if score >= 8 else "Bearish" if score <= -8 else "Neutral"
    reason = ", ".join(matched[:4]) if matched else "No strong keyword catalyst"
    return score, label, reason


def _score_news(frame: pd.DataFrame) -> pd.DataFrame:
    required = ["published", "symbol", "headline", "summary", "source", "url", "provider"]
    if frame.empty:
        return pd.DataFrame(columns=required + ["catalyst_score", "sentiment", "catalyst_reason"])
    frame = frame.copy()
    scored = frame.apply(
        lambda row: catalyst_score(str(row.get("headline", "")), str(row.get("summary", ""))),
        axis=1,
        result_type="expand",
    )
    scored.columns = ["catalyst_score", "sentiment", "catalyst_reason"]
    frame = pd.concat([frame.reset_index(drop=True), scored], axis=1)
    frame["published"] = pd.to_datetime(frame["published"], utc=True, errors="coerce")
    return frame.sort_values("published", ascending=False, na_position="last")


def combine_news(*frames: pd.DataFrame) -> pd.DataFrame:
    valid = [f for f in frames if f is not None and not f.empty]
    if not valid:
        return _score_news(pd.DataFrame())
    combined = pd.concat(valid, ignore_index=True)
    combined["dedupe"] = combined["headline"].fillna("").str.lower().str.replace(r"\W+", "", regex=True)
    combined = combined.drop_duplicates("dedupe").drop(columns="dedupe")
    return combined.sort_values("published", ascending=False, na_position="last")


def headline_symbol(text: str) -> str:
    match = re.search(r"\b[A-Z]{1,5}\b", text or "")
    return match.group(0) if match else ""
