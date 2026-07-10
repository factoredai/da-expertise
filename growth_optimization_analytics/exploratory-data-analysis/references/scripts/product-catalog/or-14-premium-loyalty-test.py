"""
OR-14: Premium and Specialty Product Loyalty Test
Business problem: Test if premium variants generate higher repeat purchasing.
Required columns: product_id, product_name, reorder_rate, total_orders, department.
Output: Overall and per-category comparison, effect sizes.
"""
import pandas as pd
import numpy as np
from scipy.stats import mannwhitneyu

product_stats['is_premium'] = product_stats['product_name'].str.contains(
    'Organic|Artisan|Free.?Range|Premium|Natural|Craft', case=False, na=False, regex=True)
qualified = product_stats[product_stats['total_orders'] >= min_orders]

premium = qualified[qualified['is_premium']]['reorder_rate']
conventional = qualified[~qualified['is_premium']]['reorder_rate']
stat, p = mannwhitneyu(premium, conventional, alternative='two-sided')
n1, n2 = len(premium), len(conventional)
r_rb = 1 - (2 * stat) / (n1 * n2)

for dept in qualified['department'].unique():
    d = qualified[qualified['department'] == dept]
    prem = d[d['is_premium']]['reorder_rate']
    conv = d[~d['is_premium']]['reorder_rate']
    if len(prem) >= 10 and len(conv) >= 10:
        s, p = mannwhitneyu(prem, conv)
        print(f"{dept}: premium={prem.median():.3f}, conv={conv.median():.3f}, p={p:.4f}")
