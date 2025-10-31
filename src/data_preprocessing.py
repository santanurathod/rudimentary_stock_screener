import finvizfinance as fz
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as dt
from finvizfinance.quote import finvizfinance, Statements, Quote
import yfinance as yf
import math

from src.helper_functions import (
    _to_float, _to_pct, _pos, _neg, 
    _series_recentN, _weighted_recent, _safe_cv, 
    _blend, _median, score_label
)

# global variables hardcoded
ALPHA_GROWTH_RECENT   = 0.7  # TTM vs 3y CAGR
ALPHA_STAB_RECENT     = 0.6  # quarterly vs annual CV score
ALPHA_MOAT_RECENT     = 0.6
ALPHA_RD_RECENT       = 0.7  # TTM vs annual avg
ALPHA_INV_RECENT      = 0.7


def extract_from_statements(info_dict, income_q, cashflow_q, balance_q, income_y, cashflow_y):
    # ---------- TTM (RECENT) ----------
    rev_q = _series_recentN(income_q, 'Total Revenue', 5)
    gp_q  = _series_recentN(income_q, 'Gross Profit', 5)
    rd_q  = _series_recentN(income_q, 'Research And Development', 5)
    capex_q = _series_recentN(cashflow_q, 'Capital Expenditure', 5)
    ocf_q   = _series_recentN(cashflow_q, 'Operating Cash Flow', 5)

    # TTM sums (last 4 quarters)
    rev_ttm = sum(rev_q[:4]); gp_ttm = sum(gp_q[:4]); rd_ttm = sum(rd_q[:4])
    capex_ttm = sum(abs(x) for x in capex_q[:4]); ocf_ttm = sum(ocf_q[:4])

    # Growth (recent): YoY from quarters (Q0 vs Q4 if present)
    rev_ttm_growth_recent = None
    if len(rev_q) >= 5 and rev_q[4] > 0:
        rev_ttm_growth_recent = ((rev_q[0] - rev_q[4]) / rev_q[4]) * 100.0

    # Stability (recent): CV of quarterly YoY over available pairs
    rev_yoy_recent = []
    if len(rev_q) >= 5:
        for i in range(len(rev_q)-4):
            base = rev_q[i+4]
            rev_yoy_recent.append(((rev_q[i]-base)/base*100.0) if base>0 else 0.0)
    rev_cv_recent = _safe_cv(rev_yoy_recent) if len(rev_yoy_recent) >= 2 else None
    stability_score_recent = None if rev_cv_recent is None else _neg(rev_cv_recent, 0.3, 1.5)

    # Moat (recent): CV of quarterly GM% (5 points)
    gm_q = [(gp_q[i]/rev_q[i]*100.0) if rev_q[i]>0 else 0.0 for i in range(len(rev_q))]
    gm_cv_recent = _safe_cv(gm_q) if len(gm_q) >= 3 else None
    moat_score_recent = None if gm_cv_recent is None else _neg(gm_cv_recent, 0.05, 0.25)

    # R&D intensity (recent TTM %)
    rd_intensity_recent = (rd_ttm/rev_ttm*100.0) if rev_ttm>0 else None

    # Investment ratio (recent TTM %)
    invest_recent = (capex_ttm/ocf_ttm*100.0) if ocf_ttm>0 else None

    # ---------- ANNUAL (HISTORICAL) ----------
    # Growth (long): 3y CAGR using 4 annual years y0..y3
    rev_growth_long = None
    if ('Total Revenue' in income_y.index) and (income_y.shape[1] >= 4):
        r0 = _to_float(income_y.loc['Total Revenue'].iloc[0])
        r3 = _to_float(income_y.loc['Total Revenue'].iloc[3])
        if r3 > 0:
            rev_growth_long = ((r0/r3)**(1/3) - 1) * 100.0

    # Stability (long): CV of annual YoY across 3 intervals
    stability_score_long = None
    if ('Total Revenue' in income_y.index) and (income_y.shape[1] >= 4):
        ry = [_to_float(income_y.loc['Total Revenue'].iloc[i], 0.0) for i in range(4)]
        yoy = [((ry[i]-ry[i+1])/ry[i+1]*100.0) if ry[i+1]>0 else 0.0 for i in range(3)]
        cv_long = _safe_cv(yoy) if len(yoy) >= 2 else None
        stability_score_long = None if cv_long is None else _neg(cv_long, 0.3, 1.5)

    # Moat (long): CV of annual GM% over 4 years
    moat_score_long = None
    if all(lbl in income_y.index for lbl in ['Gross Profit','Total Revenue']) and (income_y.shape[1] >= 4):
        gp_y = [_to_float(income_y.loc['Gross Profit'].iloc[i], 0.0) for i in range(4)]
        rv_y = [_to_float(income_y.loc['Total Revenue'].iloc[i], 0.0) for i in range(4)]
        gm_y = [(gp_y[i]/rv_y[i]*100.0) if rv_y[i]>0 else 0.0 for i in range(4)]
        gm_cv_long = _safe_cv(gm_y) if len(gm_y) >= 2 else None
        moat_score_long = None if gm_cv_long is None else _neg(gm_cv_long, 0.05, 0.25)

    # R&D intensity (long): average of last 3 annual R&D%
    rd_intensity_long = None
    if all(lbl in income_y.index for lbl in ['Research And Development','Total Revenue']) and (income_y.shape[1] >= 3):
        rds = []
        for i in range(3):
            rev_i = _to_float(income_y.loc['Total Revenue'].iloc[i], 0.0)
            rd_i  = _to_float(income_y.loc['Research And Development'].iloc[i], 0.0)
            rds.append((rd_i/rev_i*100.0) if rev_i>0 else None)
        rds = [x for x in rds if x is not None]
        rd_intensity_long = sum(rds)/len(rds) if rds else None

    # Investment ratio (long): median of last 3 annual CapEx/OCF
    invest_long = None
    if (cashflow_y is not None) and all(lbl in cashflow_y.index for lbl in ['Capital Expenditure','Operating Cash Flow']) and (cashflow_y.shape[1] >= 3):
        vals = []
        for i in range(3):
            cap = abs(_to_float(cashflow_y.loc['Capital Expenditure'].iloc[i], 0.0))
            ocf = _to_float(cashflow_y.loc['Operating Cash Flow'].iloc[i], 0.0)
            vals.append((cap/ocf*100.0) if ocf>0 else None)
        invest_long = _median(vals)

    # ---------- BLEND ----------
    # Growth (use raw %)
    
    rev_growth = _blend(rev_ttm_growth_recent, rev_growth_long, ALPHA_GROWTH_RECENT)
    

    # Stability & Moat are already scores in 0..1 (after _neg), blend scores directly
    stability_score = _blend(stability_score_recent, stability_score_long, ALPHA_STAB_RECENT)
    moat_score      = _blend(moat_score_recent,      moat_score_long,      ALPHA_MOAT_RECENT)
    

    # R&D intensity (%), Investment ratio (%)
    rd_intensity = _blend(rd_intensity_recent, rd_intensity_long, ALPHA_RD_RECENT)
    invest_ratio = _blend(invest_recent,       invest_long,       ALPHA_INV_RECENT)
    
    # ---------- Core items unchanged ----------
    fcf4 = _series_recentN(cashflow_q, 'Free Cash Flow', 4)
    rev4 = _series_recentN(income_q,   'Total Revenue', 4)
    fcf_w = _weighted_recent(fcf4, [1.0, 0.75, 0.50, 0.25])
    rev_w = _weighted_recent(rev4,     [1.0, 0.75, 0.50, 0.25])
    fcf_margin = (fcf_w/rev_w*100.0) if rev_w>0 else 0.0

    if ('Current Assets' in balance_q.index) and ('Current Liabilities' in balance_q.index):
        ca = _to_float(balance_q.loc['Current Assets'].iloc[0]); cl = _to_float(balance_q.loc['Current Liabilities'].iloc[0])
        curr_ratio = (ca/cl) if (cl and cl!=0) else _to_float(info_dict.get('currentRatio', 1.0))
    else:
        curr_ratio = _to_float(info_dict.get('currentRatio', 1.0))

    if ('Total Debt' in balance_q.index) and ('Stockholders Equity' in balance_q.index):
        td = _to_float(balance_q.loc['Total Debt'].iloc[0], 0.0); se = _to_float(balance_q.loc['Stockholders Equity'].iloc[0], 0.0)
        debt_eq = (td / se) if (se > 0 and not math.isnan(td)) else _to_float(info_dict.get('debtToEquity', 0.0)/100)
    else:
        debt_eq = _to_float(info_dict.get('debtToEquity', 0.0))/100.0

    return (rev_growth, fcf_margin, debt_eq, curr_ratio,
            stability_score, moat_score, rd_intensity, invest_ratio)