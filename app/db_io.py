"""
PostgreSQL database integration for DRS
Provides connection management and vector retrieval from graph_segments table
"""
import os
import logging
from typing import List, Tuple, Optional
import numpy as np
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Connection pool (initialized on first use)
_pool: Optional[SimpleConnectionPool] = None


def init_pool(host: str, port: int, database: str, user: str, password: str, minconn: int = 1, maxconn: int = 10):
    """Initialize PostgreSQL connection pool"""
    global _pool
    if _pool is None:
        try:
            _pool = SimpleConnectionPool(
                minconn,
                maxconn,
                host=host,
                port=port,
                database=database,
                user=user,
                password=password
            )
            logger.info(f"PostgreSQL connection pool initialized: {database}@{host}:{port}")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    return _pool


@contextmanager
def get_connection():
    """Context manager for database connections"""
    if _pool is None:
        raise RuntimeError("Connection pool not initialized. Call init_pool() first.")

    conn = _pool.getconn()
    try:
        yield conn
    finally:
        _pool.putconn(conn)


def fetch_all_segments(ma_type: str = "MA20", latest_only: bool = False) -> Tuple[np.ndarray, List[str], List[dict]]:
    """
    Fetch all pre-computed vector segments from graph_segments table

    Args:
        ma_type: Moving average type (default "MA20")
        latest_only: If True, fetch only the latest segment per ticker (much faster!)

    Returns:
        Tuple of:
        - vectors: numpy array of shape (N, 128) - all segment vectors
        - tickers: list of ticker symbols for each segment
        - metadata: list of dicts with segment info (id, start_date, end_date, volatility)
    """
    if latest_only:
        # 티커당 최신 세그먼트만 (DISTINCT ON 사용)
        query = """
            SELECT DISTINCT ON (ticker)
                id,
                ticker,
                segment_start,
                segment_end,
                vector,
                volatility
            FROM graph_segments
            WHERE ma_type = %s
            ORDER BY ticker, segment_end DESC;
        """
    else:
        # 모든 세그먼트 (기존 방식)
        query = """
            SELECT
                id,
                ticker,
                segment_start,
                segment_end,
                vector,
                volatility
            FROM graph_segments
            WHERE ma_type = %s
            ORDER BY ticker, segment_start;
        """

    logger.info(f"🔍 Executing SQL Query: fetch_all_segments (latest_only={latest_only})")
    logger.info(f"   {query.strip()}")
    logger.info(f"   Parameters: ma_type='{ma_type}'")

    with get_connection() as conn:
        with conn.cursor() as cur:
            import time
            start_time = time.time()
            cur.execute(query, (ma_type,))
            rows = cur.fetchall()
            elapsed = time.time() - start_time
            logger.info(f"✅ Query executed in {elapsed:.3f}s, fetched {len(rows)} rows")

    if not rows:
        logger.warning(f"No segments found for ma_type={ma_type}")
        return np.array([]), [], []

    vectors = []
    tickers = []
    metadata = []

    for row in rows:
        seg_id, ticker, start_date, end_date, vector, volatility = row

        # Convert PostgreSQL array to numpy array
        if isinstance(vector, list):
            vec = np.array(vector, dtype=np.float32)
        else:
            # Handle potential string representation
            vec = np.array(eval(vector) if isinstance(vector, str) else vector, dtype=np.float32)

        vectors.append(vec)
        tickers.append(ticker)
        metadata.append({
            'id': seg_id,
            'ticker': ticker,
            'start_date': start_date,
            'end_date': end_date,
            'volatility': volatility
        })

    vectors_array = np.vstack(vectors)  # Shape: (N, 128)

    logger.info(f"Loaded {len(vectors)} segments from database (ma_type={ma_type})")

    return vectors_array, tickers, metadata


def fetch_latest_ma20_for_tickers(tickers: List[str], limit: int = 5) -> dict:
    """
    Fetch the most recent MA20 segment for each ticker

    Args:
        tickers: List of ticker symbols
        limit: Number of tickers to fetch

    Returns:
        Dict mapping ticker -> latest segment vector (128-dim)
    """
    if not tickers:
        return {}

    query = """
        SELECT DISTINCT ON (ticker)
            ticker,
            vector,
            segment_end
        FROM graph_segments
        WHERE ticker = ANY(%s) AND ma_type = 'MA20'
        ORDER BY ticker, segment_end DESC;
    """

    logger.info(f"🔍 Executing SQL Query: fetch_latest_ma20_for_tickers")
    logger.info(f"   Tickers: {tickers[:limit]} (limit: {limit})")

    with get_connection() as conn:
        with conn.cursor() as cur:
            import time
            start_time = time.time()
            cur.execute(query, (tickers[:limit],))
            rows = cur.fetchall()
            elapsed = time.time() - start_time
            logger.info(f"✅ Query executed in {elapsed:.3f}s, fetched {len(rows)} rows")

    result = {}
    for ticker, vector, end_date in rows:
        if isinstance(vector, list):
            vec = np.array(vector, dtype=np.float32)
        else:
            vec = np.array(eval(vector) if isinstance(vector, str) else vector, dtype=np.float32)
        result[ticker] = vec

    return result


def get_segment_count() -> int:
    """Get total number of segments in database"""
    query = "SELECT COUNT(*) FROM graph_segments WHERE ma_type = 'MA20';"

    logger.info(f"🔍 Executing SQL Query: get_segment_count")

    with get_connection() as conn:
        with conn.cursor() as cur:
            import time
            start_time = time.time()
            cur.execute(query)
            count = cur.fetchone()[0]
            elapsed = time.time() - start_time
            logger.info(f"✅ Query executed in {elapsed:.3f}s, count={count}")

    return count


def close_pool():
    """Close all connections in the pool"""
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
        logger.info("PostgreSQL connection pool closed")
