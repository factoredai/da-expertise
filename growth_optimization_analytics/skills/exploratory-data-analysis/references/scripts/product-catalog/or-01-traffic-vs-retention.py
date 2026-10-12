"""
OR-1: Traffic Engine vs Retention Engine Classification
Business problem: Determine if high-volume products are the same as high-reorder products.
Required columns: product_id, total_orders, reorder_rate, unique_users in product_stats.
Output: Two ranked lists (Traffic Engines, Retention Engines), Spearman correlation with bootstrap CI.
"""
import pandas as pd
import numpy as np
from scipy.stats import spearmanr

ps = product_stats.copy()
ps_sorted = ps.sort_values('total_orders')
ps_sorted['rr_rolling'] = ps_sorted['reorder_rate'].rolling(50, center=True).mean()
# Visual inspection or second-derivative analysis to find stabilization point
min_orders = ...  # data-derived from stabilization point
qualified = ps[ps['total_orders'] >= min_orders].copy()

qualified['vol_rank'] = qualified['total_orders'].rank(ascending=False)
qualified['rr_rank'] = qualified['reorder_rate'].rank(ascending=False)
rho, p = spearmanr(qualified['vol_rank'], qualified['rr_rank'])

# Bootstrap significance test
n_boot = 1000
boot_rhos = []
for _ in range(n_boot):
    sample = qualified.sample(frac=1, replace=True)
    r, _ = spearmanr(sample['vol_rank'], sample['rr_rank'])
    boot_rhos.append(r)
ci_lower, ci_upper = np.percentile(boot_rhos, [2.5, 97.5])

# Measure overlap at Pareto elbow
cum_share = ps.sort_values('total_orders', ascending=False)['total_orders'].cumsum() / ps['total_orders'].sum()
elbow_n = (cum_share < 0.80).sum()
top_vol = set(qualified.nlargest(elbow_n, 'total_orders')['product_id'])
top_rr = set(qualified.nlargest(elbow_n, 'reorder_rate')['product_id'])
overlap_pct = len(top_vol & top_rr) / elbow_n * 100
