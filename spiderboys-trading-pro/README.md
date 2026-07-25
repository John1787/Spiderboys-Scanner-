# Spiderboys Trading Pro

A Streamlit-first momentum trading workstation with a transparent scanner, TradingView tools, risk controls, a full trading journal, analytics, replay training, and an upgrade path for live market data.

## Current release

**v6.2.0 — Software Project Foundation**

The repository starts in demo/training mode and requires no API keys.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Test

```bash
python scripts/check_project.py
pytest
```

## Deploy

Connect this GitHub repository to Streamlit Community Cloud and set the main file to `app.py`. Future updates should be committed to GitHub rather than uploaded as replacement ZIP files.

## Repository map

- `app.py` — Streamlit entry point
- `core/` — scanner, risk, analytics, storage, and TradingView helpers
- `providers/` — demo and future live-market-data integrations
- `tradingview/` — Pine Script indicator and radar
- `tests/` — automated tests
- `docs/` — architecture, deployment, development, releases, and live-data roadmap
- `.github/workflows/ci.yml` — automatic checks on GitHub

## Safety and scope

The bundled feed is simulated. This project is a research and training workstation, not financial advice. It does not place broker orders. Live data and execution require separate provider agreements, entitlements, security controls, testing, and persistent storage.
