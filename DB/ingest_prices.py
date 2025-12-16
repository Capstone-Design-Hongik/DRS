# ingest_prices.py
# ------------------------------------------------------------
# NASDAQ API → 티커 자동 수집 → Yahoo Finance → PostgreSQL 업서트 (최종)
# - NASDAQ 스크리너 API로 티커 자동 수집(get_nasdaq_tickers)
# - .env 로 DB 접속정보 로드 (파일명은 정확히 ".env")
# - yfinance: group_by="column"으로 단일 컬럼 보장, auto_adjust=True
# - 컬럼 정규화(멀티인덱스/이상 컬럼 대응), NaN은 스킵(0으로 넣지 않음)
# - execute_batch 업서트
# ------------------------------------------------------------

import os
import math
from typing import Dict, List

import requests
import yfinance as yf
import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

# ===== .env 로드 (.py와 같은 폴더의 .env를 확실히 읽도록 절대경로 사용) =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

PG_CONN_STR = (
    f"host={os.getenv('PG_HOST')} "
    f"port={os.getenv('PG_PORT')} "
    f"dbname={os.getenv('PG_DB')} "
    f"user={os.getenv('PG_USER')} "
    f"password={os.getenv('PG_PASSWORD')}"
)

# ===== 기본 티커(백업용) =====
FALLBACK_TICKERS: List[str] = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"]


def read_tickers_json(limit: int = 1000) -> List[str] | None:
    """DRS/data/tickers_nasdaq.json에서 티커 읽기 (상위 limit개)."""
    import json
    # DB/ 폴더에서 ../data/tickers_nasdaq.json 찾기
    json_path = os.path.join(BASE_DIR, "..", "data", "tickers_nasdaq.json")
    if os.path.exists(json_path):
        try:
            with open(json_path) as f:
                all_tickers = json.load(f)
            # 상위 limit개만 반환
            ts = all_tickers[:limit] if len(all_tickers) > limit else all_tickers
            return ts if ts else None
        except Exception as e:
            print(f"[WARN] Failed to read tickers_nasdaq.json: {e}")
            return None
    return None


def read_tickers_file() -> List[str] | None:
    """tickers_list.txt가 있으면 그 목록 사용."""
    path = os.path.join(BASE_DIR, "tickers_list.txt")
    if os.path.exists(path):
        with open(path) as f:
            ts = [ln.strip() for ln in f if ln.strip()]
        return ts if ts else None
    return None


def get_nasdaq_tickers(limit: int = 200) -> List[str] | None:
    """
    NASDAQ 스크리너 API에서 티커 자동 수집.
    - 브라우저 헤더 필요(없으면 403)
    - limit: 가져올 종목 수
    """
    url = f"https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit={limit}"
    headers = {
        # 브라우저 흉내 (중요)
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.nasdaq.com/",
        "Origin": "https://www.nasdaq.com",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        rows = data["data"]["table"]["rows"]
        # 심볼만 추출 + 간단 필터(공백/하이픈/점 등 제거)
        tickers = []
        for r in rows:
            sym = r.get("symbol", "").strip().upper()
            # 보통 yfinance는 하이픈/점 포함 심볼도 처리하지만, 간단히 알파넘/점만 허용
            if sym and all(c.isalnum() or c == "." for c in sym):
                tickers.append(sym)
        # 중복 제거, 정렬
        tickers = sorted(set(tickers))
        return tickers if tickers else None
    except Exception as e:
        print(f"[WARN] NASDAQ API failed: {e}")
        return None


def resolve_tickers(limit: int = 1000) -> List[str]:
    """우선순위: tickers_nasdaq.json > tickers_list.txt > NASDAQ API > FALLBACK."""
    # 1. tickers_nasdaq.json 우선
    ts = read_tickers_json(limit=limit)
    if ts:
        print(f"[INFO] Using tickers_nasdaq.json ({len(ts)} symbols)")
        return ts

    # 2. tickers_list.txt
    ts = read_tickers_file()
    if ts:
        print(f"[INFO] Using tickers_list.txt ({len(ts)} symbols)")
        return ts

    # 3. NASDAQ API
    ts = get_nasdaq_tickers(limit=limit)
    if ts:
        print(f"[INFO] Using NASDAQ API ({len(ts)} symbols)")
        # 필요하면 파일로 저장(로그용)
        try:
            with open(os.path.join(BASE_DIR, "tickers_list.txt"), "w") as f:
                f.write("\n".join(ts))
            print("[INFO] Saved tickers_list.txt")
        except Exception:
            pass
        return ts

    # 4. FALLBACK
    print("[INFO] Using fallback tickers")
    return FALLBACK_TICKERS


def safe_float(x) -> float | None:
    """float 캐스팅; NaN/None이면 None 반환 (0으로 넣지 않기 위함)"""
    try:
        if x is None or (isinstance(x, float) and math.isnan(x)):
            return None
        return float(x)
    except Exception:
        return None


def safe_int(x) -> int | None:
    """int 캐스팅; NaN/None이면 None 반환"""
    try:
        if x is None or (isinstance(x, float) and math.isnan(x)):
            return None
        return int(x)
    except Exception:
        return None


def upsert_stock_meta(conn, ticker: str, info: Dict):
    """stocks 테이블 업서트"""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO stocks (ticker, company_name, exchange, sector, market_cap)
            VALUES (%s,%s,%s,%s,%s)
            ON CONFLICT (ticker) DO UPDATE SET
              company_name=EXCLUDED.company_name,
              exchange=EXCLUDED.exchange,
              sector=EXCLUDED.sector,
              market_cap=EXCLUDED.market_cap;
            """,
            (
                ticker,
                info.get("longName") or info.get("shortName") or None,
                info.get("exchange"),
                info.get("sector"),
                info.get("marketCap") or 0,
            ),
        )
    conn.commit()


def normalize_ohlcv_columns(df: pd.DataFrame, ticker: str) -> pd.DataFrame | None:
    """
    어떤 형태로 와도 Open/High/Low/Close/Volume/Adj Close 확보.
    - MultiIndex면 해당 ticker 슬라이스 또는 평탄화
    - 표준 컬럼명으로 매핑 실패 시 None 반환
    """
    if isinstance(df.columns, pd.MultiIndex):
        try:
            df = df.xs(ticker, axis=1, level=-1)
        except Exception:
            df.columns = ["_".join(map(str, c)).strip() for c in df.columns.to_list()]

    cols = list(df.columns)

    def pick(*cands):
        for c in cands:
            if c in cols:
                return c
        return None

    c_open = pick("Open", f"Open_{ticker}", "Price_Open", f"Price_Open_{ticker}")
    c_high = pick("High", f"High_{ticker}", "Price_High", f"Price_High_{ticker}")
    c_low = pick("Low", f"Low_{ticker}", "Price_Low", f"Price_Low_{ticker}")
    c_close = pick("Close", f"Close_{ticker}", "Price_Close", f"Price_Close_{ticker}")
    c_adj = pick("Adj Close", "Adj_Close", f"Adj Close_{ticker}", f"Adj_Close_{ticker}")
    c_vol = pick("Volume", f"Volume_{ticker}", "Price_Volume", f"Price_Volume_{ticker}")

    if not all([c_open, c_high, c_low, c_close, c_vol]):
        print(f"[WARN] columns missing → {cols[:10]}...")
        return None

    if not c_adj:
        df["Adj Close"] = df[c_close]
        c_adj = "Adj Close"

    rename_map = {
        c_open: "Open",
        c_high: "High",
        c_low: "Low",
        c_close: "Close",
        c_adj: "Adj Close",
        c_vol: "Volume",
    }
    df = df.rename(columns=rename_map)
    df = df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]]
    return df


def upsert_prices(conn, ticker: str, df: pd.DataFrame):
    """prices 테이블 대량 업서트 (정규화 + NaN 행 스킵)."""
    if df is None or df.empty:
        return

    df = normalize_ohlcv_columns(df, ticker)
    if df is None or df.empty:
        print(f"[WARN] {ticker}: unable to normalize columns. skipped.")
        return

    df = df.dropna(how="any")

    rows = []
    for idx, row in df.iterrows():
        trade_date = idx.date()
        open_ = safe_float(row["Open"])
        high_ = safe_float(row["High"])
        low_ = safe_float(row["Low"])
        close_ = safe_float(row["Close"])
        adjc_ = safe_float(row["Adj Close"])
        vol_ = safe_int(row["Volume"])
        if None in (open_, high_, low_, close_, adjc_, vol_):
            continue
        rows.append((ticker, trade_date, open_, high_, low_, close_, adjc_, vol_))

    if not rows:
        print(f"[WARN] {ticker}: no valid rows after cleaning. skipped.")
        return

    with conn.cursor() as cur:
        execute_batch(
            cur,
            """
            INSERT INTO prices (ticker, trade_date, open, high, low, close, adj_close, volume)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (ticker, trade_date) DO UPDATE SET
              open=EXCLUDED.open,
              high=EXCLUDED.high,
              low=EXCLUDED.low,
              close=EXCLUDED.close,
              adj_close=EXCLUDED.adj_close,
              volume=EXCLUDED.volume;
            """,
            rows,
            page_size=1000,
        )
    conn.commit()


def main():
    print("[DEBUG] will connect to DB:", os.getenv("PG_DB"))
    conn = psycopg2.connect(PG_CONN_STR)
    with conn.cursor() as cur:
        cur.execute("SELECT current_database();")
        print("[DEBUG] connected DB:", cur.fetchone()[0])

    # NASDAQ에서 자동 수집 (없으면 txt / 그래도 없으면 기본)
    all_tickers = resolve_tickers(limit=5364)  # 5364개 티커 사용 (필터링된 보통주)
    print(f"[INFO] Total tickers from file: {len(all_tickers)}")

    # DB에 이미 있는 ticker 조회
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT ticker FROM prices;")
        existing_tickers = {row[0] for row in cur.fetchall()}
    print(f"[INFO] Already in DB: {len(existing_tickers)} tickers")

    # 새로운 ticker만 필터링
    tickers = [t for t in all_tickers if t not in existing_tickers]
    print(f"[INFO] New tickers to add: {len(tickers)}")
    print(f"[INFO] First 20: {', '.join(tickers[:20])}"
          f"{' ...' if len(tickers) > 20 else ''}")

    if not tickers:
        print("[INFO] No new tickers to add. All tickers already in DB.")
        conn.close()
        return

    # 다운로드 & 업서트
    for idx, t in enumerate(tickers, 1):
        print(f"[{idx}/{len(tickers)}] Downloading {t}…")
        df = yf.download(
            t,
            period="18mo",  # 300거래일 (약 1.5년)
            interval="1d",
            auto_adjust=True,
            progress=False,
            group_by="column",
            threads=False,
        )
        if df is None or df.empty:
            print(f"[WARN] {t}: empty DataFrame (skip)")
            continue

        # 디버그: 컬럼 확인
        print("[DEBUG]", t, "columns:", list(df.columns)[:6])

        # 종목 메타 (실패 무시)
        try:
            info = yf.Ticker(t).info
        except Exception:
            info = {}

        try:
            upsert_stock_meta(conn, t, info)
            upsert_prices(conn, t, df)
            print(f"[OK] {t}: {len(df)} rows processed.")
        except Exception as e:
            print(f"[ERROR] {t}: {e}")

    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
