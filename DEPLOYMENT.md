# DRS 배포 가이드

## 🚀 Render로 배포하기 (추천)

### 1단계: GitHub 푸시

```bash
git add .
git commit -m "chore: add deployment configuration"
git push origin main
```

### 2단계: Render 계정 생성

1. https://render.com 접속
2. **"Get Started for Free"** 클릭
3. GitHub 계정으로 로그인

### 3단계: PostgreSQL 데이터베이스 생성

1. Render 대시보드에서 **"New +"** → **"PostgreSQL"** 클릭
2. 설정:
   - **Name**: `drs-postgres`
   - **Database**: `drs_db`
   - **User**: `drs_user`
   - **Region**: 가까운 지역 선택 (예: Oregon, Singapore)
   - **Plan**: Free
3. **"Create Database"** 클릭
4. **Internal Database URL** 복사해두기 (나중에 사용)

### 4단계: 웹 서비스 생성

1. Render 대시보드에서 **"New +"** → **"Web Service"** 클릭
2. GitHub 리포지토리 연결: `Capstone-Design-Hongik/DRS` 선택
3. 설정:
   - **Name**: `drs-api`
   - **Region**: PostgreSQL과 같은 지역
   - **Branch**: `main`
   - **Root Directory**: (비워두기)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

### 5단계: 환경 변수 설정

**Environment** 탭에서 다음 환경 변수 추가:

```
DATA_SOURCE=postgresql
API_HOST=0.0.0.0
API_TITLE=DRS - Drawing Stock
LOG_LEVEL=INFO

# PostgreSQL 연결 정보 (Step 3의 Database URL에서 추출)
PG_HOST=dpg-xxxxx.oregon-postgres.render.com
PG_PORT=5432
PG_DATABASE=drs_db
PG_USER=drs_user
PG_PASSWORD=xxxxxxxxxxxxx

# 기타 설정
TARGET_LEN=200
CACHE_TTL_SEC=86400
MAX_TICKERS=5000
RATE_LIMIT_INGEST=5/minute
RATE_LIMIT_SIMILAR=20/minute
MIN_DATA_POINTS=30
MIN_MA_POINTS=25
PG_MIN_CONN=1
PG_MAX_CONN=10

# CORS (필요시 수정)
CORS_ORIGINS=["https://your-drs-api.onrender.com"]
```

### 6단계: 배포

**"Create Web Service"** 클릭하면 자동으로 배포가 시작됩니다!

배포 로그에서 진행 상황 확인 가능:
```
==> Building...
==> Installing dependencies...
==> Starting server...
✅ Your service is live at https://drs-api.onrender.com
```

---

## 📊 PostgreSQL 데이터 마이그레이션

배포 후 데이터를 옮겨야 합니다:

### 방법 1: pg_dump/pg_restore (추천)

```bash
# 로컬 DB 덤프
pg_dump -h 172.17.240.1 -p 5433 -U postgres -d drs_db \
  -F c -b -v -f drs_backup.dump

# Render DB에 복원
pg_restore -h dpg-xxxxx.oregon-postgres.render.com \
  -p 5432 -U drs_user -d drs_db -v drs_backup.dump
```

### 방법 2: 스크립트 재실행

```bash
# DB 스크립트 실행 (Render DB 정보로)
python DB/ingest_prices.py
python DB/build_segments.py
```

---

## 🔧 배포 후 테스트

1. **API 문서 확인**:
   ```
   https://your-drs-api.onrender.com/docs
   ```

2. **Health Check**:
   ```bash
   curl https://your-drs-api.onrender.com/health
   ```

3. **웹 인터페이스**:
   ```
   https://your-drs-api.onrender.com/web/index.html
   ```

---

## 💡 팁

### 무료 플랜 제한사항

- **Render Free Tier**:
  - 15분 동안 요청이 없으면 슬립 모드
  - 첫 요청 시 콜드 스타트 (~30초)
  - PostgreSQL: 90일 후 삭제 (활성화 필요)

### 성능 개선

- **Paid Plan**으로 업그레이드하면:
  - 항상 실행 (슬립 모드 없음)
  - 더 빠른 CPU/메모리
  - 자동 스케일링

---

## 🆘 문제 해결

### 1. 데이터베이스 연결 오류

```
ERROR: Connection to PostgreSQL failed
```

**해결**: 환경 변수 확인 (PG_HOST, PG_PORT, PG_PASSWORD)

### 2. 메모리 부족

```
ERROR: Out of memory
```

**해결**: Paid plan으로 업그레이드 또는 데이터 최적화

### 3. 타임아웃

```
ERROR: Request timeout
```

**해결**: `latest_only=True` 사용 (이미 적용됨)

---

## 📚 다른 플랫폼

### Railway

```bash
# Railway CLI 설치
npm i -g @railway/cli

# 로그인 및 배포
railway login
railway init
railway up
```

### Fly.io

```bash
# Fly CLI 설치
curl -L https://fly.io/install.sh | sh

# 배포
fly launch
fly deploy
```

---

## ✅ 체크리스트

배포 전 확인:
- [ ] `.env` 파일이 `.gitignore`에 포함됨
- [ ] `requirements.txt` 최신 버전
- [ ] PostgreSQL 데이터 백업 완료
- [ ] 환경 변수 설정 준비
- [ ] CORS 설정 확인

배포 후 확인:
- [ ] API 문서 접근 가능
- [ ] Health check 성공
- [ ] PostgreSQL 연결 성공
- [ ] 유사도 검색 작동
- [ ] 웹 인터페이스 작동
