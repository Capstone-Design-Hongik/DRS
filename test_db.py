#!/usr/bin/env python3
"""PostgreSQL 연결 및 데이터 확인 스크립트"""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

# 연결 정보
conn_params = {
    'host': os.getenv('PG_HOST', '172.17.240.1'),
    'port': int(os.getenv('PG_PORT', 5433)),
    'database': os.getenv('PG_DATABASE', 'drs_db'),
    'user': os.getenv('PG_USER', 'postgres'),
    'password': os.getenv('PG_PASSWORD', '')
}

print("=" * 60)
print("PostgreSQL 연결 테스트")
print("=" * 60)
print(f"Host: {conn_params['host']}:{conn_params['port']}")
print(f"Database: {conn_params['database']}")
print(f"User: {conn_params['user']}")
print()

try:
    # 연결
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()

    print("✅ 연결 성공!")
    print()

    # 테이블 확인
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    tables = cur.fetchall()
    print(f"📊 테이블 목록: {[t[0] for t in tables]}")
    print()

    # graph_segments 테이블 확인
    if ('graph_segments',) in tables:
        # 총 레코드 수
        cur.execute("SELECT COUNT(*) FROM graph_segments")
        total = cur.fetchone()[0]
        print(f"📈 graph_segments 테이블:")
        print(f"  - 총 세그먼트 수: {total:,}")

        # MA 타입별 개수
        cur.execute("""
            SELECT ma_type, COUNT(*)
            FROM graph_segments
            GROUP BY ma_type
        """)
        ma_counts = cur.fetchall()
        print(f"  - MA 타입별 개수:")
        for ma_type, count in ma_counts:
            print(f"    • {ma_type}: {count:,}")

        # 티커 수
        cur.execute("SELECT COUNT(DISTINCT ticker) FROM graph_segments WHERE ma_type = 'MA20'")
        ticker_count = cur.fetchone()[0]
        print(f"  - MA20 기준 고유 티커 수: {ticker_count:,}")

        # 샘플 데이터
        cur.execute("""
            SELECT ticker, segment_start, segment_end,
                   array_length(vector, 1) as vector_dim
            FROM graph_segments
            WHERE ma_type = 'MA20'
            LIMIT 3
        """)
        samples = cur.fetchall()
        print(f"\n  📝 샘플 데이터 (최근 3개):")
        for ticker, start, end, dim in samples:
            print(f"    • {ticker}: {start} ~ {end} (벡터 차원: {dim})")
    else:
        print("⚠️  graph_segments 테이블이 없습니다!")

    cur.close()
    conn.close()

    print()
    print("=" * 60)
    print("✅ 모든 확인 완료!")
    print("=" * 60)

except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
