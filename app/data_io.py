import yfinance as yf
import pandas as pd
from pathlib import Path
import time, json

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

def download_ohlc(tickers, period="2y"):
    df = yf.download(
        tickers, period=period, interval="1d",
        auto_adjust=True, group_by="ticker", threads=True, progress=False
    )
    return df

def last_n_days(df, n=365):
    return df.loc[df.index >= (df.index.max() - pd.Timedelta(days=n))]

def compute_ma20(ohlc_multi):
    out = {}
    # 멀티컬럼: (Ticker, Field)
    for t in ohlc_multi.columns.levels[0]:
        if (t, 'Close') in ohlc_multi.columns:
            s = ohlc_multi[(t, 'Close')].dropna()
            if len(s) >= 25:
                out[t] = s.rolling(20).mean().dropna()
    return out

def save_ma20_parquet(ma_dict):
    df = pd.DataFrame({t: s for t, s in ma_dict.items()}).dropna(how="all")
    p = DATA_DIR / "ma20.parquet"
    df.to_parquet(p)
    return str(p)

def save_meta(meta: dict):
    (DATA_DIR / "meta.json").write_text(json.dumps(meta, indent=2))

def load_ma20_parquet():
    p = DATA_DIR / "ma20.parquet"
    return pd.read_parquet(p) if p.exists() else None
