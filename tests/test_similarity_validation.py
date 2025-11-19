"""
DRS 유사도 검증 테스트

교수님 추천: 테스트 데이터셋으로 객관적 검증

테스트 전략:
1. Ground Truth 데이터셋 생성
2. 정량적 평가 지표 계산
3. 자동화된 검증
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from typing import List, Tuple, Dict
import json
from datetime import datetime

from app.features import normalize_pipeline
from app.similar import rank_top_k, ensemble_score
from app.data_io import load_ma20_parquet


class SimilarityValidator:
    """유사도 검증 클래스"""

    def __init__(self):
        self.test_cases = []
        self.results = []

    def create_test_pattern(self, pattern_type: str, length: int = 200) -> np.ndarray:
        """
        테스트 패턴 생성

        Args:
            pattern_type: 패턴 유형
                - "uptrend": 상승 추세
                - "downtrend": 하락 추세
                - "peak": 산 모양 (올라갔다 내려옴)
                - "valley": 골짜기 (내려갔다 올라옴)
                - "sine": 사인파 (주기적 변동)
                - "flat": 평평함 (변동 없음)
            length: 패턴 길이

        Returns:
            정규화된 패턴 (length 길이)
        """
        x = np.linspace(0, 1, length)

        if pattern_type == "uptrend":
            y = x  # 0 → 1 선형 증가

        elif pattern_type == "downtrend":
            y = 1 - x  # 1 → 0 선형 감소

        elif pattern_type == "peak":
            # 0 → 1 → 0 (산 모양)
            y = np.where(x < 0.5, 2 * x, 2 * (1 - x))

        elif pattern_type == "valley":
            # 1 → 0 → 1 (골짜기)
            y = np.where(x < 0.5, 1 - 2 * x, 2 * x - 1)

        elif pattern_type == "sine":
            # 사인파 (2주기)
            y = 0.5 + 0.5 * np.sin(4 * np.pi * x)

        elif pattern_type == "flat":
            # 평평함
            y = np.ones(length) * 0.5

        else:
            raise ValueError(f"Unknown pattern type: {pattern_type}")

        # Z-score 정규화
        return normalize_pipeline(y, length)

    def add_noise(self, pattern: np.ndarray, noise_level: float = 0.1) -> np.ndarray:
        """패턴에 노이즈 추가"""
        noise = np.random.normal(0, noise_level, len(pattern))
        return pattern + noise

    def generate_test_dataset(self) -> List[Dict]:
        """
        테스트 데이터셋 생성

        각 패턴에 대해:
        1. 원본 패턴
        2. 노이즈 추가 패턴 (낮음)
        3. 노이즈 추가 패턴 (높음)
        4. 반대 패턴
        """
        patterns = ["uptrend", "downtrend", "peak", "valley", "sine"]
        dataset = []

        for pattern_type in patterns:
            # 원본 패턴
            original = self.create_test_pattern(pattern_type)

            # 테스트 케이스 1: 자기 자신 (100% 유사)
            dataset.append({
                "query_name": f"{pattern_type}_original",
                "query_pattern": original.tolist(),
                "expected_similar": [f"{pattern_type}_original"],
                "expected_score_range": (0.9, 1.0),
                "description": "동일 패턴 검색 (자기 자신)"
            })

            # 테스트 케이스 2: 낮은 노이즈 (80%+ 유사)
            noisy_low = self.add_noise(original, noise_level=0.1)
            dataset.append({
                "query_name": f"{pattern_type}_noisy_low",
                "query_pattern": noisy_low.tolist(),
                "expected_similar": [f"{pattern_type}_original", f"{pattern_type}_noisy_low"],
                "expected_score_range": (0.7, 0.9),
                "description": "낮은 노이즈 추가 (매우 유사)"
            })

            # 테스트 케이스 3: 높은 노이즈 (50%+ 유사)
            noisy_high = self.add_noise(original, noise_level=0.3)
            dataset.append({
                "query_name": f"{pattern_type}_noisy_high",
                "query_pattern": noisy_high.tolist(),
                "expected_similar": [f"{pattern_type}_original"],
                "expected_score_range": (0.4, 0.7),
                "description": "높은 노이즈 추가 (유사)"
            })

        # 테스트 케이스 4: 반대 패턴 (낮은 유사도)
        uptrend = self.create_test_pattern("uptrend")
        downtrend = self.create_test_pattern("downtrend")
        dataset.append({
            "query_name": "uptrend_vs_downtrend",
            "query_pattern": uptrend.tolist(),
            "expected_dissimilar": ["downtrend_original"],
            "expected_score_range": (0.0, 0.4),
            "description": "반대 패턴 검색 (비유사)"
        })

        return dataset

    def evaluate_precision_at_k(self, retrieved: List[str], relevant: List[str], k: int = 5) -> float:
        """
        Precision@K 계산

        상위 K개 결과 중 정답이 몇 개인가?

        Args:
            retrieved: 검색 결과 (순서대로)
            relevant: 정답 리스트
            k: 상위 K개

        Returns:
            Precision@K (0~1)
        """
        if k == 0 or len(retrieved) == 0:
            return 0.0

        top_k = retrieved[:k]
        num_relevant = sum(1 for item in top_k if item in relevant)
        return num_relevant / k

    def evaluate_recall_at_k(self, retrieved: List[str], relevant: List[str], k: int = 5) -> float:
        """
        Recall@K 계산

        전체 정답 중 상위 K개에 몇 개가 포함되었는가?

        Args:
            retrieved: 검색 결과
            relevant: 정답 리스트
            k: 상위 K개

        Returns:
            Recall@K (0~1)
        """
        if len(relevant) == 0:
            return 0.0

        top_k = retrieved[:k]
        num_relevant = sum(1 for item in top_k if item in relevant)
        return num_relevant / len(relevant)

    def evaluate_ndcg_at_k(self, retrieved: List[str], relevant: List[str], k: int = 5) -> float:
        """
        NDCG@K (Normalized Discounted Cumulative Gain) 계산

        순위를 고려한 평가 지표 (상위에 정답이 많을수록 높은 점수)

        Args:
            retrieved: 검색 결과
            relevant: 정답 리스트
            k: 상위 K개

        Returns:
            NDCG@K (0~1)
        """
        def dcg(relevances):
            """DCG 계산"""
            return sum(rel / np.log2(i + 2) for i, rel in enumerate(relevances))

        # 실제 검색 결과의 relevance
        actual_relevances = [1 if item in relevant else 0 for item in retrieved[:k]]

        # 이상적인 순위 (모든 정답이 상위에)
        ideal_relevances = sorted([1] * min(len(relevant), k) + [0] * (k - len(relevant)), reverse=True)

        actual_dcg = dcg(actual_relevances)
        ideal_dcg = dcg(ideal_relevances)

        if ideal_dcg == 0:
            return 0.0

        return actual_dcg / ideal_dcg

    def run_validation_on_real_data(self, test_cases: List[Dict]) -> Dict:
        """
        실제 주가 데이터로 검증

        Args:
            test_cases: 테스트 케이스 리스트

        Returns:
            검증 결과
        """
        # MA20 데이터 로드
        df = load_ma20_parquet()
        if df is None or df.empty:
            raise ValueError("MA20 데이터가 없습니다. 먼저 /ingest를 실행하세요.")

        from app.features import dict_to_matrix

        ma20 = {c: df[c].dropna() for c in df.columns}
        matrix, tickers = dict_to_matrix(ma20, target_len=200)

        results = []

        for test_case in test_cases:
            query_pattern = np.array(test_case["query_pattern"])

            # Top 5 검색
            top_results = rank_top_k(query_pattern, matrix, tickers, k=5)
            retrieved_tickers = [t for t, _ in top_results]
            retrieved_scores = [s for _, s in top_results]

            # 평가 (실제 데이터에서는 expected_similar를 사용할 수 없으므로 점수만 확인)
            result = {
                "test_case": test_case["query_name"],
                "description": test_case["description"],
                "top_5_results": [
                    {"ticker": t, "score": float(s)}
                    for t, s in top_results
                ],
                "avg_score": float(np.mean(retrieved_scores)),
                "max_score": float(np.max(retrieved_scores)),
                "min_score": float(np.min(retrieved_scores)),
                "expected_range": test_case.get("expected_score_range", (0.0, 1.0)),
                "in_range": test_case.get("expected_score_range", (0.0, 1.0))[0] <= np.max(retrieved_scores) <= test_case.get("expected_score_range", (0.0, 1.0))[1]
            }

            results.append(result)

        # 전체 요약
        summary = {
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results if r["in_range"]),
            "avg_max_score": np.mean([r["max_score"] for r in results]),
            "avg_avg_score": np.mean([r["avg_score"] for r in results]),
        }

        return {
            "summary": summary,
            "details": results,
            "timestamp": datetime.now().isoformat()
        }

    def save_results(self, results: Dict, filename: str = "validation_results.json"):
        """결과를 JSON 파일로 저장"""
        output_dir = os.path.join(os.path.dirname(__file__), "results")
        os.makedirs(output_dir, exist_ok=True)

        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"✅ 결과 저장됨: {filepath}")
        return filepath


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("  DRS 유사도 검증 테스트")
    print("=" * 60)
    print()

    validator = SimilarityValidator()

    # 1. 테스트 데이터셋 생성
    print("📦 1단계: 테스트 데이터셋 생성...")
    test_dataset = validator.generate_test_dataset()
    print(f"   생성된 테스트 케이스: {len(test_dataset)}개")
    print()

    # 2. 실제 데이터로 검증
    print("🔍 2단계: 실제 주가 데이터로 검증...")
    try:
        results = validator.run_validation_on_real_data(test_dataset)

        # 3. 결과 출력
        print()
        print("=" * 60)
        print("📊 검증 결과")
        print("=" * 60)
        print(f"총 테스트: {results['summary']['total_tests']}개")
        print(f"통과: {results['summary']['passed_tests']}개")
        print(f"평균 최고 점수: {results['summary']['avg_max_score']:.4f}")
        print(f"평균 평균 점수: {results['summary']['avg_avg_score']:.4f}")
        print()

        # 상세 결과
        print("📋 상세 결과:")
        print()
        for i, detail in enumerate(results['details'], 1):
            status = "✅ PASS" if detail['in_range'] else "❌ FAIL"
            print(f"{i}. {detail['test_case']} {status}")
            print(f"   설명: {detail['description']}")
            print(f"   예상 범위: {detail['expected_range']}")
            print(f"   실제 최고 점수: {detail['max_score']:.4f}")
            print(f"   Top 3 결과:")
            for j, res in enumerate(detail['top_5_results'][:3], 1):
                print(f"      {j}. {res['ticker']}: {res['score']:.4f}")
            print()

        # 4. 결과 저장
        print("💾 3단계: 결과 저장...")
        filepath = validator.save_results(results)
        print()

        print("=" * 60)
        print("✅ 검증 완료!")
        print("=" * 60)

    except ValueError as e:
        print(f"❌ 오류: {e}")
        print()
        print("해결 방법:")
        print("1. 서버를 실행하세요")
        print("2. /ingest 엔드포인트를 호출하여 데이터를 준비하세요")
        print("   curl -X POST 'http://localhost:8080/ingest?max_tickers=200' -H 'Content-Type: application/json' -d '{\"days\": 365}'")


if __name__ == "__main__":
    main()
