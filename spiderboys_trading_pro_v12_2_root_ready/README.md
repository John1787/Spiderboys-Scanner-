# Spiderboys Trading Pro v12.2

## Dark Scanner Decision Engine

Version 12.2 removes the bright white scanner backgrounds and adds a more disciplined decision layer.

### Dark scanner interface

- Dark slate scanner cells
- Charcoal headers
- Dark select boxes and number inputs
- Muted green for strength
- Amber for caution
- Red for high risk and avoid
- Cyan/teal for unusual volume and low float
- Dark fallback rendering if advanced cell styling ever fails

### Decision engine

Every scanner row now receives:

- Momentum Quality: 0–100
- Decision: READY, WAIT, or AVOID
- Structural Risk: LOW, MODERATE, or HIGH
- Primary warning
- Setup context
- Spread check
- Room-to-resistance check
- Catalyst and pullback-quality check
- Above-VWAP check
- Chase-risk check

READY does not mean automatic entry. It means the available structure, volume, catalyst, and risk filters are aligned enough to watch for the actual trigger.

### Risk Guard

The Live Scanner now includes:

- Account size
- Risk-per-trade percentage
- Daily loss limit
- Maximum daily trades
- Current daily P/L
- Automatic risk lock
- Position-size preview
- 1R and 2R targets

When the daily loss limit or maximum trade count is reached, the scanner stays visible but suggested position size becomes zero.

### Market alignment

When Finnhub is connected, the scanner checks SPY and QQQ and labels the broad tape:

- RISK-ON
- MIXED
- RISK-OFF

This does not replace stock-specific confirmation.

### News risk filter

Recent headlines are checked for terms related to:

- Offerings and dilution
- Reverse splits
- Bankruptcy
- Investigations and lawsuits
- Downgrades
- Delisting
- Warrants
- Going-concern language

Positive catalyst terms such as contracts, approvals, partnerships, awards, patents, and regulatory clearance are also identified.

### Data note

Scanner setup metrics are derived from the bundled training data in this build. Quotes, company profiles, news, and SPY/QQQ alignment are live only when the connected provider endpoints respond.

### Deployment

Upload the contents of this folder directly to the GitHub repository root.

Main file:

```text
app.py
```
