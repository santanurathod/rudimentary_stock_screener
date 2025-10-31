import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as dt
import plotly.express as px

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

# Load the file
file_path = 'Hindalco_Inds.xlsx'
df = pd.read_excel(file_path, sheet_name="Data Sheet", engine="openpyxl")
df = df.dropna(how='all').dropna(axis=1, how='all')

# Extract different sections
df.reset_index(drop=True, inplace=True)
pnl_idx = df[df['COMPANY NAME'] == 'PROFIT & LOSS'].index[0]
q_idx = df[df['COMPANY NAME'] == 'Quarters'].index[0]
bs_idx = df[df['COMPANY NAME'] == 'BALANCE SHEET'].index[0]
cf_idx = df[df['COMPANY NAME'] == 'CASH FLOW:'].index[0]

df_pnl = df.iloc[pnl_idx+1 : q_idx].reset_index(drop=True)
df_q = df.iloc[q_idx+1 : bs_idx].reset_index(drop=True)
df_bs = df.iloc[bs_idx+1 : cf_idx].reset_index(drop=True)
df_cf = df.iloc[cf_idx+1 :].reset_index(drop=True)

# Set up column headers for all dataframes
for dataframe, name in [(df_pnl, 'pnl'), (df_q, 'q'), (df_bs, 'bs'), (df_cf, 'cf')]:
    dataframe.columns = dataframe[dataframe['COMPANY NAME']=='Report Date'].loc[0].to_list()
    dataframe.columns.values[0] = 'Variable'
    dataframe.drop(dataframe.index[0], inplace=True)
    dataframe.reset_index(drop=True, inplace=True)

# Clean up DataFrames
for df_temp in [df_pnl, df_q, df_bs, df_cf]:
    df_temp.dropna(how='all', axis=1, inplace=True)
    df_temp.dropna(how='all', inplace=True)
    df_temp.reset_index(drop=True, inplace=True)

# Convert column names to datetime and normalize Variable column
def convert_columns_to_datetime(df):
    new_cols = []
    for col in df.columns:
        if col == 'Variable':
            new_cols.append(col)
        else:
            try:
                new_col = pd.to_datetime(col)
            except:
                new_col = col
            new_cols.append(new_col)
    df.columns = new_cols

for df_temp in [df_pnl, df_q, df_bs, df_cf]:
    convert_columns_to_datetime(df_temp)
    df_temp["Variable"] = df_temp["Variable"].astype(str).str.strip().str.lower()

print("Data loaded and processed successfully!")
print(f"Annual P&L shape: {df_pnl.shape}")
print(f"Quarterly data shape: {df_q.shape}")
print(f"Balance Sheet shape: {df_bs.shape}")
print(f"Cash Flow shape: {df_cf.shape}")

# Display quarterly data structure
print("\n" + "="*50)
print("QUARTERLY DATA STRUCTURE:")
print("="*50)
print(df_q.head())

print("\n" + "="*50)
print("QUARTERLY DATA COLUMNS:")
print("="*50)
quarterly_cols = [col for col in df_q.columns if isinstance(col, pd.Timestamp)]
print(f"Quarterly periods available: {len(quarterly_cols)}")
for col in quarterly_cols[:10]:  # Show first 10 quarters
    print(f"  {col}")

# Get annual years and quarterly periods
annual_years = [col for col in df_pnl.columns if isinstance(col, pd.Timestamp)]
quarterly_periods = [col for col in df_q.columns if isinstance(col, pd.Timestamp)]

print(f"\nAnnual years: {len(annual_years)} periods")
print(f"Quarterly periods: {len(quarterly_periods)} periods")

# Helper functions
def get_row_values(df, var_name, columns=None):
    """Get values for a variable across specified columns"""
    if columns is None:
        columns = [col for col in df.columns if isinstance(col, pd.Timestamp)]
    
    var_name_clean = var_name.lower().strip()
    row = df[df["Variable"] == var_name_clean]
    if row.empty:
        print(f"Warning: Variable '{var_name}' not found in dataframe")
        return np.array([0] * len(columns))
    
    values = row.iloc[0][columns]
    return pd.to_numeric(values, errors='coerce').fillna(0).values

def get_latest_quarters(df, var_name, num_quarters=4):
    """Get the most recent quarterly values for a variable"""
    quarterly_cols = [col for col in df.columns if isinstance(col, pd.Timestamp)]
    if len(quarterly_cols) == 0:
        return np.array([])
    
    # Sort columns by date and take the last num_quarters
    quarterly_cols_sorted = sorted(quarterly_cols)
    recent_quarters = quarterly_cols_sorted[-num_quarters:] if len(quarterly_cols_sorted) >= num_quarters else quarterly_cols_sorted
    
    return get_row_values(df, var_name, recent_quarters), recent_quarters

def calculate_ttm(quarterly_values):
    """Calculate Trailing Twelve Months (TTM) from quarterly data"""
    if len(quarterly_values) >= 4:
        return np.sum(quarterly_values[-4:])  # Sum last 4 quarters
    else:
        return np.sum(quarterly_values)  # Sum all available quarters

# Extract annual data
annual_sales = get_row_values(df_pnl, "sales", annual_years)
annual_net_profit = get_row_values(df_pnl, "net profit", annual_years)
annual_stock_price = get_row_values(df_cf, "price:", annual_years)

# Extract quarterly data for more recent and accurate calculations
quarterly_sales, q_sales_periods = get_latest_quarters(df_q, "sales", 8)  # Last 8 quarters
quarterly_net_profit, q_profit_periods = get_latest_quarters(df_q, "net profit", 8)

print(f"\nQuarterly sales (last 8 quarters): {quarterly_sales}")
print(f"Quarterly net profit (last 8 quarters): {quarterly_net_profit}")

# Calculate TTM (Trailing Twelve Months) values for more accurate recent metrics
ttm_sales = calculate_ttm(quarterly_sales)
ttm_net_profit = calculate_ttm(quarterly_net_profit)

print(f"\nTTM Sales: {ttm_sales:.2f}")
print(f"TTM Net Profit: {ttm_net_profit:.2f}")

# Get number of shares (use latest available)
num_shares_annual = get_row_values(df_bs, "no. of equity shares", annual_years)
latest_shares = num_shares_annual[-1] if len(num_shares_annual) > 0 else 0

print(f"Latest number of shares: {latest_shares}")

# Calculate more accurate EPS using TTM data
ttm_eps = (ttm_net_profit * 1e7) / latest_shares if latest_shares > 0 else 0
annual_eps_latest = (annual_net_profit[-1] * 1e7) / latest_shares if latest_shares > 0 and len(annual_net_profit) > 0 else 0

print(f"TTM EPS: {ttm_eps:.2f}")
print(f"Latest Annual EPS: {annual_eps_latest:.2f}")

# Get latest stock price
latest_stock_price = annual_stock_price[-1] if len(annual_stock_price) > 0 else 0

# Calculate more accurate P/E ratios
pe_ratio_ttm = latest_stock_price / ttm_eps if ttm_eps > 0 else np.inf
pe_ratio_annual = latest_stock_price / annual_eps_latest if annual_eps_latest > 0 else np.inf

print(f"\nCurrent Stock Price: {latest_stock_price}")
print(f"P/E Ratio (TTM): {pe_ratio_ttm:.2f}")
print(f"P/E Ratio (Annual): {pe_ratio_annual:.2f}")

# Calculate other enhanced metrics using quarterly data
# EBITDA calculation
annual_pbt = get_row_values(df_pnl, "profit before tax", annual_years)
annual_depreciation = get_row_values(df_pnl, "depreciation", annual_years)
annual_interest = get_row_values(df_pnl, "interest", annual_years)

quarterly_pbt, _ = get_latest_quarters(df_q, "profit before tax", 8)
quarterly_depreciation, _ = get_latest_quarters(df_q, "depreciation", 8)
quarterly_interest, _ = get_latest_quarters(df_q, "interest", 8)

ttm_ebitda = calculate_ttm(quarterly_pbt) + calculate_ttm(quarterly_depreciation) + calculate_ttm(quarterly_interest)
annual_ebitda = annual_pbt + annual_depreciation + annual_interest

print(f"\nTTM EBITDA: {ttm_ebitda:.2f}")
print(f"Latest Annual EBITDA: {annual_ebitda[-1]:.2f}")

# Other key metrics
equity_cap = get_row_values(df_bs, "equity share capital", annual_years)
reserves = get_row_values(df_bs, "reserves", annual_years)
total_equity = equity_cap + reserves
borrowings = get_row_values(df_bs, "borrowings", annual_years)

# Market Cap
market_cap = latest_stock_price * latest_shares

# Book Value per Share
latest_total_equity = total_equity[-1] if len(total_equity) > 0 else 0
bvps = (latest_total_equity * 1e7) / latest_shares if latest_shares > 0 else 0

# P/B Ratio
pb_ratio = latest_stock_price / bvps if bvps > 0 else np.inf

# ROE using TTM data
roe_ttm = (ttm_net_profit / latest_total_equity) * 100 if latest_total_equity > 0 else 0
roe_annual = (annual_net_profit[-1] / latest_total_equity) * 100 if latest_total_equity > 0 and len(annual_net_profit) > 0 else 0

# ROCE using TTM data
latest_borrowings = borrowings[-1] if len(borrowings) > 0 else 0
roce_ttm = (ttm_ebitda / (latest_total_equity + latest_borrowings)) * 100 if (latest_total_equity + latest_borrowings) > 0 else 0

# Create enhanced results DataFrame
enhanced_results = pd.DataFrame({
    'Metric': [
        'Current Stock Price',
        'Market Cap (Cr)',
        'TTM Sales (Cr)',
        'TTM Net Profit (Cr)',
        'TTM EPS (Rs)',
        'Annual EPS (Rs)',
        'P/E Ratio (TTM)',
        'P/E Ratio (Annual)',
        'TTM EBITDA (Cr)',
        'Book Value per Share (Rs)',
        'P/B Ratio',
        'ROE % (TTM)',
        'ROE % (Annual)',
        'ROCE % (TTM)',
        'Number of Shares',
        'Total Equity (Cr)'
    ],
    'Value': [
        f"{latest_stock_price:.2f}",
        f"{market_cap/1e7:.2f}",
        f"{ttm_sales:.2f}",
        f"{ttm_net_profit:.2f}",
        f"{ttm_eps:.2f}",
        f"{annual_eps_latest:.2f}",
        f"{pe_ratio_ttm:.2f}",
        f"{pe_ratio_annual:.2f}",
        f"{ttm_ebitda:.2f}",
        f"{bvps:.2f}",
        f"{pb_ratio:.2f}",
        f"{roe_ttm:.2f}%",
        f"{roe_annual:.2f}%",
        f"{roce_ttm:.2f}%",
        f"{latest_shares:.0f}",
        f"{latest_total_equity:.2f}"
    ]
})

print("\n" + "="*60)
print("ENHANCED FINANCIAL METRICS (Using Quarterly Data)")
print("="*60)
print(enhanced_results.to_string(index=False))

# Quarterly trend analysis
if len(quarterly_net_profit) >= 4:
    print("\n" + "="*50)
    print("QUARTERLY TREND ANALYSIS:")
    print("="*50)
    
    # Quarter-over-Quarter growth
    qoq_growth = []
    for i in range(1, len(quarterly_net_profit)):
        if quarterly_net_profit[i-1] != 0:
            growth = ((quarterly_net_profit[i] - quarterly_net_profit[i-1]) / quarterly_net_profit[i-1]) * 100
            qoq_growth.append(growth)
        else:
            qoq_growth.append(0)
    
    quarterly_trend = pd.DataFrame({
        'Quarter': [str(period)[:10] for period in q_profit_periods[-len(quarterly_net_profit):]],
        'Net Profit (Cr)': quarterly_net_profit,
        'QoQ Growth %': [0] + qoq_growth
    })
    
    print(quarterly_trend.to_string(index=False))

# Year-over-Year quarterly comparison
if len(quarterly_net_profit) >= 8:
    print("\n" + "="*50)
    print("YEAR-OVER-YEAR QUARTERLY COMPARISON:")
    print("="*50)
    
    yoy_comparison = []
    for i in range(4, len(quarterly_net_profit)):
        if quarterly_net_profit[i-4] != 0:
            yoy_growth = ((quarterly_net_profit[i] - quarterly_net_profit[i-4]) / quarterly_net_profit[i-4]) * 100
        else:
            yoy_growth = 0
        yoy_comparison.append({
            'Quarter': str(q_profit_periods[-len(quarterly_net_profit)+i])[:10],
            'Current': quarterly_net_profit[i],
            'Previous Year': quarterly_net_profit[i-4],
            'YoY Growth %': yoy_growth
        })
    
    yoy_df = pd.DataFrame(yoy_comparison)
    print(yoy_df.to_string(index=False))

print(f"\n{'='*60}")
print("ANALYSIS COMPLETE - Enhanced with Quarterly Data")
print("="*60)
print("Key advantages of this enhanced analysis:")
print("• Uses TTM (Trailing Twelve Months) data for more current metrics")
print("• More accurate EPS calculation using latest quarterly earnings")
print("• Updated P/E ratios reflecting recent performance")
print("• Quarterly trend analysis showing recent momentum")
print("• Year-over-year quarterly comparisons")