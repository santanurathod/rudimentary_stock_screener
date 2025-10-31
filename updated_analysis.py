import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as dt
import plotly.express as px

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

# Load the file (change the path if needed)
# file_path = 'Eicher_Motors.xlsx'
file_path= 'Hindalco_Inds.xlsx'

# Load ONLY the "Data Sheet"
df = pd.read_excel(file_path, sheet_name="Data Sheet", engine="openpyxl")

# Drop empty columns/rows that may interfere
df = df.dropna(how='all').dropna(axis=1, how='all')

df.reset_index(drop=True, inplace=True)
# Find the row indices for section headers
pnl_idx = df[df['COMPANY NAME'] == 'PROFIT & LOSS'].index[0]
q_idx = df[df['COMPANY NAME'] == 'Quarters'].index[0]
bs_idx = df[df['COMPANY NAME'] == 'BALANCE SHEET'].index[0]
cf_idx = df[df['COMPANY NAME'] == 'CASH FLOW:'].index[0]

# Extract sub-DataFrames (excluding the header rows themselves)
df_pnl = df.iloc[pnl_idx+1 : q_idx].reset_index(drop=True)
df_q = df.iloc[q_idx+1 : bs_idx].reset_index(drop=True)
df_bs = df.iloc[bs_idx+1 : cf_idx].reset_index(drop=True)
df_cf = df.iloc[cf_idx+1 :].reset_index(drop=True)

# Set column headers
df_pnl.columns= df_pnl[df_pnl['COMPANY NAME']=='Report Date'].loc[0].to_list()
df_pnl.columns.values[0]= 'Variable'
df_pnl= df_pnl.drop(df_pnl.index[0])

df_q.columns= df_q[df_q['COMPANY NAME']=='Report Date'].loc[0].to_list()
df_q.columns.values[0]= 'Variable'
df_q= df_q.drop(df_q.index[0])

df_bs.columns= df_bs[df_bs['COMPANY NAME']=='Report Date'].loc[0].to_list()
df_bs.columns.values[0]= 'Variable'
df_bs= df_bs.drop(df_bs.index[0])

df_cf.columns= df_cf[df_cf['COMPANY NAME']=='Report Date'].loc[0].to_list()
df_cf.columns.values[0]= 'Variable'
df_cf= df_cf.drop(df_cf.index[0])

# Clean up: drop fully empty columns/rows and reset index
for df in (df_pnl, df_bs, df_cf, df_q):
    df.dropna(how='all', axis=1, inplace=True)
    df.dropna(how='all', inplace=True)
    df.reset_index(drop=True, inplace=True)

# Rename first column to "Variable"
for df in (df_pnl, df_bs, df_cf, df_q):
    df.columns.values[0] = "Variable"

# Convert column names to datetime wherever possible
def convert_columns_to_datetime(df):
    new_cols = []
    for col in df.columns:
        try:
            new_col = pd.to_datetime(col)
        except:
            new_col = col
        new_cols.append(new_col)
    df.columns = new_cols

convert_columns_to_datetime(df_pnl)
convert_columns_to_datetime(df_bs)
convert_columns_to_datetime(df_cf)
convert_columns_to_datetime(df_q)

# Normalize the 'Variable' column (strip whitespace and lowercase)
for df in (df_pnl, df_bs, df_cf, df_q):
    df["Variable"] = df["Variable"].astype(str).str.strip().str.lower()

# ============= ANNUAL ANALYSIS =============

# Identify all datetime columns (the last 9 fiscal years)
years = [col for col in df_pnl.columns if isinstance(col, pd.Timestamp)]
# e.g., [Timestamp('2016-03-31'), ..., Timestamp('2025-03-31')]

# Define helper to fetch a row's values across all 9 years
def get_row_values(df, var_name):
    var_name_clean = var_name.lower().strip()
    row = df[df["Variable"] == var_name_clean]
    if row.empty:
        raise ValueError(f"Variable '{var_name}' not found")
    return row.iloc[0][years].astype(float).values

# Extract series for the last 9 years (sales, net profit, price)
sales = get_row_values(df_pnl, "sales")
net_profit = get_row_values(df_pnl, "net profit")
stock_price = get_row_values(df_cf, "price:")

# Compute EBITDA for last 9 years = PBT + Depreciation + Interest
ebitda = (
    get_row_values(df_pnl, "profit before tax")
    + get_row_values(df_pnl, "depreciation")
    + get_row_values(df_pnl, "interest")
)

# Dividend Amount (crores) – last 9 years
div_amt = get_row_values(df_pnl, "dividend amount")

# Number of Equity Shares (absolute count) for last 9 years
num_shares = df_bs[df_bs["Variable"] == "no. of equity shares"][years].astype(float).values.flatten()

# Market Cap = price * num_shares
market_cap = stock_price * num_shares

# Total Equity (crores) = Equity Share Capital + Reserves
equity_cap = get_row_values(df_bs, "equity share capital")
reserves = get_row_values(df_bs, "reserves")
total_equity = equity_cap + reserves  # in crores

# Book Value per Share (Rs) = (Total Equity crores * 1e7) / number of shares
bvps = (total_equity * 1e7) / num_shares

# P/E Ratio = Price / (Net Profit per share)
# Net Profit per share (Rs) = (Net profit crores * 1e7) / number of shares
eps = (net_profit * 1e7) / num_shares
pe_ratio = stock_price / eps

# P/B Ratio = Price / BVPS
pb_ratio = stock_price / bvps

# ROE (%) = (Net Profit crores / Total Equity crores) * 100
roe = (net_profit / total_equity) * 100

# ROCE (%) = [EBITDA crores / (Total Equity + Borrowings) crores] * 100
borrowings = get_row_values(df_bs, "borrowings")
roce = (ebitda / (total_equity + borrowings)) * 100

# Cash Flow (Net Cash Flow) last 9 years
cash_flow = get_row_values(df_cf, "net cash flow")

# Net Assets = Total Equity (crores) for last 9 years
net_assets = total_equity

# Dividend Yield (%) = [Dividend per share / Price] * 100
# Dividend per share (Rs) = (Dividend Amount crores * 1e7) / number of shares
dps = (div_amt * 1e7) / num_shares
div_yield = (dps / stock_price) * 100

# Compute Stock Price CAGR over 8 periods (2016→2025)
def compute_cagr(start_val, end_val, periods):
    return (end_val / start_val) ** (1 / periods) - 1

stock_cagr = compute_cagr(stock_price[0], stock_price[-1], len(stock_price) - 1)

# Compute Sales % YoY increase for 8 intervals (2017 vs 2016, ..., 2025 vs 2024)
sales_pct_yoy = [
    (sales[i] - sales[i - 1]) / sales[i - 1] * 100 if sales[i - 1] != 0 else np.nan
    for i in range(1, len(sales))
]

# Compute Net Profit % YoY increase similarly
net_profit_pct_yoy = [
    (net_profit[i] - net_profit[i - 1]) / net_profit[i - 1] * 100 if net_profit[i - 1] != 0 else np.nan
    for i in range(1, len(net_profit))
]

# Prepare a DataFrame or print results
results = pd.DataFrame({
    "Year": [col.year for col in years],
    "Sales": sales,
    "Sales YoY %": [np.nan] + [round(pct, 2) for pct in sales_pct_yoy],
    "Net Profit": net_profit,
    "Net Profit YoY %": [np.nan] + [round(pct, 2) for pct in net_profit_pct_yoy],
    "Stock Price": stock_price,
    "Market Cap": market_cap,
    "EBITDA": ebitda,
    "Dividend Amt": div_amt,
    "Book Value/Share": bvps,
    "P/E": pe_ratio,
    "eps": eps,
    "P/B": pb_ratio,
    "ROE (%)": roe,
    "ROCE (%)": roce,
    "Net Assets": net_assets,
    "Cash Flow": cash_flow,
    "Div Yield (%)": div_yield
})

print("=== ANNUAL ANALYSIS ===")
print(results)
print(f"\nStock Price CAGR (2016→2025): {round(stock_cagr * 100, 2)}%")

# ============= QUARTERLY ANALYSIS =============

# Extract quarterly data
quarters = [col for col in df_q.columns if isinstance(col, pd.Timestamp)]

# Helper function for quarterly data
def get_quarterly_values(df, var_name):
    var_name_clean = var_name.lower().strip()
    row = df[df["Variable"] == var_name_clean]
    if row.empty:
        raise ValueError(f"Quarterly variable '{var_name}' not found")
    return row.iloc[0][quarters].astype(float).values

# Extract quarterly metrics
q_sales = get_quarterly_values(df_q, "sales")
q_expenses = get_quarterly_values(df_q, "expenses")
q_other_income = get_quarterly_values(df_q, "other income")
q_depreciation = get_quarterly_values(df_q, "depreciation")
q_interest = get_quarterly_values(df_q, "interest")
q_pbt = get_quarterly_values(df_q, "profit before tax")
q_tax = get_quarterly_values(df_q, "tax")
q_net_profit = get_quarterly_values(df_q, "net profit")
q_operating_profit = get_quarterly_values(df_q, "operating profit")

# Calculate quarterly growth rates (QoQ)
def calculate_qoq_growth(values):
    return [(values[i] - values[i-1]) / values[i-1] * 100 if values[i-1] != 0 else np.nan 
            for i in range(1, len(values))]

q_sales_qoq = calculate_qoq_growth(q_sales)
q_net_profit_qoq = calculate_qoq_growth(q_net_profit)
q_operating_profit_qoq = calculate_qoq_growth(q_operating_profit)

# Calculate quarterly margins
q_operating_margin = (q_operating_profit / q_sales) * 100
q_net_margin = (q_net_profit / q_sales) * 100
q_tax_rate = (q_tax / q_pbt) * 100

# Calculate quarterly EBITDA
q_ebitda = q_pbt + q_depreciation + q_interest
q_ebitda_margin = (q_ebitda / q_sales) * 100

# Prepare quarterly results DataFrame
quarterly_results = pd.DataFrame({
    "Quarter": [f"{col.year}Q{((col.month-1)//3)+1}" for col in quarters],
    "Sales": q_sales,
    "Sales QoQ %": [np.nan] + [round(pct, 2) for pct in q_sales_qoq],
    "Net Profit": q_net_profit,
    "Net Profit QoQ %": [np.nan] + [round(pct, 2) for pct in q_net_profit_qoq],
    "Operating Profit": q_operating_profit,
    "Op Profit QoQ %": [np.nan] + [round(pct, 2) for pct in q_operating_profit_qoq],
    "EBITDA": q_ebitda,
    "Operating Margin %": np.round(q_operating_margin, 2),
    "Net Margin %": np.round(q_net_margin, 2),
    "EBITDA Margin %": np.round(q_ebitda_margin, 2),
    "Tax Rate %": np.round(q_tax_rate, 2),
    "Expenses": q_expenses,
    "Other Income": q_other_income
})

print("\n=== QUARTERLY ANALYSIS ===")
print(quarterly_results)

# Calculate yearly quarters comparison (YoY for same quarters)
# Find matching quarters across years for YoY comparison
yoy_comparisons = []
for i, quarter in enumerate(quarters):
    # Find the same quarter in previous year
    prev_year_quarter = quarter.replace(year=quarter.year-1)
    if prev_year_quarter in quarters:
        prev_idx = quarters.index(prev_year_quarter)
        sales_yoy = (q_sales[i] - q_sales[prev_idx]) / q_sales[prev_idx] * 100 if q_sales[prev_idx] != 0 else np.nan
        profit_yoy = (q_net_profit[i] - q_net_profit[prev_idx]) / q_net_profit[prev_idx] * 100 if q_net_profit[prev_idx] != 0 else np.nan
        yoy_comparisons.append({
            "Quarter": f"{quarter.year}Q{((quarter.month-1)//3)+1}",
            "Sales YoY %": round(sales_yoy, 2) if not np.isnan(sales_yoy) else np.nan,
            "Net Profit YoY %": round(profit_yoy, 2) if not np.isnan(profit_yoy) else np.nan
        })

if yoy_comparisons:
    yoy_df = pd.DataFrame(yoy_comparisons)
    print("\n=== QUARTERLY YoY COMPARISON ===")
    print(yoy_df)

# Key quarterly insights
print("\n=== QUARTERLY INSIGHTS ===")
print(f"Latest Quarter Sales: {q_sales[-1]:.0f} Crores")
print(f"Latest Quarter Net Profit: {q_net_profit[-1]:.0f} Crores")
print(f"Latest Quarter Operating Margin: {q_operating_margin[-1]:.2f}%")
print(f"Latest Quarter Net Margin: {q_net_margin[-1]:.2f}%")
print(f"Average Quarterly Sales (Last 4Q): {np.mean(q_sales[-4:]):.0f} Crores")
print(f"Average Quarterly Net Profit (Last 4Q): {np.mean(q_net_profit[-4:]):.0f} Crores")

# Quarterly trend analysis
recent_quarters = 4  # Last 4 quarters
if len(q_sales) >= recent_quarters:
    recent_sales_trend = np.polyfit(range(recent_quarters), q_sales[-recent_quarters:], 1)[0]
    recent_profit_trend = np.polyfit(range(recent_quarters), q_net_profit[-recent_quarters:], 1)[0]
    
    print(f"\nQuarterly Trends (Last {recent_quarters} quarters):")
    print(f"Sales Trend: {'Increasing' if recent_sales_trend > 0 else 'Decreasing'} ({recent_sales_trend:.0f} Crores/quarter)")
    print(f"Profit Trend: {'Increasing' if recent_profit_trend > 0 else 'Decreasing'} ({recent_profit_trend:.0f} Crores/quarter)")

# Additional quarterly metrics comparison
print("\n=== QUARTERLY VS ANNUAL COMPARISON ===")
print(f"Latest annual sales (FY{years[-1].year}): {sales[-1]:.0f} Crores")
print(f"Latest 4 quarters total sales: {sum(q_sales[-4:]):.0f} Crores")
print(f"Latest annual net profit (FY{years[-1].year}): {net_profit[-1]:.0f} Crores")
print(f"Latest 4 quarters total net profit: {sum(q_net_profit[-4:]):.0f} Crores")

# Show quarterly seasonality patterns
print("\n=== QUARTERLY SEASONALITY ===")
q_by_season = {}
for i, quarter in enumerate(quarters):
    season = f"Q{((quarter.month-1)//3)+1}"
    if season not in q_by_season:
        q_by_season[season] = {"sales": [], "profit": []}
    q_by_season[season]["sales"].append(q_sales[i])
    q_by_season[season]["profit"].append(q_net_profit[i])

for season in ["Q1", "Q2", "Q3", "Q4"]:
    if season in q_by_season:
        avg_sales = np.mean(q_by_season[season]["sales"])
        avg_profit = np.mean(q_by_season[season]["profit"])
        print(f"{season} Average - Sales: {avg_sales:.0f} Crores, Net Profit: {avg_profit:.0f} Crores")

print("\n=== ANALYSIS COMPLETE ===") 