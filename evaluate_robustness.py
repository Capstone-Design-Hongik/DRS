#!/usr/bin/env python3
"""검색 알고리즘 변형(Noise) 저항성 다중 평가 (Data Transformation & MRR, Hit@5) 스크립트"""
import os
import sys
import requests
import numpy as np

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, *args, **kwargs):
        return iterable

# 프로젝트 루트 폴더를 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from evaluate_self_retrieval import get_reference_sketch

BASE_URL = "http://localhost:8080"
TARGET_TICKERS = ["NFLX", "MSFT", "NVDA", "AMZN", "META", "GOOG", "INTC", "AMD", "DIS", "CRM"]
NUM_TRIALS = 15  # 왜곡 테스트 반복 횟수

def add_human_noise(sketch, noise_level=0.08):
    y = np.array(sketch, dtype=float)
    N = len(y)
    
    y_range = np.max(y) - np.min(y)
    if y_range == 0: y_range = 1
    
    y += np.random.normal(0, noise_level * y_range, N)
    
    scale_factor = np.random.uniform(0.6, 1.4)
    y = y * scale_factor
    
    x_orig = np.linspace(0, 1, N)
    power = np.random.uniform(0.7, 1.3)
    x_warped = x_orig ** power
    
    y_warped = np.interp(x_orig, x_warped, y)
    
    return y_warped.tolist()

def main():
    print("=" * 60)
    print("🚀 다중 종목 변형 저항성 연속 테스트 시작!")
    print(f"진행할 10개 종목: {TARGET_TICKERS}")
    print("=" * 60)
    
    try:
        requests.get(f"{BASE_URL}/health", timeout=5)
    except:
        print("❌ 서버가 켜져있지 않습니다! ./start_server.sh 를 먼저 실행해주세요.")
        return

    for target_ticker in TARGET_TICKERS:
        print("\n\n" + "*" * 60)
        print(f"🌪️ 변형 저항성 평가 (Robustness & MRR Test): {target_ticker}")
        print(f"   => 진짜 차트에 '손떨림, 스케일 붕괴, 시간축 쏠림'을 무작위로 준 뒤")
        print(f"   => 본래 주식을 얼마나 잘 찾는지 {NUM_TRIALS}회 반복 테스트합니다.")
        print("*" * 60)
        
        print("\n📦 데이터베이스에서 원본 차트 스케치를 가져오는 중...")
        base_sketch = get_reference_sketch(target_ticker)
        if not base_sketch:
            print(f"❌ {target_ticker} 원본 데이터를 구할 수 없어 해당 종목은 건너뜁니다.")
            continue
            
        print(f"✅ 원본 데이터 추출 성공! 이제 본격적으로 {NUM_TRIALS}회 테스트를 돌립니다.\n")

        api_endpoint = "/similar" if settings.data_source == "parquet" else "/similar_db"
        url = f"{BASE_URL}{api_endpoint}"
        
        ranks = []
        reciprocal_ranks = []
        hits_at_5 = 0
        
        for i in tqdm(range(NUM_TRIALS), desc=f"🔥 {target_ticker} 노이즈 테스트 중"):
            
            noisy_sketch = add_human_noise(base_sketch, noise_level=0.08)
            
            payload = {
                "y": noisy_sketch,
                "target_len": 128
            }

            try:
                import time
                time.sleep(1) # 서버 과부하 방지
                response = requests.post(url, json=payload, timeout=120)
                response.raise_for_status()
                items = response.json().get('items', [])
                
                target_rank = -1
                for idx, item in enumerate(items):
                    if item['ticker'] == target_ticker:
                        target_rank = idx + 1
                        break
                
                if target_rank != -1:
                    ranks.append(target_rank)
                    reciprocal_ranks.append(1.0 / target_rank)
                    if target_rank <= 5:
                        hits_at_5 += 1
                else:
                    ranks.append(100)
                    reciprocal_ranks.append(0.0)
                    
            except Exception as e:
                print(f"\n❌ API 통신 오류 발생 (시도 {i+1}): {e}")
                ranks.append(100)
                reciprocal_ranks.append(0.0)
                
        mrr_score = np.mean(reciprocal_ranks)
        hit_at_5_rate = (hits_at_5 / NUM_TRIALS) * 100
        avg_rank = np.mean(ranks)
        
        print("\n" + "=" * 50)
        print(f"📊 {target_ticker} 최종 평가 리포트")
        print("=" * 50)
        print(f" 🎯 Hit@5: {hit_at_5_rate:.1f}%")
        print(f" 🏆 MRR: {mrr_score:.4f}")
        print(f" 📉 평균 순위: {avg_rank:.1f}위")
        print("=" * 50)

    print("\n✅ 모든 10개 종목의 노이즈 테스트가 완료되었습니다! 수고하셨습니다 👏")

if __name__ == "__main__":
    main()
