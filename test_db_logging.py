#!/usr/bin/env python3
"""DB 접근 로그 테스트 스크립트"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from app.config import settings
from app import db_io

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("=" * 70)
print("PostgreSQL DB 접근 로그 테스트")
print("=" * 70)
print()

# 1. 연결 풀 초기화
print("1️⃣ PostgreSQL 연결 풀 초기화...")
print()
db_io.init_pool(
    host=settings.pg_host,
    port=settings.pg_port,
    database=settings.pg_database,
    user=settings.pg_user,
    password=settings.pg_password,
    minconn=settings.pg_min_conn,
    maxconn=settings.pg_max_conn
)

print()
print("=" * 70)

# 2. 세그먼트 개수 조회
print("2️⃣ 세그먼트 개수 조회...")
print()
count = db_io.get_segment_count()

print()
print("=" * 70)

# 3. 모든 세그먼트 조회
print("3️⃣ 모든 MA20 세그먼트 조회...")
print()
vectors, tickers, metadata = db_io.fetch_all_segments(ma_type="MA20")

print()
print("=" * 70)
print(f"✅ 테스트 완료!")
print(f"   - 총 세그먼트 수: {count:,}")
print(f"   - 로드된 벡터: {vectors.shape}")
print(f"   - 고유 티커: {len(set(tickers))}")
print("=" * 70)

# 4. 연결 풀 종료
db_io.close_pool()
