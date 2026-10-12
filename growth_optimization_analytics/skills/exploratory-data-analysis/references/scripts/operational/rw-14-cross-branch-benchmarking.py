"""
RW-14: Cross-Branch Benchmarking
Business problem: Compare branches controlling for market differences.
Required columns: branch, category, amount, transaction_id.
Output: Category-adjusted performance ratios per branch.
"""
import pandas as pd

branch_cat = df.groupby(['branch', 'category']).agg(
    revenue=('amount', 'sum'), transactions=('transaction_id', 'nunique'))
chain_cat_share = df.groupby('category')['amount'].sum() / df['amount'].sum()
branch_total = df.groupby('branch')['amount'].sum()
# Actual/expected ratio: >1.0 = outperforming, <1.0 = underperforming
