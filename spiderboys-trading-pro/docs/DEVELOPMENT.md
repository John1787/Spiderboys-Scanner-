# Local Development

## First setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest
streamlit run app.py
```

On Windows, activate with `.venv\\Scripts\\activate`.

## Before committing

```bash
python scripts/check_project.py
pytest
```

## Branch naming

- `feature/live-market-data`
- `feature/journal-screenshots`
- `fix/scanner-filter`
- `release/6.2.0`
