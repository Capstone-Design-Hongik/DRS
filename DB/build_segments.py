# build_segments.py
# prices → MA20/30 → 90영업일 구간 → 128 길이 리샘플 + Z정규화 → graph_segments 저장

import os
import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

PG_CONN_STR = (
    f"host={os.getenv('PG_HOST')} "
    f"port={os.getenv('PG_PORT')} "
    f"dbname={os.getenv('PG_DB')} "
    f"user={os.getenv('PG_USER')} "
    f"password={os.getenv('PG_PASSWORD')}"
)

OUT_LEN   = 128        # 벡터 길이
SEG_DAYS  = 90         # 한 구간 길이(영업일)
VOL_MIN, VOL_MAX = 0.2, 2.0   # 변동성 컷(정규화 후 표준편차 범위)
TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"]  # 필요 시 tickers_list.txt 읽어도 됨
CLEAR_BEFORE_INSERT = True     # 같은 티커/MA 재생성 시 기존 기록 삭제

def resample_z(y: np.ndarray, out_len=128) -> np.ndarray:
    x_old = np.linspace(0, 1, len(y), dtype=np.float32)
    x_new = np.linspace(0, 1, out_len, dtype=np.float32)
    y_new = np.interp(x_new, x_old, y.astype(np.float32))
    y_new = (y_new - y_new.mean()) / (y_new.std() + 1e-8)  # Z-정규화
    return y_new

def fetch_adj_close(conn, ticker: str) -> pd.DataFrame | None:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT trade_date, adj_close
            FROM prices
            WHERE ticker=%s
            ORDER BY trade_date
        """, (ticker,))
        rows = cur.fetchall()
    if not rows:
        return None
    return pd.DataFrame(rows, columns=["date", "adj"])

def insert_segments(conn, rows):
    if not rows:
        return
    with conn.cursor() as cur:
        execute_batch(cur, """
            INSERT INTO graph_segments
              (ticker, segment_start, segment_end, ma_type, vector, volatility)
            VALUES
              (%s, %s, %s, %s, %s, %s)
        """, rows, page_size=1000)
    conn.commit()

def build_for_ticker(conn, ticker: str, ma_window: int):
    df = fetch_adj_close(conn, ticker)
    if df is None or df.empty:
        print(f"[WARN] {ticker}: no adj_close in prices (skip)")
        return

    # 이동평균 계산
    df["ma"] = df["adj"].rolling(ma_window).mean()
    df = df.dropna(subset=["ma"]).reset_index(drop=True)

    vals = df["ma"].to_numpy(dtype=np.float32)
    dates = df["date"].tolist()
    rows = []

    for i in range(0, len(vals) - SEG_DAYS + 1):
        win = vals[i:i+SEG_DAYS]
        vec = resample_z(win, OUT_LEN)
        stdev = float(np.std(vec))
        if VOL_MIN <= stdev <= VOL_MAX:
            ws, we = dates[i], dates[i+SEG_DAYS-1]
            ma_type = f"MA{ma_window}"  # "MA20" 또는 "MA30"
            rows.append((ticker, ws, we, ma_type, list(map(float, vec)), stdev))

    # 중복 방지를 원하면 기존 것 삭제
    if CLEAR_BEFORE_INSERT:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM graph_segments
                WHERE ticker=%s AND ma_type=%s
            """, (ticker, f"MA{ma_window}"))
        conn.commit()

    insert_segments(conn, rows)
    print(f"[OK] {ticker} MA{ma_window}: inserted {len(rows)} segments")

def fetch_all_tickers(conn) -> list[str]:
    """DB에서 모든 티커 조회"""
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT ticker FROM prices ORDER BY ticker;")
        rows = cur.fetchall()
    return [r[0] for r in rows]


def main():
    print("[DEBUG] DB:", os.getenv("PG_DB"))
    conn = psycopg2.connect(PG_CONN_STR)

    # DB에서 모든 티커 조회
    tickers = fetch_all_tickers(conn)
    print(f"[INFO] Found {len(tickers)} tickers in DB")
    print(f"[INFO] Processing MA20 only...")

    # MA20만 처리
    for t in tickers:
        build_for_ticker(conn, t, 20)

    conn.close()
    print("Done.")

if __name__ == "__main__":
    main()
