# DRS 로컬 실행 가이드

## 개선 사항 요약 ✅

### 보안 강화
- ✅ CORS 설정 제한 (특정 도메인만 허용)
- ✅ 레이트 리밋 추가 (ingest: 5/분, similar: 20/분)
- ✅ 전역 예외 처리 강화
- ✅ 동시성 제어 (Lock 추가)

### 코드 품질 개선
- ✅ 타입 힌트 완성 (모든 함수)
- ✅ 로깅 시스템 추가
- ✅ 매직 넘버 제거 (상수화)
- ✅ Docstring 추가 (모든 함수)

### 설정 관리
- ✅ pydantic-settings로 환경 변수 관리
- ✅ .env 파일로 설정 분리
- ✅ 동적 API URL (프론트엔드)

---

## 사전 요구사항

- Python 3.9 이상
- pip (Python 패키지 관리자)

---

## 설치 및 실행

### 1. 가상 환경 생성 (권장)

```bash
# 가상 환경 생성
python3 -m venv .venv

# 가상 환경 활성화
# Linux/Mac:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

**설치되는 주요 패키지:**
- `fastapi` - 웹 프레임워크
- `uvicorn[standard]` - ASGI 서버
- `yfinance` - 주가 데이터 API
- `pandas`, `numpy` - 데이터 처리
- `fastdtw`, `scipy` - 유사도 알고리즘
- `slowapi` - 레이트 리밋
- `pydantic-settings` - 설정 관리

### 3. 환경 변수 설정 (선택)

`.env` 파일이 이미 생성되어 있습니다. 필요 시 수정:

```bash
# .env
API_HOST=0.0.0.0
API_PORT=8080
CORS_ORIGINS=["http://localhost:8080", "http://127.0.0.1:8080"]
TARGET_LEN=200
LOG_LEVEL=INFO
```

### 4. 서버 실행

```bash
# 방법 1: uvicorn으로 직접 실행
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# 방법 2: Python 모듈로 실행
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

**실행 옵션:**
- `--reload`: 코드 변경 시 자동 재시작 (개발용)
- `--host 0.0.0.0`: 모든 인터페이스에서 접근 가능
- `--port 8080`: 포트 번호

### 5. 웹 브라우저에서 접속

```
http://localhost:8080/web/index.html
```

또는 FastAPI 자동 문서:
```
http://localhost:8080/docs
```

---

## 사용 방법

### Step 1: 데이터 준비 (Ingest)

1. 웹 페이지에서 **"데이터 준비"** 버튼 클릭
2. 티커 개수 선택 (50/200/1000/5000)
3. 약 1-10분 소요 (티커 개수에 따라)
4. 완료 메시지 확인

**API 호출 예시:**
```bash
curl -X POST "http://localhost:8080/ingest?max_tickers=50" \
  -H "Content-Type: application/json" \
  -d '{"days": 365}'
```

### Step 2: 스케치 & 검색

1. 캔버스에 마우스/터치로 주가 패턴 그리기
2. **"유사도 검색"** 버튼 클릭
3. Top 5 유사 종목 확인
4. 오버레이 차트에서 비교

**API 호출 예시:**
```bash
curl -X POST "http://localhost:8080/similar" \
  -H "Content-Type: application/json" \
  -d '{
    "y": [0.1, 0.15, 0.2, ...],
    "target_len": 200
  }'
```

---

## 프로젝트 구조

```
DRS/
├── app/                    # Backend
│   ├── main.py            # FastAPI 앱 (CORS, 레이트 리밋, 로깅)
│   ├── config.py          # 설정 관리 (NEW)
│   ├── models.py          # Pydantic 모델
│   ├── tickers.py         # 티커 관리 (예외 처리 강화)
│   ├── data_io.py         # 데이터 I/O (타입 힌트 추가)
│   ├── features.py        # 정규화 파이프라인 (상수화)
│   └── similar.py         # 유사도 알고리즘
├── web/                   # Frontend
│   ├── index.html         # UI
│   └── script.js          # Canvas 드로잉 (동적 API URL)
├── data/                  # 데이터 저장소 (자동 생성)
│   ├── tickers_nasdaq.json
│   ├── ma20.parquet
│   └── meta.json
├── .env                   # 환경 변수 (NEW)
├── requirements.txt       # Python 의존성 (업데이트)
├── .gitignore            # Git 제외 파일
├── Claude.md             # 프로젝트 분석 문서
└── SETUP.md              # 이 파일
```

---

## API 엔드포인트

### `GET /health`
헬스체크

**Response:**
```json
{"ok": true}
```

---

### `POST /ingest`
주가 데이터 다운로드 및 캐싱

**Rate Limit:** 5회/분

**Query Parameters:**
- `max_tickers` (int): 티커 개수 (10-5000, 기본 5000)
- `force_refresh` (bool): 티커 강제 재수집 (기본 false)

**Body:**
```json
{
  "days": 365
}
```

**Response:**
```json
{
  "tickers_count": 3800,
  "ok_count": 3750,
  "target_len": 200
}
```

---

### `POST /similar`
스케치와 유사한 종목 검색

**Rate Limit:** 20회/분

**Body:**
```json
{
  "y": [0.1, 0.15, 0.2, ...],  // 200개 포인트
  "target_len": 200
}
```

**Response:**
```json
{
  "items": [
    {
      "ticker": "AAPL",
      "score": 0.8234,
      "rank": 1,
      "series_norm": [...],
      "sketch_norm": [...]
    }
  ]
}
```

---

### `POST /refresh_tickers`
티커 리스트 강제 갱신

**Query Parameters:**
- `max_tickers` (int): 티커 개수

**Response:**
```json
{
  "refreshed": 3800
}
```

---

## 로그 확인

서버 실행 시 콘솔에서 실시간 로그 확인:

```
2025-11-16 10:30:15 - app.main - INFO - Starting warmup: loading cached data...
2025-11-16 10:30:16 - app.tickers - INFO - Loaded 3800 tickers from cache (age: 2.3h)
2025-11-16 10:30:20 - app.main - INFO - Warmup completed: 3750 tickers loaded into cache
2025-11-16 10:35:42 - app.main - INFO - Similar search started: sketch length=200
2025-11-16 10:35:43 - app.main - INFO - Top 5 matches found: ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
```

**로그 레벨 변경:** `.env` 파일에서 `LOG_LEVEL` 수정
- `DEBUG`: 상세 로그
- `INFO`: 일반 정보
- `WARNING`: 경고만
- `ERROR`: 에러만

---

## 문제 해결

### 1. CORS 에러 발생 시

**.env** 파일에서 CORS_ORIGINS에 프론트엔드 URL 추가:
```bash
CORS_ORIGINS=["http://localhost:8080", "http://127.0.0.1:8080", "http://your-domain.com"]
```

### 2. Rate Limit 초과 시

**.env** 파일에서 제한 완화:
```bash
RATE_LIMIT_INGEST=10/minute
RATE_LIMIT_SIMILAR=50/minute
```

### 3. 메모리 부족 시

티커 개수 줄이기:
```bash
# 50개만 사용
curl -X POST "http://localhost:8080/ingest?max_tickers=50" ...
```

### 4. yfinance 다운로드 실패 시

- 네트워크 연결 확인
- Yahoo Finance API 상태 확인
- VPN 사용 중이면 해제

---

## 성능 최적화 팁

### 1. 티커 개수별 권장 사항

| 티커 개수 | 데이터 로드 | 검색 속도 | 메모리 | 용도 |
|----------|------------|---------|--------|------|
| 50       | ~5초       | ~10ms   | ~1MB   | 테스트 |
| 200      | ~20초      | ~40ms   | ~3MB   | 개발 |
| 1000     | ~2분       | ~200ms  | ~16MB  | 일반 |
| 5000     | ~10분      | ~1초    | ~80MB  | 프로덕션 |

### 2. 캐시 활용

- 첫 실행 시: `/ingest` 호출 → 데이터 다운로드
- 이후 실행: 서버 재시작 시 자동 로드 (warmup)
- 캐시 유효기간: 24시간

### 3. 프로덕션 배포

```bash
# 워커 수 증가 (CPU 코어 수만큼)
uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 4

# 또는 Gunicorn 사용
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## 개발자 가이드

### 코드 수정 시 확인 사항

1. **타입 힌트 검사**
   ```bash
   mypy app/
   ```

2. **코드 포맷팅**
   ```bash
   black app/ --line-length 100
   ```

3. **Import 정리**
   ```bash
   isort app/
   ```

### 새로운 엔드포인트 추가

```python
@app.get("/new_endpoint")
@limiter.limit("10/minute")  # 레이트 리밋
def new_endpoint(request: Request):
    """엔드포인트 설명"""
    logger.info("New endpoint called")
    try:
        # 로직
        return {"result": "success"}
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(500, str(e))
```

---

## 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [yfinance GitHub](https://github.com/ranaroussi/yfinance)
- [Dynamic Time Warping](https://en.wikipedia.org/wiki/Dynamic_time_warping)
- [Claude.md](./Claude.md) - 상세 코드 리뷰

---

**작성일**: 2025-11-16
**버전**: 2.0 (개선판)
