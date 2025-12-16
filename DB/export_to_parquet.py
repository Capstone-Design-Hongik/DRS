#!/usr/bin/env python3
"""
Render PostgreSQL DB에서 graph_segments 테이블의 데이터를 parquet 파일로 내보내기
"""
import os
import psycopg2
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# .env 로드
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

# Render DB 연결
PG_CONN_STR = (
    f"host={os.getenv('PG_HOST')} "
    f"port={os.getenv('PG_PORT')} "
    f"dbname={os.getenv('PG_DB')} "
    f"user={os.getenv('PG_USER')} "
    f"password={os.getenv('PG_PASSWORD')}"
)

print(f"[INFO] Connecting to Render DB: {os.getenv('PG_DB')}")
conn = psycopg2.connect(PG_CONN_STR)

# 최신 MA20 세그먼트만 가져오기 (티커당 1개)
print("[INFO] Fetching latest MA20 segments from Render DB...")
query = """
    SELECT DISTINCT ON (ticker)
        ticker,
        segment_start,
        segment_end,
        vector,
        volatility
    FROM graph_segments
    WHERE ma_type = 'MA20'
    ORDER BY ticker, segment_end DESC;
"""

df = pd.read_sql_query(query, conn)
conn.close()

print(f"[INFO] Fetched {len(df)} segments")

# vector 컬럼을 numpy array로 변환 (리스트로 저장되어 있을 수 있음)
if len(df) > 0:
    print("[INFO] Converting vector column...")
    # vector가 문자열이나 리스트로 저장되어 있을 수 있으므로 변환
    if isinstance(df['vector'].iloc[0], str):
        # PostgreSQL에서 array로 저장된 경우 문자열로 나올 수 있음
        import ast
        df['vector'] = df['vector'].apply(lambda x: np.array(ast.literal_eval(x)) if isinstance(x, str) else np.array(x))
    elif not isinstance(df['vector'].iloc[0], np.ndarray):
        df['vector'] = df['vector'].apply(lambda x: np.array(x))

# Parquet로 저장
output_path = os.path.join(BASE_DIR, "..", "data", "ma20.parquet")
print(f"[INFO] Saving to {output_path}...")
df.to_parquet(output_path, index=False, engine='pyarrow')

print(f"[OK] Exported {len(df)} segments to ma20.parquet")
print(f"[INFO] File size: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")

# 티커 목록 출력
tickers = sorted(df['ticker'].unique())
print(f"\n[INFO] Total tickers: {len(tickers)}")
print(f"[INFO] First 20 tickers: {', '.join(tickers[:20])}")
if len(tickers) > 20:
    print(f"[INFO] Last 20 tickers: {', '.join(tickers[-20:])}")
