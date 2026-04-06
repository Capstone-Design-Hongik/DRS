#!/usr/bin/env python3
"""검색 알고리즘 완벽 일치 검사 (Self-retrieval Test) 스크립트"""
import os
import sys
import requests
import numpy as np

# 프로젝트 루트 폴더를 경로에 추가 (tmp 폴더 안에 있으므로 parent directory로 추가)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

BASE_URL = "http://localhost:8080"
TARGET_TICKER = "AAPL"  # 애플 데이터로 테스트

def get_aapl_sketch():
    """DB 또는 캐시에서 AAPL 스케치(벡터)를 가져옵니다."""
    print(f"📦 현재 설정된 데이터 소스(data_source): {settings.data_source}")
    
    # 1. PostgreSQL DB 사용 시
    if settings.data_source == "postgresql":
        try:
            from app.db_io import init_pool, fetch_latest_ma20_for_tickers, close_pool
            print("   PostgreSQL DB에 연결하여 데이터를 가져옵니다...")
            init_pool(
                host=settings.pg_host,
                port=settings.pg_port,
                database=settings.pg_database,
                user=settings.pg_user,
                password=settings.pg_password,
            )
            data_dict = fetch_latest_ma20_for_tickers([TARGET_TICKER], limit=1)
            close_pool()
            
            if TARGET_TICKER in data_dict:
                return data_dict[TARGET_TICKER].tolist()
        except Exception as e:
            print(f"⚠️ PostgreSQL 연결/조회 실패: {e}")
            print("   아직 DB 환경 세팅이 완료되지 않은 것 같습니다. Parquet 방식으로 우회 시도합니다.")

    # 2. Parquet 캐시 파일 혹은 DB 실패 시 우회
    try:
        from app.data_io import load_ma20_parquet
        print("   로컬 파일(Parquet DB)에서 데이터를 스캔하여 가져옵니다...")
        df = load_ma20_parquet()
        if df is not None and not df.empty:
            if 'ticker' in df.columns and 'vector' in df.columns:
                # 새 포맷
                row = df[df['ticker'] == TARGET_TICKER]
                if not row.empty:
                    vec = row.iloc[0]['vector']
                    if isinstance(vec, list): return vec
                    if isinstance(vec, np.ndarray): return vec.tolist()
            else:
                # 옛날 포맷
                if TARGET_TICKER in df.columns:
                    # 마지막 128일 데이터 (target_len)
                    series = df[TARGET_TICKER].dropna().tail(settings.target_len)
                    from app.features import normalize_pipeline
                    return normalize_pipeline(series.values, target_len=settings.target_len).tolist()
    except Exception as e:
        print(f"⚠️ Parquet 로드 실패: {e}")

    # 3. 최후의 수단: 실시간 다운로드 (야후 파이낸스)
    print("   DB와 캐시에 데이터가 없으므로 웹(야후 파이낸스)에서 실시간으로 가져옵니다...")
    from app.data_io import download_ohlc, last_n_days, compute_ma20
    from app.features import normalize_pipeline
    raw = download_ohlc([TARGET_TICKER], period="2y")
    raw = last_n_days(raw, n=settings.target_len)
    ma20 = compute_ma20(raw)
    series = ma20[TARGET_TICKER].dropna().values
    return normalize_pipeline(series, target_len=settings.target_len).tolist()

def main():
    print("=" * 60)
    print(f"🚀 완벽 일치 검사 (Self-retrieval Test): {TARGET_TICKER}")
    print("   내 DB에 있는 데이터를 그대로 검색했을 때, 본인이 1위로 나오는지 확인합니다.")
    print("=" * 60)
    
    # 1. 서버 작동 확인
    try:
        requests.get(f"{BASE_URL}/health", timeout=5)
    except:
        print("❌ 서버가 켜져있지 않습니다! ./start_server.sh 를 먼저 실행해주세요.")
        return

    # 2. 데이터 가져오기
    sketch_vec = get_aapl_sketch()
    if not sketch_vec:
        print(f"❌ {TARGET_TICKER} 데이터를 어디에서도 구할 수 없었습니다.")
        return
        
    print(f"✅ {TARGET_TICKER} 데이터 추출 성공! (길이: {len(sketch_vec)})")

    # 3. 가져온 AAPL 스케치(배열)를 그대로 우리 검색엔진 API에 던져봅니다.
    print(f"\n🔍 추출한 '{TARGET_TICKER}' 데이터로 검색 엔진에 질의를 보냅니다...")
    payload = {
        "y": sketch_vec,
        "target_len": 128
    }

    # 현재 서버가 parquet 모드라면 /similar, postgresql 이면 /similar_db
    api_endpoint = "/similar" if settings.data_source == "parquet" else "/similar_db"
    print(f"   (서버 설정에 맞추어 {api_endpoint} 엔드포인트 사용)")

    try:
        response = requests.post(f"{BASE_URL}{api_endpoint}", json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        top_k_items = result['items'][:5]
        
        print("\n🏆 검색된 상위 5개 결과 (우리의 목표는 1위가 AAPL이 나오는 것):")
        for idx, item in enumerate(top_k_items):
            print(f"   {idx+1}위. {item['ticker']} (유사도 {item['score']:.4f})")
            
        print("\n⏳ 채점 중...")
        
        # 4. 정말로 1위가 AAPL인지 채점하기
        if not top_k_items:
            print("❌ 검색 결과가 한 개도 안 나왔습니다.")
            return
            
        rank_1_ticker = top_k_items[0]['ticker']
        rank_1_score = top_k_items[0]['score']
        
        if rank_1_ticker == TARGET_TICKER:
            print(f"✅ [테스트 통과!] {TARGET_TICKER} 데이터를 넣었을 때 스스로를 1위로 정확히 찾아냈습니다!")
            if rank_1_score > 0.99:
                print(f"   => 완벽합니다! 유사도 점수도 {rank_1_score:.4f}로 거의 100% 일치합니다.")
        else:
            print(f"❌ [테스트 실패!] {TARGET_TICKER}를 검색했는데 엉뚱한 {rank_1_ticker}가 1위로 나왔습니다.")
            
    except Exception as e:
        print(f"❌ API 통신 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
