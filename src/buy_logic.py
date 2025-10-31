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
from src.data_preprocessing import extract_from_statements


def buy_score(info_dict, income_q, cashflow_q, balance_q, income_y, cashflow_y, importance_factors):
    # Profitability snapshot (convert decimals → %)
    gm  = _to_pct(info_dict.get('grossMargins', 0))
    om  = _to_pct(info_dict.get('operatingMargins', 0))
    roe = _to_pct(info_dict.get('returnOnEquity', 0))

    # Valuation
    fpe = _to_float(info_dict.get('forwardPE', 0))
    peg = _to_float(info_dict.get('trailingPegRatio', 0))
    ev_ebitda = _to_float(info_dict.get('enterpriseToEbitda', 0))

    (rev_g, fcf_margin, debt_eq, curr_ratio,
     stability, moat, rd_intensity, invest_ratio) = extract_from_statements(
        info_dict, income_q, cashflow_q, balance_q, income_y, cashflow_y
    )

    # Core subscores
    
    ##### growth

    # growth = _pos(rev_g, 5, 40)

    # improving recent quarterly operating margin
    if ('Operating Margin' in income_q.index) and income_q.shape[1] >= 5:
        om_now  = _to_float(income_q.loc['Operating Margin'].iloc[0])
        om_prev = _to_float(income_q.loc['Operating Margin'].iloc[4])
        om_change = om_now - om_prev
    else:
        om_change = 0.0
    
    # improving yearly operating margin
    if ('Operating Margin' in income_y.index) and income_y.shape[1] >= 4:
        om_y_recent  = _to_float(income_y.loc['Operating Margin'].iloc[0]+income_y.loc['Operating Margin'].iloc[1])
        om_y_prev = _to_float(income_y.loc['Operating Margin'].iloc[2]+income_y.loc['Operating Margin'].iloc[3])
        om_y_change = om_y_recent - om_y_prev
    else:
        om_y_change = 0.0

    growth = (
        _pos(rev_g, 5, 40)*0.5 +     # growth rewarded
        _pos(om_change, 0, 12)*0.2+
        _pos(om_y_change, 0, 8)*0.3 # margin expansion rewarded
    )
    

    ##### profitability
    profitability = (
        _pos(gm, 40, 70) +
        _pos(om, 15, 45) +
        _pos(roe, 10, 40) +
        _pos(fcf_margin, 5, 35)
    ) / 4.0


    ##### valuation
    # if peg <= 0:
    #     valuation = _neg(fpe, 10, 45)
    # else:
    #     valuation = (_neg(fpe, 10, 45) + _neg(peg, 0.5, 3.0)) / 2.0

    # Component scores
    V_PE = _neg(fpe, 12, 45)
    V_EV = _neg(ev_ebitda, 6, 30)

    # Choose PEG or GAV
    if peg and peg > 0:
        V_driver = _neg(peg, 0.5, 3.0)
    else:
        GAV = (ev_ebitda / rev_g) if (ev_ebitda > 0 and rev_g and rev_g > 0) else None
        V_driver = _neg(GAV, 0.4, 2.5) if GAV is not None else V_PE  # fallback to PE if no growth

    valuation = 0.5 * V_PE + 0.3 * V_EV + 0.2 * V_driver

    ##### safety

    safety = (
        _neg(debt_eq, 0.0, 1.0) +
        _pos(curr_ratio, 1.0, 3.0)
    ) / 2.0

    # New subscores (using annuals)

    stability = 0.5 if pd.isna(stability) else stability
    moat      = 0.5 if pd.isna(moat) else moat
    rd_score  = 0 if pd.isna(rd_intensity) else _pos(rd_intensity, 5, 22)
    invest_sc = 0.5 if pd.isna(invest_ratio) else _neg(invest_ratio, 15, 60)
    
    score01 = (
        importance_factors['growth']*growth +
        importance_factors['profitability']*profitability +
        importance_factors['valuation']*valuation +
        importance_factors['safety']*safety +
        importance_factors['stability']*stability +
        importance_factors['moat']*moat +
        importance_factors['rd_score']*rd_score +
        importance_factors['invest_score']*invest_sc
    )
    score = round(100*score01, 1)

    metric_vals = [
        gm, om, roe, fpe, peg,
        rev_g, fcf_margin, debt_eq, curr_ratio,
        rd_intensity, invest_ratio,
        growth, profitability, valuation, safety,
        stability, moat, rd_score, invest_sc,
        score
    ]
    return score, metric_vals




def rank_stocks(bundles, importance_factors):
    """
    bundles: [{'fund': info_dict,
               'inc_q': incQ, 'cf_q': cfQ, 'bs_q': bsQ,
               'inc_y': incY, 'cf_y': cfY}, ...]
    """
    out = []
    ticker_df = pd.DataFrame(columns=["Company", "Growth Margin", "Operating Margin", "ROE", "Forward P/E", "PEG", "Revenue TTM Growth", "FCF Margin", "Debt/Equity", "Current Ratio", "R&D Intensity", "Investment Ratio", "Growth", "Profitability", "Valuation", "Safety", "Stability Score (Rev- Var)", "Moat Score (G.Margin- Var)", "R&D Score", "Investment Score", "Score"])
    for b in bundles:
        name = b['fund'].get('longName') or b['fund'].get('shortName') or b['fund'].get('symbol') or 'Unknown'
        sc, metric_vals = buy_score(b['fund'], b['inc_q'], b['cf_q'], b['bs_q'], b['inc_y'], b['cf_y'], importance_factors)
        ticker_df.loc[len(ticker_df)] = [name] + metric_vals
        out.append((name, sc, score_label(sc)))
    return sorted(out, key=lambda x: x[1], reverse=True), ticker_df