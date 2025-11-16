# DRS (Drawing Stocks) - 프로젝트 분석 및 리뷰

> **분석 날짜**: 2025-11-16
> **분석자**: Claude (Anthropic)
> **프로젝트**: https://github.com/Capstone-Design-Hongik/DRS

---

## 📖 프로젝트 개요

**DRS (Drawing Stocks)**는 사용자가 캔버스에 주가 패턴을 스케치하면, NASDAQ 상장 주식 중 해당 패턴과 가장 유사한 종목을 찾아주는 시계열 패턴 매칭 시스템입니다.

### 핵심 기능
- 🎨 **캔버스 기반 스케치**: HTML5 Canvas로 주가 패턴 그리기
- 📊 **MA20 기반 매칭**: 20일 이동평균선으로 패턴 비교
- 🔍 **앙상블 유사도**: DTW + Pearson + Cosine 조합
- 💾 **멀티레벨 캐싱**: 티커 리스트, Parquet, 인메모리 캐시

---

## 🏗️ 기술 스택

### Backend
- **Framework**: FastAPI (Python)
- **Server**: Uvicorn (ASGI)
- **Data Processing**: pandas, numpy, scipy, pyarrow
- **Financial Data**: yfinance (Yahoo Finance API)
- **Database**: DuckDB (embedded analytical DB)
- **Similarity**: fastdtw, scipy

### Frontend
- **UI**: Vanilla JavaScript + HTML5
- **Drawing**: Canvas API
- **Styling**: Custom CSS (Dark Theme)

---

## 📁 프로젝트 구조

```
/home/claude/DRS/
├── app/                    # Backend (FastAPI)
│   ├── main.py            # API 엔드포인트 (ingest, similar, health)
│   ├── models.py          # Pydantic 데이터 모델
│   ├── data_io.py         # 데이터 다운로드/저장/로드
│   ├── features.py        # 리샘플링/정규화/파이프라인
│   ├── similar.py         # DTW/Pearson/Cosine 앙상블
│   └── tickers.py         # NASDAQ 티커 관리 (캐싱)
├── web/                   # Frontend
│   ├── index.html         # UI 인터페이스
│   └── script.js          # Canvas 드로잉/API 통신
├── data/                  # 데이터 저장소 (gitignored)
│   ├── tickers_nasdaq.json # 캐시된 티커 리스트
│   ├── ma20.parquet       # MA20 시계열 데이터
│   └── meta.json          # 메타데이터
├── .vscode/
│   └── launch.json        # Chrome 디버거 설정
├── requirements.txt       # Python 의존성
└── README.md             # 프로젝트 문서
```

---

## 🔄 애플리케이션 플로우

### 1. 데이터 준비 (Ingest)
```
1. NASDAQ API → 티커 리스트 조회 (3,800+ 종목)
   ↓
2. yfinance → 2년치 OHLC 데이터 다운로드
   ↓
3. 최근 365일 슬라이싱 → MA20 계산
   ↓
4. Parquet 저장 + 인메모리 정규화 매트릭스 생성
```

### 2. 유사도 검색 (Similar)
```
1. 사용자 스케치 (Canvas) → 200 포인트로 리샘플링
   ↓
2. Z-score 정규화 (평균=0, 표준편차=1)
   ↓
3. 앙상블 스코어 계산 (DTW 70% + Pearson 20% + Cosine 10%)
   ↓
4. Top 5 종목 반환 + 오버레이 시각화
```

---

## ⚙️ API 명세

### `POST /ingest`
**설명**: 주가 데이터 다운로드 및 캐싱
**Parameters**:
- `max_tickers` (query): 티커 개수 (50~5000, 기본 5000)
- `force_refresh` (query): 티커 강제 재수집 (기본 false)
- `days` (body): 데이터 기간 (기본 365일)

**Response**:
```json
{
  "tickers_count": 3800,
  "ok_count": 3750,
  "target_len": 200
}
```

### `POST /similar`
**설명**: 스케치와 유사한 종목 검색
**Request**:
```json
{
  "y": [0.1, 0.15, 0.2, ...],  // 200개 포인트
  "target_len": 200
}
```

**Response**:
```json
{
  "items": [
    {
      "ticker": "AAPL",
      "score": 0.8234,
      "rank": 1,
      "series_norm": [...],  // 정규화된 MA20
      "sketch_norm": [...]   // 정규화된 스케치
    }
  ]
}
```

### `GET /health`
**설명**: 헬스체크
**Response**: `{"ok": true}`

### `POST /refresh_tickers`
**설명**: 티커 리스트 강제 갱신 (가격 데이터는 제외)
**Response**: `{"refreshed": 3800}`

---

## 🎯 핵심 알고리즘

### 1. 시계열 정규화 (`app/features.py`)
```python
def normalize_pipeline(y: np.ndarray, target_len: int) -> np.ndarray:
    # 1. 리샘플링: 임의 길이 → 200 포인트
    y = resample_series(y, target_len)
    # 2. Z-score 정규화: 평균=0, 표준편차=1
    y = zscore(y)
    return y
```

### 2. 앙상블 유사도 (`app/similar.py`)
```python
def ensemble_score(sketch, series, alpha=0.7, beta=0.2, gamma=0.1):
    # DTW: 시간 왜곡 허용 (70% 가중치)
    d = dtw_distance(sketch, series)
    d_norm = -d / len(sketch)

    # Pearson: 선형 상관관계 (20% 가중치)
    c = pearson(sketch, series)

    # Cosine: 각도 유사도 (10% 가중치)
    s = cosine_sim(sketch, series)

    return alpha * d_norm + beta * c + gamma * s
```

### 3. 티커 필터링 (`app/tickers.py`)
```python
# 제외 대상: 워런트, SPAC, 우선주
bad_fragments = ("-WT", "-WS", "-W", "-R", "-U")

# 정규 표현식: 대문자 + 숫자/점/하이픈
_symbol_ok = re.compile(r"^[A-Z][A-Z0-9\.\-]*$")
```

---

## 📊 성능 최적화

### 캐싱 전략
1. **티커 리스트**: 24시간 TTL (JSON 파일)
2. **MA20 데이터**: Parquet 포맷 (컬럼 저장 효율)
3. **정규화 매트릭스**: 인메모리 (NumPy array)
4. **Warmup**: 서버 시작 시 캐시 사전 로드

### 데이터 크기 예측
- 5000 티커 × 200 포인트 × 8 bytes (float64) = **7.6 MB**
- norm_map (list 변환) = 추가 **7.6 MB**
- **총 메모리**: ~15 MB (매우 효율적)

---

## ⚠️ 코드 리뷰 결과

### 🔴 Critical Issues

#### 1. CORS 설정 취약 (`app/main.py:17`)
**문제**:
```python
app.add_middleware(CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용
    allow_methods=["*"],
    allow_headers=["*"]
)
```

**해결**:
```python
app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:8080", "https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"]
)
```

#### 2. 예외 처리 누락 (`app/tickers.py:33`)
**문제**:
```python
def fetch_tickers_from_nasdaq() -> List[str]:
    r = requests.get(NASDAQ_API, headers=HEADERS, timeout=30)
    r.raise_for_status()  # 예외 발생 시 서버 크래시
```

**해결**:
```python
def fetch_tickers_from_nasdaq() -> List[str]:
    try:
        r = requests.get(NASDAQ_API, headers=HEADERS, timeout=30)
        r.raise_for_status()
        rows = r.json()["data"]["table"]["rows"]
        # ...
    except requests.RequestException as e:
        logger.error(f"Failed to fetch tickers: {e}")
        raise HTTPException(503, "NASDAQ API 호출 실패")
```

#### 3. 레이트 리밋 없음
**문제**: `/ingest` 엔드포인트가 무제한 호출 가능 (DoS 취약)

**해결**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/ingest")
@limiter.limit("5/minute")  # 분당 5회 제한
def ingest(...):
    ...
```

### 🟡 Medium Issues

#### 4. 동시성 문제 (`app/main.py:19`)
**문제**: 전역 `CACHE` dict는 thread-safe하지 않음

**해결**:
```python
import threading

CACHE_LOCK = threading.Lock()

@app.post("/ingest")
def ingest(...):
    with CACHE_LOCK:
        CACHE.update({"matrix": matrix, ...})
```

#### 5. 하드코딩된 설정 (`web/script.js:1`)
**문제**:
```javascript
const API = "http://localhost:8080";
```

**해결**:
```javascript
const API = window.location.origin;  // 동적 URL
// 또는 환경 변수 사용
const API = process.env.VUE_APP_API_URL || "http://localhost:8080";
```

#### 6. 타입 힌트 불완전 (`app/data_io.py:19`)
**문제**:
```python
def compute_ma20(ohlc_multi):  # 타입 없음
```

**해결**:
```python
def compute_ma20(ohlc_multi: pd.DataFrame) -> dict[str, pd.Series]:
    """
    OHLC 데이터에서 MA20 계산

    Args:
        ohlc_multi: MultiIndex 컬럼 DataFrame (ticker, field)

    Returns:
        {ticker: MA20 Series} 딕셔너리
    """
```

### 🟢 Low Priority

#### 7. 매직 넘버 제거
**Before**:
```python
if len(y) < 30:  # 30이 뭔지 불명확
    continue
```

**After**:
```python
MIN_DATA_POINTS = 30  # MA20 계산 후 최소 포인트
if len(y) < MIN_DATA_POINTS:
    continue
```

#### 8. 로깅 추가
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/ingest")
def ingest(...):
    logger.info(f"Ingesting {max_tickers} tickers, force={force_refresh}")
    # ...
    logger.info(f"Ingest completed: {len(T)} tickers cached")
```

#### 9. 비동기 처리
```python
@app.post("/ingest")
async def ingest(...):
    # yfinance는 동기 함수이므로 thread pool 사용
    raw = await asyncio.to_thread(download_ohlc, tickers, period="2y")
```

---

## 🚀 개선 제안

### 즉시 수정 (High Priority)
1. ✅ **CORS 설정 제한**: 특정 도메인만 허용
2. ✅ **예외 처리 추가**: try-except 블록으로 안정성 확보
3. ✅ **레이트 리밋**: slowapi로 API 호출 제한
4. ✅ **환경 변수**: dotenv로 설정 관리

### 단기 개선 (Medium Priority)
5. ✅ **동시성 제어**: Lock으로 CACHE 보호
6. ✅ **로깅 시스템**: structlog로 체계적 로그
7. ✅ **타입 힌트 완성**: mypy 검사 통과
8. ✅ **설정 클래스**: pydantic-settings 활용

### 장기 개선 (Low Priority)
9. ✅ **테스트 코드**: pytest로 커버리지 80% 이상
10. ✅ **CI/CD 구축**: GitHub Actions
11. ✅ **성능 최적화**: ANN 알고리즘 (FAISS)
12. ✅ **모니터링**: Prometheus + Grafana

---

## 📈 벤치마크 (예상)

| 티커 개수 | 데이터 로드 | 유사도 검색 | 메모리 사용 |
|----------|------------|-----------|-----------|
| 50       | ~5초       | ~10ms     | ~0.8 MB   |
| 200      | ~20초      | ~40ms     | ~3.2 MB   |
| 1000     | ~2분       | ~200ms    | ~16 MB    |
| 5000     | ~10분      | ~1초      | ~80 MB    |

*네트워크 속도 및 Yahoo Finance API 응답 시간에 따라 변동*

---

## 🧪 테스트 시나리오

### 단위 테스트
```python
# tests/test_features.py
def test_zscore_normalization():
    y = np.array([1, 2, 3, 4, 5])
    result = zscore(y)
    assert abs(result.mean()) < 1e-6
    assert abs(result.std() - 1.0) < 1e-6

# tests/test_similar.py
def test_dtw_distance():
    a = np.array([1, 2, 3, 4, 5])
    b = np.array([1, 2, 3, 4, 5])
    assert dtw_distance(a, b) == 0.0
```

### 통합 테스트
```python
# tests/test_api.py
from fastapi.testclient import TestClient

def test_ingest_endpoint():
    client = TestClient(app)
    response = client.post("/ingest?max_tickers=10",
                          json={"days": 365})
    assert response.status_code == 200
    assert "tickers_count" in response.json()
```

---

## 🔒 보안 체크리스트

- [ ] CORS 설정 제한
- [ ] API 레이트 리밋 추가
- [ ] 입력 검증 강화 (Pydantic validator)
- [ ] SQL Injection 방지 (현재 해당 없음)
- [ ] XSS 방지 (프론트엔드 sanitize)
- [ ] HTTPS 적용 (프로덕션)
- [ ] 인증/인가 시스템 (향후 추가)
- [ ] 환경 변수로 민감 정보 관리

---

## 📚 참고 자료

### 알고리즘
- [Dynamic Time Warping](https://en.wikipedia.org/wiki/Dynamic_time_warping)
- [Pearson Correlation](https://en.wikipedia.org/wiki/Pearson_correlation_coefficient)
- [Cosine Similarity](https://en.wikipedia.org/wiki/Cosine_similarity)

### 라이브러리
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [yfinance 사용법](https://pypi.org/project/yfinance/)
- [fastdtw GitHub](https://github.com/slaypni/fastdtw)

---

## 🎓 학습 포인트

이 프로젝트는 다음 개념을 학습하기에 적합합니다:

1. **시계열 분석**: MA20, 정규화, 리샘플링
2. **유사도 알고리즘**: DTW, Pearson, Cosine
3. **FastAPI**: RESTful API, Pydantic, CORS
4. **데이터 파이프라인**: yfinance → Parquet → NumPy
5. **캐싱 전략**: 멀티레벨 캐싱, warmup
6. **Canvas API**: 마우스/터치 이벤트, 드로잉

---

## 📊 종합 평가

| 항목 | 점수 | 평가 |
|------|------|------|
| **기능성** | ⭐⭐⭐⭐⭐ | 핵심 기능 완벽 구현 |
| **코드 품질** | ⭐⭐⭐⭐ | 깔끔하지만 개선 여지 있음 |
| **보안** | ⭐⭐ | CORS, 예외 처리 취약 |
| **성능** | ⭐⭐⭐ | 기본은 좋으나 최적화 필요 |
| **유지보수성** | ⭐⭐⭐⭐ | 모듈화 우수 |
| **문서화** | ⭐⭐ | 주석/docstring 부족 |
| **테스트** | ⭐ | 테스트 코드 없음 |

**총점**: 3.4 / 5.0

---

## 🏁 결론

**DRS**는 시계열 패턴 매칭을 위한 교육용/연구용 프로토타입으로서 우수한 아키텍처를 갖추고 있습니다.

**강점**:
- 명확한 모듈 분리와 캐싱 전략
- 앙상블 기반의 robust한 유사도 측정
- 직관적인 Canvas UI

**개선 필요**:
- 보안 강화 (CORS, 레이트 리밋, 예외 처리)
- 테스트 코드 작성
- 로깅 및 모니터링 추가

**프로덕션 배포 전 필수 작업**:
1. 보안 이슈 해결 (CORS, 레이트 리밋)
2. 예외 처리 강화
3. 통합 테스트 작성
4. HTTPS 적용
5. 환경 변수 분리

---
