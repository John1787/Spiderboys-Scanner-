from pathlib import Path
import pandas as pd

JOURNAL_COLUMNS = [
    "date","weekday","ticker","side","setup","entry","exit","stop","shares","pnl",
    "r_multiple","win","execution_grade","emotion","time_bucket","catalyst",
    "followed_plan","chased","moved_stop","mistake","lesson","screenshot_url"
]

def _read(path, columns=None):
    if path.exists() and path.stat().st_size:
        try:
            return pd.read_csv(path)
        except Exception:
            pass
    return pd.DataFrame(columns=columns or [])

def load_market(base_dir):
    df=_read(Path(base_dir)/"data"/"market.csv")
    if not df.empty and "datetime" in df: df["datetime"]=pd.to_datetime(df["datetime"],errors="coerce")
    return df

def load_journal(base_dir):
    df=_read(Path(base_dir)/"data"/"journal.csv", JOURNAL_COLUMNS)
    for col in JOURNAL_COLUMNS:
        if col not in df.columns: df[col]=pd.NA
    return df[JOURNAL_COLUMNS]

def save_journal(base_dir, df):
    path=Path(base_dir)/"data"/"journal.csv"
    path.parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(path,index=False)

def append_journal(base_dir, record):
    df=load_journal(base_dir)
    out=pd.concat([df,pd.DataFrame([record])],ignore_index=True)
    save_journal(base_dir,out)
    return out

def replace_journal(base_dir, uploaded):
    incoming=pd.read_csv(uploaded)
    for col in JOURNAL_COLUMNS:
        if col not in incoming.columns: incoming[col]=pd.NA
    incoming=incoming[JOURNAL_COLUMNS]
    save_journal(base_dir,incoming)
    return incoming

def load_news(base_dir): return _read(Path(base_dir)/"data"/"news.csv")
def load_indices(base_dir):
    df=_read(Path(base_dir)/"data"/"indices.csv")
    if not df.empty and "datetime" in df: df["datetime"]=pd.to_datetime(df["datetime"],errors="coerce")
    return df
def load_alerts(base_dir): return _read(Path(base_dir)/"data"/"alerts.csv")
