# Spiderboys Trading Pro — Flagship v6

A clean Streamlit-first trading workstation that launches with `app.py`.

## Included

- Elite momentum scanner and transparent eight-factor score
- TradingView one-click chart links
- TradingView Pine indicator and 12-symbol radar script
- Risk-first trade planner and daily lock controls
- Full trading journal with CSV backup/restore
- Performance analytics, replay training and execution coach
- Simulated training data so the app starts without API keys

## Deploy on Streamlit Community Cloud

1. Unzip this package.
2. Upload **all files and folders** to one GitHub repository.
3. In Streamlit Community Cloud, create or edit the app.
4. Choose the repository and branch.
5. Set the main file path to `app.py`.
6. Deploy or reboot.

Do not upload the ZIP itself into the repository. Upload the unzipped contents.

## Local launch

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Important

The included stock prices and headlines are simulated training data. The app does not place broker orders. Journal storage on Streamlit Community Cloud may reset during a redeploy, so use the built-in CSV backup.
