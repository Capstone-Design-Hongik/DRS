-- ============================================================
-- PostgreSQL 쿼리 로깅 활성화 (pgAdmin에서 실행)
-- ============================================================

-- 현재 로그 설정 확인
SHOW log_statement;
SHOW log_duration;

-- 모든 쿼리 로깅 활성화 (세션 레벨)
SET log_statement = 'all';
SET log_duration = 'on';
SET log_min_duration_statement = 0;  -- 모든 쿼리 (0ms 이상)

-- 또는 특정 시간 이상만 로깅 (예: 100ms 이상)
-- SET log_min_duration_statement = 100;

-- ============================================================
-- 실행 중인 쿼리 실시간 모니터링
-- ============================================================

-- 현재 실행 중인 쿼리 확인
SELECT
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    query
FROM pg_stat_activity
WHERE state != 'idle'
  AND query NOT ILIKE '%pg_stat_activity%'
ORDER BY query_start DESC;

-- ============================================================
-- 쿼리 통계 확인 (pg_stat_statements 필요)
-- ============================================================

-- pg_stat_statements 확장 설치 (한 번만)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- 가장 많이 실행된 쿼리 Top 10
SELECT
    calls,
    total_exec_time::numeric(10,2) as total_time_ms,
    mean_exec_time::numeric(10,2) as avg_time_ms,
    query
FROM pg_stat_statements
WHERE query LIKE '%graph_segments%'
ORDER BY calls DESC
LIMIT 10;

-- 가장 느린 쿼리 Top 10
SELECT
    calls,
    total_exec_time::numeric(10,2) as total_time_ms,
    mean_exec_time::numeric(10,2) as avg_time_ms,
    query
FROM pg_stat_statements
WHERE query LIKE '%graph_segments%'
ORDER BY mean_exec_time DESC
LIMIT 10;

-- 통계 초기화 (필요 시)
-- SELECT pg_stat_statements_reset();
