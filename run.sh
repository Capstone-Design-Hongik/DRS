#!/bin/bash

# DRS 서버 실행 스크립트

echo "========================================="
echo "  DRS (Drawing Stocks) Server Launcher  "
echo "========================================="
echo ""

# 가상 환경 확인
if [ ! -d ".venv" ]; then
    echo "❌ 가상 환경이 없습니다."
    echo "📦 가상 환경을 생성합니다..."
    python3 -m venv .venv

    if [ $? -ne 0 ]; then
        echo "❌ 가상 환경 생성 실패. python3-venv를 설치하세요:"
        echo "   sudo apt install python3-venv"
        exit 1
    fi
fi

# 가상 환경 활성화
echo "🔧 가상 환경 활성화..."
source .venv/bin/activate

# 의존성 설치 확인
if [ ! -f ".venv/installed" ]; then
    echo "📦 의존성을 설치합니다..."
    pip install -r requirements.txt

    if [ $? -eq 0 ]; then
        touch .venv/installed
        echo "✅ 의존성 설치 완료"
    else
        echo "❌ 의존성 설치 실패"
        exit 1
    fi
else
    echo "✅ 의존성이 이미 설치되어 있습니다."
fi

echo ""
echo "🚀 서버를 시작합니다..."
echo "   API: http://localhost:8080"
echo "   Web: http://localhost:8080/web/index.html"
echo "   Docs: http://localhost:8080/docs"
echo ""
echo "중지하려면 Ctrl+C를 누르세요."
echo ""

# 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
