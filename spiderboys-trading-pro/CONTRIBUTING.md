# Contributing

1. Create a branch from `main`: `feature/short-name` or `fix/short-name`.
2. Make one focused change.
3. Run `python scripts/check_project.py` and `pytest`.
4. Open a pull request and describe the deployment impact.
5. Merge only after CI passes.

Never commit API keys, brokerage credentials, webhook secrets, personal trading records, or `.streamlit/secrets.toml`.
