import numpy as np
from fastdtw import fastdtw
from scipy.stats import pearsonr
from numpy.linalg import norm

def dtw_distance(a: np.ndarray, b: np.ndarray) -> float:
    d, _ = fastdtw(a, b)
    return float(d)

def cosine_sim(a, b):
    return float(np.dot(a, b) / (norm(a) * norm(b) + 1e-9))

def pearson(a, b):
    r, _ = pearsonr(a, b)
    return float(r)

def ensemble_score(sketch, series, alpha=0.7, beta=0.2, gamma=0.1):
    d = dtw_distance(sketch, series)
    d_norm = -d / len(sketch)   # 거리 → 점수
    c = pearson(sketch, series)
    s = cosine_sim(sketch, series)
    return alpha * d_norm + beta * c + gamma * s

def rank_top_k(sketch_vec, db_matrix, tickers, k=5):
    scores = [ensemble_score(sketch_vec, row) for row in db_matrix]
    idx = np.argsort(scores)[::-1][:k]
    return [(tickers[i], float(scores[i])) for i in idx]
