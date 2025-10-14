# app/tickers.py
import requests, time, json, re
from pathlib import Path
from typing import List

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
CACHE_FILE = DATA_DIR / "tickers_nasdaq.json"
CACHE_TTL_SEC = 24 * 3600  # 캐시 유효기간 1일

HEADERS = {"User-Agent": "Mozilla/5.0"}
NASDAQ_API = "https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=9999"

_symbol_ok = re.compile(r"^[A-Z][A-Z0-9\.\-]*$")

def _normalize_for_yfinance(symbol: str) -> str:
    s = symbol.strip().upper().replace(".", "-")
    return s

def _looks_like_equity(symbol: str) -> bool:
    if not _symbol_ok.match(symbol):
        return False
    bad_prefix = ("^", "$")
    if symbol.startswith(bad_prefix):
        return False
    s = _normalize_for_yfinance(symbol)
    bad_fragments = ("-WT", "-WS", "-W", "-R", "-U")  # SPAC/워런트 등 제외
    if any(s.endswith(f) for f in bad_fragments):
        return False
    return True

def fetch_tickers_from_nasdaq() -> List[str]:
    r = requests.get(NASDAQ_API, headers=HEADERS, timeout=30)
    r.raise_for_status()
    rows = r.json()["data"]["table"]["rows"]
    raw_symbols = [row["symbol"] for row in rows if row.get("symbol")]
    raw_symbols = [s for s in raw_symbols if _looks_like_equity(s)]
    yf_symbols = [_normalize_for_yfinance(s) for s in raw_symbols]
    uniq = sorted(set(yf_symbols))
    return uniq

def load_cached_tickers() -> List[str] | None:
    if CACHE_FILE.exists():
        mtime = CACHE_FILE.stat().st_mtime
        if (time.time() - mtime) < CACHE_TTL_SEC:
            try:
                return json.loads(CACHE_FILE.read_text())
            except Exception:
                return None
    return None

def save_cached_tickers(symbols: List[str]) -> None:
    CACHE_FILE.write_text(json.dumps(symbols, indent=2))

def get_tickers(max_count: int = 5000, force_refresh: bool = False) -> List[str]:
    """NASDAQ 전체 티커 중 상위 max_count개 반환"""
    if not force_refresh:
        cached = load_cached_tickers()
        if cached:
            return cached[:max_count]
    syms = fetch_tickers_from_nasdaq()
    save_cached_tickers(syms)
    return syms[:max_count]
