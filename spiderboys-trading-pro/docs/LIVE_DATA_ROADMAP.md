# Live Data Roadmap

## Milestone 6.2 — Read-only live scanner

- Implement a provider under `providers/`.
- Normalize live bars into the columns expected by `core.engine.scan_setups`.
- Add rate-limit handling, connection status, delayed-data labeling, and fallback to demo mode.
- Keep broker execution disabled.

## Milestone 6.3 — Persistent journal

- Add an authenticated cloud database.
- Store trades, screenshots, notes, alert events, and versioned edits.
- Add scheduled exports and restore testing.

## Milestone 6.4 — Paper-trading integration

- Add broker paper-account connectivity.
- Require server-side risk validation for every order.
- Log orders, fills, rejects, cancels, and position reconciliation.

## Milestone 7.0 — Controlled live execution

Live execution should remain opt-in and unavailable until paper trading, reconciliation, kill switches, permissions, audit logs, and failure testing are complete.
