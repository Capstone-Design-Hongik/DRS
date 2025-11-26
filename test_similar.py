#!/usr/bin/env python3
"""PostgreSQL 기반 유사도 검색 테스트 스크립트"""
import requests
import json
import numpy as np

# API 엔드포인트
BASE_URL = "http://localhost:8080"

# 테스트용 스케치 데이터 생성
# 상승 추세 패턴
def generate_uptrend():
    """상승 추세 패턴 생성"""
    x = np.linspace(0, 10, 100)
    y = x + np.random.normal(0, 0.5, 100)
    return y.tolist()

# 하락 추세 패턴
def generate_downtrend():
    """하락 추세 패턴 생성"""
    x = np.linspace(0, 10, 100)
    y = -x + np.random.normal(0, 0.5, 100)
    return y.tolist()

# V자 반등 패턴
def generate_v_shape():
    """V자 반등 패턴 생성"""
    x = np.linspace(0, 10, 100)
    y = np.abs(x - 5) * -1 + np.random.normal(0, 0.3, 100)
    return y.tolist()

# 사인파 패턴
def generate_sine():
    """사인파 패턴 생성"""
    x = np.linspace(0, 4 * np.pi, 100)
    y = np.sin(x) + np.random.normal(0, 0.1, 100)
    return y.tolist()

def test_similar_db(sketch_data, pattern_name):
    """DB 기반 유사도 검색 테스트"""
    print(f"\n{'='*60}")
    print(f"🔍 테스트: {pattern_name}")
    print(f"{'='*60}")

    # API 요청
    payload = {
        "y": sketch_data,
        "target_len": 128
    }

    try:
        response = requests.post(f"{BASE_URL}/similar_db", json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()

        print(f"✅ 요청 성공! Top 5 유사 종목:\n")

        for item in result['items']:
            print(f"  🏆 Rank #{item['rank']}: {item['ticker']}")
            print(f"     유사도 점수: {item['score']:.4f}")
            print()

    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다.")
        print("   먼저 서버를 실행하세요: ./start_server.sh")
    except requests.exceptions.Timeout:
        print("❌ 요청 시간 초과")
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP 오류: {e}")
        print(f"   응답: {response.text}")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def main():
    """메인 테스트 실행"""
    print("=" * 60)
    print("PostgreSQL 기반 유사도 검색 테스트")
    print("=" * 60)

    # 서버 헬스 체크
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.json().get('ok'):
            print("✅ 서버 정상 작동 중\n")
        else:
            print("⚠️  서버 상태 이상\n")
            return
    except:
        print("❌ 서버가 실행되지 않았습니다!")
        print("   다음 명령으로 서버를 실행하세요:")
        print("   ./start_server.sh\n")
        return

    # 다양한 패턴 테스트
    patterns = [
        (generate_uptrend(), "📈 상승 추세"),
        (generate_downtrend(), "📉 하락 추세"),
        (generate_v_shape(), "✌️  V자 반등"),
        (generate_sine(), "🌊 사인파 패턴")
    ]

    for sketch, name in patterns:
        test_similar_db(sketch, name)

    print("\n" + "=" * 60)
    print("✅ 모든 테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    main()
