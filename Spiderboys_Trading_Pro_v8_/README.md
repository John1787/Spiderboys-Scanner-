# Spiderboys Trading Pro v8

Version 8 introduces the Spider AI Command Center and a unified market-data engine.

## Key fix

The Trade Plan crash was caused by an inconsistent return signature. Every chart request now returns exactly:

```python
bars, mode, source_note
```

The Trade Plan and Command Center use a unified exception-safe payload, so unavailable endpoints produce visible notes rather than crashing the page.

## Features

- Shared active ticker across the app
- Spider AI rule-based setup summary
- Saved watchlist for the current session
- Live or clearly labeled demo chart fallback
- Live quote, profile and company-news retrieval
- Interactive position sizing and checklist
- Visual equity and setup analytics
- Live order submission remains disabled

## GitHub root layout

Upload the contents of this folder directly to the repository root:

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
