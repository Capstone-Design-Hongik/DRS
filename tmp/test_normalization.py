import sys
import numpy as np

# 프로젝트 루트 경로 추가 (app 폴더를 찾기 위함)
sys.path.append('/Users/myeongjin/Documents/GitHub/DRS') 
from app.features import normalize_pipeline

def test_correctness():
    inputs = {
        "짧고 높게 그린 스케치": np.random.rand(50) * 100 + 200,   
        "길고 낮게 그린 스케치": np.sin(np.linspace(0, 10, 300)) * 50 - 100, 
        "아예 변화없는 일직선": np.array([50.0] * 80) 
    }
    
    print("="*60)
    print("✅ 정규화(Normalization) 파이프라인 검증 테스트")
    print("="*60)
    
    for name, data in inputs.items():
        print(f"\n[테스트 대상: {name}]")
        print(f"  > 원본 상태: 점 {len(data)}개 | 높이 평균 {np.mean(data):.2f} | 표준편차(등락폭) {np.std(data):.2f}")
        
        # 실제 시스템과 동일한 정규화 함수 통과!
        normalized = normalize_pipeline(data, target_len=128)
        
        print(f"  👉 정규화 통과 후:")
        print(f"      - 길이: {len(normalized)} (목표: 128)")
        print(f"      - 높이 평균: {np.mean(normalized):.5f} (목표: 0.0)")
        print(f"      - 등락폭(표준편차): {np.std(normalized):.5f} (목표: 1.0 또는 0.0)")

if __name__ == "__main__":
    test_correctness()
