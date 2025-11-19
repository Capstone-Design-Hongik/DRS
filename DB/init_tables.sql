-- DRS 프로젝트 데이터베이스 테이블 생성

-- 1. stocks 테이블 (티커 메타데이터)
CREATE TABLE IF NOT EXISTS stocks (
    ticker VARCHAR(20) PRIMARY KEY,
    company_name VARCHAR(255),
    exchange VARCHAR(50),
    sector VARCHAR(100),
    market_cap BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. prices 테이블 (가격 데이터)
CREATE TABLE IF NOT EXISTS prices (
    ticker VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    open NUMERIC(12, 4),
    high NUMERIC(12, 4),
    low NUMERIC(12, 4),
    close NUMERIC(12, 4),
    adj_close NUMERIC(12, 4),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, trade_date),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
);

-- 3. graph_segments 테이블 (벡터 세그먼트)
CREATE TABLE IF NOT EXISTS graph_segments (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    ma_type VARCHAR(10) NOT NULL,  -- 'MA20' or 'MA30'
    segment_start DATE NOT NULL,
    segment_end DATE,
    vector REAL[],  -- 128차원 벡터
    volatility REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_prices_ticker ON prices(ticker);
CREATE INDEX IF NOT EXISTS idx_prices_date ON prices(trade_date);
CREATE INDEX IF NOT EXISTS idx_segments_ticker ON graph_segments(ticker);
CREATE INDEX IF NOT EXISTS idx_segments_ma_type ON graph_segments(ma_type);

-- 완료 메시지
SELECT 'Tables created successfully!' AS status;
