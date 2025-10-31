# Investing in Equity: My Journey and Approach

Hi Everyone,

I've finally started investing the savings that I have after procrastinating a lot. I have mutual fund SIPs as well, but I want to learn the nitty-gritty of equity investing. So, I started by shortlisting a few (37) companies in several sectors by just eye-balling the metrics (P/E, EBITDA, Cash-flow, etc.) from [screener.in](http://screener.in).

However, to decide which one to actually select and how much, I scraped the `.xlsx` files of those 37 companies and wrote some code to get the metrics like:

| Year | Sales | Sales YoY % | Net Profit | Net Profit YoY % | Stock Price | Market Cap | EBITDA | Dividend Amt | Book Value/Share | P/E | eps | P/B | Debt/Equity | ROE (%) | ROCE (%) | Net Assets | Cash Flow | Div Yield (%) |
|------|-------|-------------|------------|------------------|-------------|------------|--------|--------------|------------------|-----|-----|-----|-------------|---------|----------|------------|-----------|---------------|
| 2016 | 25377.33 | NaN | 550.80 | NaN | 34.45 | 1.148542e+11 | 8600.76 | NaN | 22.399510 | 20.852251 | 1.652100 | 1.537980 | 7.060834 | 7.375607 | 14.287646 | 7467.86 | -147.85 | NaN |
| 2017 | 22615.51 | -10.88 | -6174.10 | -1220.93 | 39.90 | 1.538919e+11 | 2313.92 | NaN | 7.777048 | -2.492539 | -16.007772 | 5.130481 | 17.497356 | -205.833522 | 4.170433 | 2999.56 | -25.77 | NaN |
| 2018 | 20304.28 | -10.22 | -2102.95 | -65.94 | 23.70 | 9.140945e+10 | 6190.03 | NaN | 2.305792 | -4.346725 | -5.452381 | 10.278463 | 59.409679 | -236.464529 | 11.521878 | 889.33 | -19.39 | NaN |
| 2019 | 23884.18 | 17.63 | -984.40 | -53.19 | 48.20 | 1.859045e+11 | 7431.28 | NaN | 19.995883 | -18.885053 | -2.552283 | 2.410496 | 6.091537 | -12.764043 | 13.587511 | 7712.29 | -37.08 | NaN |
| 2020 | 26467.72 | 10.82 | -2274.77 | 131.08 | 27.75 | 1.070301e+11 | 6056.40 | NaN | 16.802029 | -4.705094 | -5.897864 | 1.651586 | 8.517749 | -35.102092 | 9.819194 | 6480.44 | 916.56 | NaN |
| 2021 | 26221.48 | -0.93 | 1269.98 | -155.83 | 85.05 | 3.280327e+11 | 10596.72 | NaN | 33.997401 | 25.829750 | 3.292715 | 2.501662 | 4.005210 | 9.685196 | 16.145840 | 13112.59 | -828.06 | NaN |
| 2022 | 27711.18 | 5.68 | 4911.58 | 286.74 | 185.10 | 7.139194e+11 | 13789.45 | NaN | 47.853726 | 14.535433 | 12.734399 | 3.868037 | 2.662690 | 26.611092 | 20.398030 | 18456.89 | 669.33 | NaN |
| 2023 | 38773.30 | 39.92 | 10726.64 | 118.39 | 191.60 | 7.389895e+11 | 14311.88 | NaN | 77.459510 | 6.889292 | 27.811278 | 2.473550 | 1.417526 | 35.904278 | 19.815635 | 29875.66 | -433.14 | NaN |
| 2024 | 50351.25 | 29.86 | 20828.79 | 94.18 | 533.80 | 2.058834e+12 | 28110.93 | NaN | 111.863399 | 9.884559 | 54.003422 | 4.771891 | 0.802307 | 48.276221 | 36.150613 | 43145.03 | 787.02 | NaN |
| 2025 | 56203.09 | 11.62 | 12938.77 | -37.88 | 509.30 | NaN | 24008.18 | NaN | NaN | NaN | NaN | NaN | NaN | 0.700921 | 22.962623 | 25.049759 | 56347.09 | -816.39 | NaN |

**NOTE:** The numbers I get above differ from screener.in slightly because I don't use the quarterly information but rather yearly.

Based on this table, I have my metric function:

```python
def buy_score(row, sector_pe=None, sector_pb=None):
    score = 0
    # Growth (multi-year average preferred)
    score += max(row['Sales YoY %'], 0) * 0.15
    score += max(row['Net Profit YoY %'], 0) * 0.15
    # Value (relative to sector if possible)
    score += (1 / row['P/E'] if row['P/E'] > 0 else 0) * 0.10
    score += (1 / row['P/B'] if row['P/B'] > 0 else 0) * 0.10
    # Profitability
    score += row['ROE (%)'] * 0.15
    score += row['ROCE (%)'] * 0.10
    # Cash flow
    score += (row['Cash Flow'] / abs(row['Net Profit'])) * 0.10 if row['Net Profit'] != 0 else 0
    # Leverage
    score -= (row['Debt/Equity'] * 0.10) if 'Debt/Equity' in row else 0
    # Dividend
    score += (row['Div Yield (%)'] * 0.05 if not np.isnan(row['Div Yield (%)']) else 0)
    return score
```

What do people think of this approach and the `buy_score` function? Does it make good sense? What else can I do? What approach do people here usually take, especially quantitatively, and is there any advice for me?

**P.S.** I finally ranked several companies based on the above, and then picked 15 based on where the amount of money invested was f(score). I picked some despite poor scores out of gut-feeling: Ather Energy and Zomato.