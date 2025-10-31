import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as dt
import math


def _to_float(x, default=0.0):
    if x is None:
        return default
    try:
        return float(x)
    except Exception:
        s = str(x).replace(",", "").strip()
        if s.endswith("%"):
            s = s[:-1]
        try:
            return float(s)
        except Exception:
            return default

def _to_pct(x, default=0.0):
    v = _to_float(x, default)
    if v is None:
        return default
    # Yahoo-style decimals (e.g., 0.60) -> %
    return v * 100.0 if -1.5 <= v <= 1.5 else v

def _pos(x, lo, hi):
    if pd.isna(x):
        return 0.0
    if x <= lo: return 0.0
    if x >= hi: return 1.0
    return (x - lo) / (hi - lo)

def _neg(x, lo, hi):
    if pd.isna(x):
        return 0.0
    if x <= lo: return 1.0
    if x >= hi: return 0.0
    return 1.0 - (x - lo) / (hi - lo)

def _series_recentN(df, row_label, n):
    if (df is None) or (row_label not in df.index):
        return [0.0] * n
    row = df.loc[row_label]
    m = min(n, row.shape[0])
    vals = [_to_float(row.iloc[i], 0.0) for i in range(m)]
    while len(vals) < n:
        vals.append(vals[-1] if vals else 0.0)
    return vals

def _weighted_recent(values, weights):
    k = min(len(values), len(weights))
    v = values[:k]; w = weights[:k]
    s = sum(w)
    if s == 0: return sum(v)/k if k else 0.0
    return sum(v[i]*w[i] for i in range(k)) / s

def _safe_cv(series):
    if not series: return None
    mu = sum(series) / len(series)
    if abs(mu) < 1e-9: return None
    var = sum((x - mu)**2 for x in series) / max(1, len(series) - 1)
    from math import sqrt
    return sqrt(var) / abs(mu)

def _blend(recent, long, alpha):
    if pd.isna(recent) and pd.isna(long): 
        return None
    if pd.isna(recent): 
        return long
    if pd.isna(long): 
        return recent
    return alpha*recent + (1-alpha)*long

    # try:
    #     if (recent is None) or (recent is pd.isna(recent)) and (long is None) or (long is pd.isna(long)): return None
    #     if (recent is None) or (recent is pd.isna(recent)): return long
    #     if (long   is None) or (long is pd.isna(long)): return recent
    #     return alpha*recent + (1-alpha)*long
    # except:
    #     import pdb; pdb.set_trace()
    # return None

def _median(xs):
    xs = [x for x in xs if x is not None]
    if not xs: return None
    xs = sorted(xs)
    n = len(xs)
    return xs[n//2] if n%2 else 0.5*(xs[n//2-1]+xs[n//2])


def score_label(score):
    if score >= 75: return "BUY (High Conviction)"
    if score >= 60: return "ACCUMULATE- HOLD"
    return "AVOID- WATCHLIST"
