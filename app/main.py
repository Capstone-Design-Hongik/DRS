# app/main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import numpy as np, pandas as pd, time

from .models import IngestRequest, SketchRequest, SimilarResponse, SimilarResponseItem
from .tickers import get_tickers
from .data_io import (
    download_ohlc,  # fallback
    last_n_days, compute_ma20,
    save_ma20_parquet, save_meta, load_ma20_parquet
)
from .features import dict_to_matrix, normalize_pipeline
from .similar import rank_top_k

app = FastAPI(title="DRS - Drawing Stock")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

CACHE = {
    "matrix": None,
    "tickers": None,
    "target_len": 200,
    "norm_map": None,   # ticker -> normalized vector(list)
}

@app.on_event("startup")
def warmup():
    # 서버 시작 시, 기존 캐시(parquet)가 있으면 메모리 캐시 생성
    df = load_ma20_parquet()
    if df is not None and not df.empty:
        ma20 = {c: df[c].dropna() for c in df.columns}
        matrix, T = dict_to_matrix(ma20, target_len=CACHE["target_len"])
        norm_map = {t: matrix[i, :].tolist() for i, t in enumerate(T)}
        CACHE.update({"matrix": matrix, "tickers": T, "norm_map": norm_map})

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ingest")
def ingest(
    req: IngestRequest,
    force_refresh: bool = Query(False),
    max_tickers: int = Query(5000, ge=10, le=5000)  # 기본 5000개 사용
):
    # 1) 티커 로드(캐시/리프레시 지원)
    tickers = get_tickers(max_count=max_tickers, force_refresh=force_refresh)

    # 2) 가격 다운로드(견고 버전 우선)
    try:
        from .data_io import download_ohlc_robust
        raw, ok = download_ohlc_robust(tickers, period="2y")
        if raw is None or raw.empty:
            raise HTTPException(500, "가격 데이터를 가져오지 못했습니다.")
    except ImportError:
        raw = download_ohlc(tickers, period="2y")
        ok = tickers

    # 3) 기간 슬라이싱 & MA20 계산
    raw = last_n_days(raw, n=req.days)
    ma20 = compute_ma20(raw)

    # 4) 디스크 캐시 저장
    p = save_ma20_parquet(ma20)
    save_meta({
        "tickers": list(ma20.keys()),
        "file": p,
        "days": req.days,
        "ts": time.time(),
        "ok_count": len(ok)
    })

    # 5) 메모리 캐시 준비(행렬/티커/정규화 맵)
    matrix, T = dict_to_matrix(ma20, target_len=CACHE["target_len"])
    norm_map = {t: matrix[i, :].tolist() for i, t in enumerate(T)}
    CACHE.update({"matrix": matrix, "tickers": T, "norm_map": norm_map})

    return {"tickers_count": len(T), "ok_count": len(ok), "target_len": CACHE["target_len"]}

@app.post("/refresh_tickers")
def refresh_tickers(max_tickers: int = Query(5000, ge=10, le=5000)):
    """
    NASDAQ API에서 강제로 티커를 다시 받아와 캐시 파일만 갱신합니다. (가격 다운로드는 아님)
    """
    syms = get_tickers(max_count=max_tickers, force_refresh=True)
    return {"refreshed": len(syms)}

@app.post("/similar", response_model=SimilarResponse)
def similar(req: SketchRequest):
    # 캐시 없거나 norm_map 미구성 → 디스크에서 불러와 구성
    if CACHE["matrix"] is None or CACHE.get("norm_map") is None:
        df = load_ma20_parquet()
        if df is None or df.empty:
            raise HTTPException(400, "먼저 /ingest로 데이터 캐시를 준비하세요.")
        ma20 = {c: df[c].dropna() for c in df.columns}
        matrix, T = dict_to_matrix(ma20, target_len=req.target_len)
        norm_map = {t: matrix[i, :].tolist() for i, t in enumerate(T)}
        CACHE.update({"matrix": matrix, "tickers": T, "target_len": req.target_len, "norm_map": norm_map})

    # 스케치 정규화
    y = np.array(req.y, dtype=float)
    sketch_vec = normalize_pipeline(y, target_len=CACHE["target_len"])

    # Top5 랭킹
    pairs = rank_top_k(sketch_vec, CACHE["matrix"], CACHE["tickers"], k=5)

    # 응답(오버레이용 정규화 시리즈 포함)
    items = []
    for i, (t, s) in enumerate(pairs):
        series_norm = CACHE["norm_map"].get(t)
        if series_norm is None:
            idx = CACHE["tickers"].index(t)
            series_norm = CACHE["matrix"][idx, :].tolist()
        items.append(SimilarResponseItem(
            ticker=t, score=s, rank=i+1,
            series_norm=series_norm,       # 해당 종목 MA20 (정규화)
            sketch_norm=sketch_vec.tolist()# 스케치 (정규화)
        ))
    return SimilarResponse(items=items)
