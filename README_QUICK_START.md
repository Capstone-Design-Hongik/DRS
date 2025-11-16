# DRS - Drawing Stocks 🎨📈

> 캔버스에 주가 패턴을 그리면 유사한 NASDAQ 종목을 찾아주는 시계열 패턴 매칭 시스템

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ⚡ 빠른 시작 (Quick Start)

### 1️⃣ 의존성 설치

```bash
# 가상 환경 생성
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2️⃣ 서버 실행

```bash
# 방법 1: 실행 스크립트 사용 (권장)
./run.sh

# 방법 2: 직접 실행
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### 3️⃣ 웹 접속

```
http://localhost:8080/web/index.html
```

**또는 API 문서:**
```
http://localhost:8080/docs
```

---

## 🎯 사용 방법

### Step 1: 데이터 준비
1. 웹 페이지에서 **"데이터 준비"** 버튼 클릭
2. 티커 개수 선택 (50개 권장, 테스트용)
3. 약 5-30초 대기

### Step 2: 스케치 & 검색
1. 캔버스에 마우스로 주가 패턴 그리기
2. **"유사도 검색"** 버튼 클릭
3. Top 5 유사 종목 확인!

---

## ✨ v2.0 개선 사항

### 🔒 보안 강화
- ✅ CORS 제한 (특정 도메인만 허용)
- ✅ 레이트 리밋 (API 남용 방지)
- ✅ 전역 예외 처리
- ✅ 동시성 제어 (Thread Lock)

### 📝 코드 품질
- ✅ 타입 힌트 100% 적용
- ✅ 로깅 시스템 추가
- ✅ 매직 넘버 제거 (상수화)
- ✅ Docstring 완비

### ⚙️ 설정 관리
- ✅ 환경 변수 지원 (.env)
- ✅ pydantic-settings 활용
- ✅ 동적 API URL

---

## 📁 주요 파일

```
DRS/
├── app/
│   ├── main.py         # FastAPI 앱 (개선됨)
│   ├── config.py       # 설정 관리 (NEW)
│   ├── tickers.py      # 예외 처리 강화
│   ├── data_io.py      # 타입 힌트 추가
│   └── features.py     # 상수화
├── web/
│   ├── index.html      # UI
│   └── script.js       # 동적 API URL (개선됨)
├── .env               # 환경 변수 (NEW)
├── run.sh             # 실행 스크립트 (NEW)
├── SETUP.md           # 상세 가이드 (NEW)
└── Claude.md          # 코드 리뷰 문서 (NEW)
```

---

## 🛠️ 기술 스택

**Backend:**
- FastAPI (웹 프레임워크)
- Uvicorn (ASGI 서버)
- yfinance (주가 데이터)
- pandas/numpy (데이터 처리)
- fastdtw (DTW 알고리즘)
- slowapi (레이트 리밋)

**Frontend:**
- Vanilla JavaScript
- HTML5 Canvas
- CSS (Dark Theme)

**알고리즘:**
- DTW (Dynamic Time Warping) 70%
- Pearson Correlation 20%
- Cosine Similarity 10%

---

## 📊 성능

| 티커 개수 | 데이터 로드 | 검색 속도 | 메모리 |
|----------|------------|---------|--------|
| 50       | ~5초       | ~10ms   | ~1MB   |
| 200      | ~20초      | ~40ms   | ~3MB   |
| 1000     | ~2분       | ~200ms  | ~16MB  |
| 5000     | ~10분      | ~1초    | ~80MB  |

---

## 🔧 설정 (.env)

```bash
# API 설정
API_HOST=0.0.0.0
API_PORT=8080

# CORS 설정
CORS_ORIGINS=["http://localhost:8080", "http://127.0.0.1:8080"]

# 데이터 설정
TARGET_LEN=200          # 시계열 정규화 길이
CACHE_TTL_SEC=86400     # 캐시 유효기간 (24시간)

# 레이트 리밋
RATE_LIMIT_INGEST=5/minute
RATE_LIMIT_SIMILAR=20/minute

# 로그 레벨
LOG_LEVEL=INFO
```

---

## 📖 문서

- **[SETUP.md](./SETUP.md)** - 상세 설치 및 사용 가이드
- **[Claude.md](./Claude.md)** - 코드 리뷰 및 분석 문서
- **[API Docs](http://localhost:8080/docs)** - 자동 생성 API 문서

---

## 🐛 문제 해결

### CORS 에러
`.env`에서 `CORS_ORIGINS`에 도메인 추가

### Rate Limit 초과
`.env`에서 제한 완화:
```bash
RATE_LIMIT_SIMILAR=50/minute
```

### 메모리 부족
티커 개수 줄이기:
```bash
# 50개만 사용
max_tickers=50
```

---

## 📝 API 예시

### 데이터 준비
```bash
curl -X POST "http://localhost:8080/ingest?max_tickers=50" \
  -H "Content-Type: application/json" \
  -d '{"days": 365}'
```

### 유사도 검색
```bash
curl -X POST "http://localhost:8080/similar" \
  -H "Content-Type: application/json" \
  -d '{
    "y": [0.1, 0.15, 0.2, 0.25, ...],
    "target_len": 200
  }'
```

---

## 👥 기여자

- **Original Team**: Capstone Design @ Hongik University
- **Code Review & Improvements**: Claude (Anthropic)

---

## 📜 라이선스

MIT License

---

## 🔗 관련 링크

- [GitHub Repository](https://github.com/Capstone-Design-Hongik/DRS)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [yfinance Documentation](https://github.com/ranaroussi/yfinance)

---

**버전**: 2.0 (개선판)
**마지막 업데이트**: 2025-11-16
