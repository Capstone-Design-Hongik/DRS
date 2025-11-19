#!/bin/bash

echo "========================================="
echo "  DRS 유사도 검증 테스트 실행"
echo "========================================="
echo ""

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

# 가상환경 활성화 (있으면)
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 테스트 실행
python3 tests/test_similarity_validation.py

echo ""
echo "결과 파일: tests/results/validation_results.json"
