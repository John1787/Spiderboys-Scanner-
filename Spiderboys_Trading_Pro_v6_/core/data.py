from pathlib import Path
import pandas as pd

def load_market(base_dir):
    df = pd.read_csv(Path(base_dir)/"data"/"market.csv")
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df

def load_journal(base_dir):
    return pd.read_csv(Path(base_dir)/"data"/"journal.csv")

def load_news(base_dir):
    return pd.read_csv(Path(base_dir)/"data"/"news.csv")

def load_indices(base_dir):
    df = pd.read_csv(Path(base_dir)/"data"/"indices.csv")
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df

def load_alerts(base_dir):
    return pd.read_csv(Path(base_dir)/"data"/"alerts.csv")
