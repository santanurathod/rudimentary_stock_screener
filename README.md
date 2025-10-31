# Buy Score Logic

## Note: this is not an investment advice, but a mere sanity check, please do your own due diligence before investing

This repo contains a personal framework for ranking and comparing companies for investments over a ~2-year horizon.  It’s not a screener in the conventional sense — it’s meant to balance **growth**, **profitability**, **valuation**, and **financial safety**, and then quantify that balance into a consistent “Buy Score”.

---


## the idea and philosophy
I wanted a scoring logic that sits between quant and intuition:  
something data-driven enough to run across a watchlist, but still intuitive to interpret all in a structured way to separate *good companies at good prices* from noise.

The goal is to find companies that would likely beat an index fund simply because they’re:
- growing steadily,
- cash positive,
- sensibly priced,
- and not financially fragile.


So the framework rewards companies that are:

- **growing** (revenues + improving margins)
- **profitable and cash-rich**
- **reasonably valued** for their quality
- **financially safe** (low leverage, good liquidity)
- **consistent** in execution
- **reinvesting wisely** (R&D and CapEx discipline)

It’s basically **quality-growth at a sensible price**.

## tl;dr

> **Buy businesses that are growing and improving, generate cash, aren’t overpriced, and don’t blow up on leverage.**

---

## data inputs

- **Quarterly statements (last 5 quarters)** → momentum, margin trend  
- **Annual statements (last 4 years)** → historical consistency  
- **Yahoo / Finviz snapshot** → forward P/E, PEG, margins, ROE, etc.  

Each metric is normalized between 0 and 1.  
Recent data gets higher weight (roughly 70% recent, 30% historical).

---

## Factors Considered:

### 1. Growth
Focuses on:
- Revenue growth (recent 12 months vs previous year)  
- Operating margin improvement (quarterly + annual)  

It rewards both *scale* and *efficiency*.  
Pure topline growth without better margins doesn’t count as “quality growth”.

---

### 2. Profitability
Averages:
- Gross Margin  
- Operating Margin  
- ROE  
- FCF Margin  

Simple rule: high margins → better economics → higher score.

---

### 3. Valuation
Uses:
- Forward P/E  
- EV/EBITDA  
- PEG (if available)  
- fallback = EV/EBITDA ÷ growth  

Weighted roughly 50/30/20.  
Lower ratios mean cheaper valuation.  
PEG is preferred when available; otherwise growth-adjusted value is used.

---

### 4. Safety
Checks:
- Debt-to-Equity (lower is better)  
- Current Ratio (higher is better)  

Average of both → balance sheet health.

---

### 5. Stability
Measures **revenue consistency** over time (coefficient of variation).  
Stable revenue growth = better predictability.

---

### 6. Moat
Same logic as stability, but for **gross margins**.  
If GM% doesn’t swing much, the company likely has pricing power or cost control.  
That’s the moat proxy.

---

### 7. R&D Score
R&D spend as % of revenue (recent + 3-year avg).  
Healthy range ≈ 5%–20%.  
Encourages innovation without excessive burn.

---

### 8. Investment Discipline
CapEx as % of Operating Cash Flow.  
Lower is better for a 2-year window (cash flexibility > over-expansion).  
Over 60% starts hurting the score.

---

## weighting and score interpretation

Each pillar is weighted through `importance_factors` and combined into a 0–100 score:


---

---

## future improvements

- Add sector-relative scoring  
- Penalize dilution (shares outstanding trend)  
- Add optional macro filter (interest rate regime)  
- Include insider ownership & FCF yield  

---

### How to Use

#### Step 0 (no need to run)
One can simply open and read the notebook file: ([main]: `analysis_yfinance.ipynb`)

#### Step 1
If you want to run your own companies, modify the tickers at the beginning of the notebook, e.g.

```python
tickers = [
    # Semiconductor Equipment & Materials
    "NVDA", "AMD", "TSM",

    # Cloud / Data platforms
    "DDOG", "SNOW", "MDB", "ESTC",

    # Security
    "PANW", "CRWD", "ZS", "OKTA"
]
```
#### Step 2

use your importance factor in notebook section: "set hyperparameters"

```
importance_factors = {
    'growth': 0.3,
    'profitability': 0.3,
    'valuation': 0.15,
    'safety': 0.12,
    'stability': 0.13,
    'moat': 0,
    'rd_score': 0,
    'invest_score': 0
}
```

#### Step 3
Once the tickers and importance_factors are set, run the python notebook ([main]: analysis_yfinance.ipynb) entirely to scrape the ticker data from yfinance and then rank the companies.
