import numpy as np

def resample_series(y: np.ndarray, target_len: int) -> np.ndarray:
    x_old = np.linspace(0, 1, num=len(y))
    x_new = np.linspace(0, 1, num=target_len)
    return np.interp(x_new, x_old, y)

def zscore(y: np.ndarray, eps=1e-8) -> np.ndarray:
    mu, std = y.mean(), y.std()
    std = std if std > eps else eps
    return (y - mu) / std

def normalize_pipeline(y: np.ndarray, target_len: int) -> np.ndarray:
    y = resample_series(y, target_len)
    y = zscore(y)
    return y

def dict_to_matrix(ma_dict: dict, target_len: int):
    rows, tickers = [], []
    for t, s in ma_dict.items():
        y = s.values.astype(float)
        if len(y) < 30:
            continue
        rows.append(normalize_pipeline(y, target_len))
        tickers.append(t)
    import numpy as np
    return np.vstack(rows), tickers
