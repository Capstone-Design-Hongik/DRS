from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import numpy as np, pandas as pd, time
from .models import IngestRequest, SketchRequest, SimilarResponse, SimilarResponseItem
from .tickers import TOP100
from .data_io import download_ohlc, last_n_days, compute_ma20, save_ma20_parquet, save_meta, load_ma20_parquet
from .features import dict_to_matrix, normalize_pipeline
from .similar import rank_top_k

app = FastAPI(title="DRS - Drawing Stock")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

CACHE = {"matrix": None, "tickers": None, "target_len": 200, "norm_map": None,}

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ingest")
def ingest(req: IngestRequest):
    tickers = TOP100
    raw = download_ohlc(tickers, period="2y")
    raw = last_n_days(raw, n=req.days)
    ma20 = compute_ma20(raw)

    p = save_ma20_parquet(ma20)
    save_meta({"tickers": list(ma20.keys()), "file": p, "days": req.days, "ts": time.time()})

    matrix, T = dict_to_matrix(ma20, target_len=CACHE["target_len"])
    norm_map = {}
    for i, t in enumerate(T):
        norm_map[t] = matrix[i, :].tolist()
    CACHE["matrix"], CACHE["tickers"], CACHE["norm_map"] = matrix, T, norm_map
    return {"tickers_count": len(T), "target_len": CACHE["target_len"]}
    
    

@app.post("/similar", response_model=SimilarResponse)
def similar(req: SketchRequest):
    if CACHE["matrix"] is None:
        df = load_ma20_parquet()
        if df is None or df.empty:
            raise HTTPException(400, "먼저 /ingest로 데이터 캐시를 준비하세요.")
        ma20 = {c: df[c].dropna() for c in df.columns}
        matrix, T = dict_to_matrix(ma20, target_len=req.target_len)
        CACHE.update({"matrix": matrix, "tickers": T, "target_len": req.target_len})

    y = np.array(req.y, dtype=float)
    sketch_vec = normalize_pipeline(y, target_len=CACHE["target_len"])

    pairs = rank_top_k(sketch_vec, CACHE["matrix"], CACHE["tickers"], k=5)

    items = []
    for i, (t, s) in enumerate(pairs):
        series_norm = CACHE["norm_map"][t]  # 정규화된 MA20
        items.append(SimilarResponseItem(
            ticker=t, score=s, rank=i+1,
            series_norm=series_norm,
            sketch_norm=sketch_vec.tolist()
        ))
    return SimilarResponse(items=items)
# series_norm: 정규화된 MA20 시계열
