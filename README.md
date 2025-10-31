## Note: this is not an investment advice, but a mere sanity check, please do your own due diligence before investing

## the idea and philosophy
I wanted a scoring logic that sits between quant and intuition:  
something data-driven enough to run across a watchlist, but still intuitive to interpret all in a structured way to separate *good companies at good prices* from noise.

The goal is to find companies that would likely beat an index fund simply because they’re:
- growing steadily,
- cash positive,
- sensibly priced,
- and not financially fragile.

# Buy Score Model  
*A quantitative framework for ranking public equities (2-year horizon)*

---

## 🧭 Overview

The **Buy Score** model is a quantitative system I built to rank public companies based on how *fundamentally strong, efficient, and reasonably valued* they are.  
It combines financial data from **Yahoo Finance (via yfinance)** and **Finviz** to produce a composite score between **0 and 100**.

The goal is to find **high-quality, well-priced businesses** that can outperform index funds over a 1–2 year period —  
companies that keep compounding even in flat or uncertain markets.

---

## ⚙️ Core Idea

Each company’s performance is evaluated across **eight pillars**:

1. **Growth** – scale and operating efficiency  
2. **Profitability** – margins and capital returns  
3. **Valuation** – price paid vs. quality  
4. **Safety** – balance sheet strength  
5. **Stability** – consistency of performance  
6. **Moat** – margin defensibility  
7. **R&D Intensity** – innovation without over-spend  
8. **Investment Discipline** – quality of capital allocation  

Every metric is normalized to a 0–1 range using simple linear scaling:

- `pos(x, low, high)` → higher values are better  
- `neg(x, low, high)` → lower values are better  

To capture both *momentum* and *sustainability*, the model blends recent (quarterly) and historical (annual) data as:  
`Final = α * Recent + (1 - α) * Long-Term`  
with α typically around 0.6–0.7.

---

## 🧩 Factor Breakdown

### 1. Growth
Captures both *top-line expansion* and *improving efficiency*.  
It’s not just about growing revenues — margins must expand too.

**Formula:**

Growth = 0.5 * pos(RevenueGrowth, 5, 40)+
 0.2 * pos(ΔOperatingMargin_quarterly, 0, 12)+
0.3 * pos(ΔOperatingMargin_annual, 0, 8)


A company growing 20–30% with expanding margins scores high;  
pure topline growth without efficiency gains doesn’t.

---

### 2. Profitability
Measures how well the company turns revenue into returns.

**Inputs:**
- Gross Margin (GM)  
- Operating Margin (OM)  
- Return on Equity (ROE)  
- Free Cash Flow Margin (FCF%)

**Formula:**
Profitability = 
(pos(GrossMargin, 40, 70)+
pos(OperatingMargin, 15, 45)+
pos(ROE, 10, 40)+
pos(FCF%, 5, 35))/4


Higher margins = stronger unit economics and durable returns.

---

### 3. Valuation
Checks whether the stock is reasonably priced relative to its quality and growth.  
Combines absolute and growth-adjusted valuation metrics.

**Inputs:**
- Forward P/E (lower = cheaper)
- EV/EBITDA (lower = cheaper)
- PEG (preferred when available)
- Fallback: EV/EBITDA ÷ Revenue Growth

**Formula:**

```
V_PE = neg(ForwardPE, 12, 45)
V_EV = neg(EV/EBITDA, 6, 30)
if PEG exists:
V_driver = neg(PEG, 0.5, 3.0)
else:
V_driver = neg(EV/EBITDA / RevenueGrowth, 0.4, 2.5)

Valuation = 0.5 * V_PE + 0.3 * V_EV + 0.2 * V_driver
```

PEG normalizes valuation by growth rate.  
If unavailable, growth-adjusted EV/EBITDA keeps comparisons fair.

---

### 4. Safety
Assesses the company’s financial resilience.

**Inputs:**
- Debt-to-Equity ratio  
- Current Ratio  

**Formula:**
Safety = 0.5 * [ neg(Debt/Equity, 0, 1) + pos(CurrentRatio, 1, 3) ]

Low leverage and healthy liquidity earn higher scores.

---

### 5. Stability
Measures **predictability of revenue** using the coefficient of variation (CV).  
Lower variation means steadier growth.

**Formula:**
Stability = neg(CV_RevenueGrowth, 0.3, 1.5)

Stable revenue → easier forecasting → less risk.

---

### 6. Moat
Uses the same logic as stability but applied to **gross margins** —  
if margins don’t fluctuate much, pricing power or cost advantage is likely.

**Formula:**
Moat = neg(CV_GrossMargin, 0.05, 0.25)


---

### 7. R&D Intensity
Encourages innovation without overspending.  
Too little → stagnation; too much → inefficiency.

**Formula:**
R&D Score = pos(R&D/Revenue%, 5, 22)


5–20% of revenue spent on R&D is generally healthy.

---

### 8. Investment Discipline
Evaluates how wisely the company reinvests operating cash flow.

**Formula:**
InvestmentScore = neg(CapEx/OCF%, 15, 60)


Below 15% = conservative,  
15–40% = balanced,  
>60% = aggressive (usually penalized).

---

## 🔀 Blending Recent and Historical Data

Each factor uses both recent and long-term data.  
To keep things responsive but not overreactive, scores are combined as:


Blended = α * Recent + (1 - α) * LongTerm

where α typically ≈ 0.6–0.7.

This makes the model responsive to changes without ignoring history.

---

## 🧮 Final Composite Score

All sub-scores are combined into one master score, weighted by importance:

```
for importance_factors = {
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

BuyScore =
0.30 * Growth +
0.30 * Profitability +
0.15 * Valuation +
0.12 * Safety +
0.13 * Stability +
0.00 * Moat +
0.00 * R&D Score +
0.00 * Investment Score

BuyScore = 100 * BuyScore


## future improvements

- Add sector-relative scoring 
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
