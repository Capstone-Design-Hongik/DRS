#!/usr/bin/env python3
"""검색 알고리즘 변형(Noise) 저항성 평가 (Data Transformation & MRR, Hit@5) 스크립트"""
import os
import sys
import requests
import numpy as np

try:
    from tqdm import tqdm
except ImportError:
    # tqdm이 없는 환경을 위한 페이크 함수
    def tqdm(iterable, *args, **kwargs):
        return iterable

# 프로젝트 루트 폴더를 경로에 추가 (app 모듈을 불러오기 위함)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
# 이전에 만든 스크립트의 편의 함수(get_aapl_sketch)를 재활용하여 진짜 AAPL 데이터를 가져옵니다.
from evaluate_self_retrieval import get_aapl_sketch

BASE_URL = "http://localhost:8080"
TARGET_TICKER = "AAPL"
NUM_TRIALS = 30  # 왜곡 테스트 반복 횟수

def add_human_noise(sketch, noise_level=0.08):
    """사람이 차트를 따라 그릴 때 발생하는 여러 왜곡(Noise)을 무작위로 가하는 함수"""
    y = np.array(sketch, dtype=float)
    N = len(y)
    
    y_range = np.max(y) - np.min(y)
    if y_range == 0: y_range = 1
    
    # 1. 수전증 (자잘하게 떨리는 현상 - Gaussian Noise)
    y += np.random.normal(0, noise_level * y_range, N)
    
    # 2. 크기 왜곡 (위아래로 너무 길쭉하게 그리거나, 너무 찌그러지게 그리는 현상)
    # 실제 진폭을 0.6배 ~ 1.4배 사이로 왜곡
    scale_factor = np.random.uniform(0.6, 1.4)
    y = y * scale_factor
    
    # 3. 비대칭 시간축 늘리기 (차트 오른쪽을 급하게 그리는 현상 등)
    # 간단하게 구현하기 위해 전체 인덱스를 약간 흔든 후 보간(Interpolation) 합니다.
    x_orig = np.linspace(0, 1, N)
    
    # 0과 1 사이를 약간 구부러뜨리는 곡선(x^power)을 써서 시간의 쏠림 현상을 모사
    power = np.random.uniform(0.7, 1.3)
    x_warped = x_orig ** power
    
    # 왜곡된 시간축에서 다시 128개의 균일한 포인트를 샘플링
    y_warped = np.interp(x_orig, x_warped, y)
    
    return y_warped.tolist()

def main():
    print("=" * 60)
    print(f"🌪️ 변형 저항성 평가 (Robustness & MRR Test): {TARGET_TICKER}")
    print(f"   => 진짜 차트에 '손떨림, 스케일 붕괴, 시간축 쏠림'을 무작위로 준 뒤")
    print(f"   => 본래 주식을 얼마나 잘 찾는지 {NUM_TRIALS}회 반복 테스트합니다.")
    print("=" * 60)
    
    # 1. 서버 작동 확인
    try:
        requests.get(f"{BASE_URL}/health", timeout=5)
    except:
        print("❌ 서버가 켜져있지 않습니다! ./start_server.sh 를 먼저 실행해주세요.")
        return

    # 2. AAPL 원본 스케치 가져오기
    print("\n📦 데이터베이스에서 원본 차트 스케치를 가져오는 중...")
    base_sketch = get_aapl_sketch()
    if not base_sketch:
        print(f"❌ {TARGET_TICKER} 원본 데이터를 구할 수 없어 테스트를 중단합니다.")
        return
        
    print(f"✅ 원본 데이터 추출 성공! 이제 본격적으로 {NUM_TRIALS}회 테스트를 돌립니다.\n")

    api_endpoint = "/similar" if settings.data_source == "parquet" else "/similar_db"
    url = f"{BASE_URL}{api_endpoint}"
    
    # 지표 측정을 위한 변수들
    ranks = []                # 각 시도에서 내 주식이 몇 등을 했는지
    reciprocal_ranks = []     # 1등: 1.0, 2등: 0.5, 3등: 0.33, 못찾음: 0.0
    hits_at_5 = 0             # 5등 안에 든 횟수
    
    for i in tqdm(range(NUM_TRIALS), desc="🔥 인공 노이즈 테스트 진행 중"):
        
        # 사람의 손을 모사한 노이즈 낀 스케치 생성
        noisy_sketch = add_human_noise(base_sketch, noise_level=0.08)
        
        payload = {
            "y": noisy_sketch,
            "target_len": 128
        }

        try:
            response = requests.post(url, json=payload, timeout=5)
            response.raise_for_status()
            items = response.json().get('items', [])
            
            # 검색 결과에서 AAPL이 몇 등인지 확인
            target_rank = -1
            # 서버에서 Top 몇 개를 넘겨주는지에 따라 다를 수 있으나, 보통 상위 N개 배열이 돌아옵니다.
            for idx, item in enumerate(items):
                if item['ticker'] == TARGET_TICKER:
                    target_rank = idx + 1  # idx는 0부터 시작하므로 +1
                    break
            
            # 통계 기록
            if target_rank != -1:
                ranks.append(target_rank)
                reciprocal_ranks.append(1.0 / target_rank)
                if target_rank <= 5:
                    hits_at_5 += 1
            else:
                # Top 리스트(보통 100위 밖)에 아예 진입조차 못 함 = 패널티 순위(예: 100위) 부여
                ranks.append(100)
                reciprocal_ranks.append(0.0)
                
        except Exception as e:
            print(f"\n❌ API 통신 오류 발생 (시도 {i+1}): {e}")
            ranks.append(100)
            reciprocal_ranks.append(0.0)
            
    # 최종 점수 계산
    mrr_score = np.mean(reciprocal_ranks)
    hit_at_5_rate = (hits_at_5 / NUM_TRIALS) * 100
    avg_rank = np.mean(ranks)
    
    print("\n" + "=" * 60)
    print(f"📊 최종 평가 리포트 (MRR & Hit@5)")
    print("=" * 60)
    print(f" 🎯 Hit@5 (상위 5위 안에 포함될 확률): {hit_at_5_rate:.1f}%")
    print(f" 🏆 MRR (정답을 상위권으로 끌어올리는 힘): {mrr_score:.4f} (1.0 만점)")
    print(f" 📉 평균 순위: {avg_rank:.1f}위")
    print("=" * 60)
    
    print("\n📝 [결과 해석 가이드]")
    print("- Hit@5 가 80% 이상이라면, 사람은 삐뚤빼뚤 그리더라도 시스템이 찰떡같이 5위 안에 정답을 보여준다는 뜻입니다.")
    print("- MRR이 0.5 이상이라면, 평균적으로 항상 2등 이내로 정답을 찾아낸다는 뜻입니다.")
    print("- 노이즈가 강하게 들어갔는데도 점수가 높다면 알고리즘(DTW/정규화 등)이 아주 튼튼하다는 증거입니다!")

if __name__ == "__main__":
    main()
