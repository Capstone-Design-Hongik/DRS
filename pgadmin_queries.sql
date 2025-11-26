-- ============================================================
-- pgAdmin에서 실행해볼 수 있는 쿼리 모음
-- ============================================================

-- 1. 테이블 구조 확인
SELECT
    column_name,
    data_type,
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'graph_segments';

-- 2. 총 세그먼트 수 확인
SELECT
    ma_type,
    COUNT(*) as segment_count,
    COUNT(DISTINCT ticker) as unique_tickers
FROM graph_segments
GROUP BY ma_type;

-- 3. 특정 티커의 세그먼트 조회 (예: AAPL)
SELECT
    id,
    ticker,
    segment_start,
    segment_end,
    volatility,
    array_length(vector, 1) as vector_dimension
FROM graph_segments
WHERE ticker = 'AAPL' AND ma_type = 'MA20'
ORDER BY segment_start DESC
LIMIT 10;

-- 4. 변동성이 높은 세그먼트 Top 10
SELECT
    ticker,
    segment_start,
    segment_end,
    volatility
FROM graph_segments
WHERE ma_type = 'MA20'
ORDER BY volatility DESC
LIMIT 10;

-- 5. 특정 기간의 세그먼트 조회
SELECT
    ticker,
    segment_start,
    segment_end,
    volatility
FROM graph_segments
WHERE ma_type = 'MA20'
  AND segment_end >= '2024-10-01'
ORDER BY ticker, segment_start;

-- 6. 티커별 세그먼트 개수
SELECT
    ticker,
    COUNT(*) as segment_count,
    MIN(segment_start) as earliest_date,
    MAX(segment_end) as latest_date
FROM graph_segments
WHERE ma_type = 'MA20'
GROUP BY ticker
ORDER BY segment_count DESC
LIMIT 20;

-- 7. 벡터 데이터 샘플 (첫 10개 값만)
SELECT
    ticker,
    segment_start,
    vector[1:10] as first_10_values  -- 벡터의 첫 10개 요소
FROM graph_segments
WHERE ticker = 'AAPL' AND ma_type = 'MA20'
LIMIT 1;

-- 8. 특정 날짜 범위의 모든 티커 조회
SELECT DISTINCT ticker
FROM graph_segments
WHERE ma_type = 'MA20'
  AND segment_end >= '2024-10-01'
ORDER BY ticker;

-- ============================================================
-- PostgreSQL에서 간단한 유사도 계산 (수동)
-- ============================================================

-- 9. 두 벡터 간 유클리드 거리 계산 (예시)
-- 참고: 실제 유사도 계산은 Python에서 더 복잡하게 수행됨
WITH vector1 AS (
    SELECT vector
    FROM graph_segments
    WHERE ticker = 'AAPL' AND ma_type = 'MA20'
    LIMIT 1
),
vector2 AS (
    SELECT vector
    FROM graph_segments
    WHERE ticker = 'MSFT' AND ma_type = 'MA20'
    LIMIT 1
)
SELECT
    sqrt(
        (SELECT SUM(power(v1 - v2, 2))
         FROM unnest((SELECT vector FROM vector1)) WITH ORDINALITY AS t1(v1, idx)
         JOIN unnest((SELECT vector FROM vector2)) WITH ORDINALITY AS t2(v2, idx2)
           ON t1.idx = t2.idx2)
    ) as euclidean_distance;

-- 10. 벡터 통계 정보
SELECT
    ticker,
    segment_start,
    (SELECT AVG(v) FROM unnest(vector) AS v) as vector_mean,
    (SELECT STDDEV(v) FROM unnest(vector) AS v) as vector_stddev,
    (SELECT MIN(v) FROM unnest(vector) AS v) as vector_min,
    (SELECT MAX(v) FROM unnest(vector) AS v) as vector_max
FROM graph_segments
WHERE ticker = 'AAPL' AND ma_type = 'MA20'
LIMIT 5;
