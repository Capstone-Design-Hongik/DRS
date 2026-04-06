#!/usr/bin/env python3
"""검색 알고리즘 정확도(Precision@K) 평가 스크립트"""
import requests
import numpy as np

# API 엔드포인트
BASE_URL = "http://localhost:8080"

# =====================================================================
# 1. 정답지 (Ground Truth) 준비
# 개발자님이 수동으로 확인한 "진짜 OOO 패턴"을 가진 종목 리스트입니다.
# 나중에 실제 테스트하실 때 진짜 정답 종목들로 안의 내용을 꽉 채워주세요!
# =====================================================================
GROUND_TRUTH = {
    "Head_And_Shoulders": ["ACHV", "ATAT", "BCML", "CDZI", "MIND", "MRCY"]
}

# 테스트용 이상적인 헤드앤숄더 스케치 생성 함수 (수학적 모델링)
def generate_head_and_shoulders():
    """3개의 가우시안(정규분포) 종 모양을 합성하여 완벽한 대칭의 헤드앤숄더 패턴 생성"""
    x = np.linspace(0, 100, 128) # 모델 입력 길이에 맞춰 128개 포인트 생성

    # 1. 왼쪽 어깨 (Left Shoulder): 위치=25, 높이=50, 너비=8
    left_shoulder = 50 * np.exp(-((x - 25) ** 2) / (2 * 8 ** 2))

    # 2. 머리 (Head): 위치=64(정중앙), 높이=90(가장 높음), 너비=10
    head = 90 * np.exp(-((x - 64) ** 2) / (2 * 10 ** 2))

    # 3. 오른쪽 어깨 (Right Shoulder): 위치=103, 높이=50, 너비=8
    right_shoulder = 50 * np.exp(-((x - 103) ** 2) / (2 * 8 ** 2))

    # 세 봉우리를 하나로 합치고, 약간의 노이즈(현실성)를 추가
    y = left_shoulder + head + right_shoulder
    noise = np.random.normal(0, 1.5, 128) # 약간의 주가 흔들림 추가 (원치 않으면 제거 가능)
    
    return (y + noise).tolist()

def evaluate_precision_at_k(sketch_data, pattern_name, true_tickers, k=5):
    """Top-K 검색 결과에 대한 정밀도(Precision) 계산"""
    print(f"\n{'='*60}")
    print(f"📊 정확도 평가: {pattern_name} (Top-{k} 정밀도)")
    print(f"✅ 정답 리스트(Ground Truth): {true_tickers}")
    print(f"{'='*60}")

    # 기존 test_similar.py 와 동일한 API 요청 형식
    payload = {
        "y": sketch_data,
        "target_len": 128
    }

    try:
        response = requests.post(f"{BASE_URL}/similar_db", json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        # 상위 K개 결과 추출 (예: 검색 결과 상위 5개)
        top_k_items = result['items'][:k]
        predicted_tickers = [item['ticker'] for item in top_k_items]
        
        print(f"\n🔍 시스템의 검색 결과 (상위 {k}개):")
        for i, item in enumerate(top_k_items):
            print(f"   {i+1}위. {item['ticker']} (유사도 {item['score']:.4f})")
            
        print("\n⏳ 채점 중...")
        
        # 채점: 검색된 종목 중 실제 정답(true_tickers) 리스트에 있는 종목 찾기
        correct_count = 0
        correct_tickers = []
        for ticker in predicted_tickers:
            if ticker in true_tickers:
                correct_count += 1
                correct_tickers.append(ticker)
                
        # 정밀도 계산 공식: (맞춘 개수 / 우리가 살펴본 개수 K) * 100
        precision = (correct_count / k) * 100
        
        print(f"\n🎯 최종 결과:")
        print(f" - 정답 적중 종목: {correct_tickers} (총 {correct_count}개)")
        print(f" - 틀린 종목 수: {k - correct_count}개")
        print(f"\n🌟 최종 정밀도 (Precision@{k}): {precision:.1f}%")
        
        if precision >= 80:
            print("   => 매우 우수한 성능입니다! 🎉")
        elif precision >= 50:
            print("   => 쓸만한 성능이지만 개선의 여지가 있습니다. 👍")
        else:
            print("   => 정확도를 좀 더 끌어올려야 합니다! 🛠️")
            
        return precision

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 0

def main():
    print("=" * 60)
    print("🚀 검색 알고리즘 성능(정확도) 평가 테스트")
    print("=" * 60)
    
    # 서버 작동 여부 확인
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if not response.json().get('ok'):
            print("⚠️ 서버 상태 이상")
            return
    except:
        print("❌ 서버가 실행되지 않았습니다! ./start_server.sh 를 먼저 실행해주세요.")
        return

    # 1. 테스트용 스케치 가져오기
    hs_sketch = generate_head_and_shoulders()
    
    # 2. 미리 준비해둔 정답지 가져오기
    true_hs_tickers = GROUND_TRUTH["Head_And_Shoulders"]
    
    # 3. Top-5 와 Top-10 에 대해서 정확도(정밀도) 평가 진행
    evaluate_precision_at_k(hs_sketch, "헤드앤숄더 패턴", true_hs_tickers, k=5)
    # 만약 상위 10개 결과에 대한 확률을 보고 싶다면 아래 주석을 해제하세요.
    # evaluate_precision_at_k(hs_sketch, "헤드앤숄더 패턴", true_hs_tickers, k=10)
    
    print("\n" + "=" * 60)
    print("✅ 테스트 종료")
    print("=" * 60)

if __name__ == "__main__":
    main()
