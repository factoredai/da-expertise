"""
OR-15: Temporal Basket Size Variation with Mandatory Segment Decomposition
Business problem: Does ordering time affect basket size enough for timing-based promotions?
Required columns: order_id, basket_size, order_dow, order_hour_of_day, user_id, segment.
Output: Population effect size, per-segment weekend/weekday premiums, concentration test.
"""
import pandas as pd
import numpy as np
from scipy.stats import kruskal

# Step 1: Population-level test
# Kruskal-Wallis chosen over ANOVA because basket sizes are typically right-skewed
dow_groups = [g['basket_size'].values for _, g in basket_stats.merge(
    orders[['order_id','order_dow']], on='order_id').groupby('order_dow')]
stat, p = kruskal(*dow_groups)

# Effect size (eta-squared approximation from Kruskal-Wallis)
# Eta-squared: proportion of variance explained by day-of-week
n = sum(len(g) for g in dow_groups)
k = len(dow_groups)
eta_sq = (stat - k + 1) / (n - k)

# Step 2: MANDATORY segment decomposition
# Population-level effects can be driven by a single segment — always decompose
seg_effects = {}
for seg in segments['segment'].unique():
    seg_bs = basket_stats[basket_stats['user_id'].isin(
        segments[segments['segment'] == seg]['user_id'])]
    seg_bs = seg_bs.merge(orders[['order_id','order_dow']], on='order_id')

    # Weekend defined as days 0,1 (Saturday, Sunday in Instacart encoding)
    weekend = seg_bs[seg_bs['order_dow'].isin([0, 1])]['basket_size']
    weekday = seg_bs[~seg_bs['order_dow'].isin([0, 1])]['basket_size']

    # Premium as percentage difference: positive = larger weekend baskets
    premium = (weekend.median() / weekday.median() - 1) * 100
    seg_effects[seg] = premium

# Step 3: Test concentration
# If one segment's effect is 3x another's, the population average is misleading
effect_range = max(seg_effects.values()) - min(seg_effects.values())
if max(abs(v) for v in seg_effects.values()) > 3 * min(abs(v) for v in seg_effects.values() if v != 0):
    print("WARNING: Population effect concentrates in one segment")
