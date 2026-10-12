"""
OR-4: Customer Lifecycle Reorder Trajectory
Business problem: Find when habitual behavior locks in and identify segments that never reach habit threshold.
Required columns: order_id, user_id, order_number, reorder_pct (or reordered flag).
Output: Inflection order number, per-segment plateau test results.
"""
import pandas as pd
import numpy as np
from scipy.stats import linregress

# Step 1: Compute reorder rate by order number
order_rr = order_stats.groupby('order_number').agg(
    median_rr=('reorder_pct', 'median'),
    n_orders=('order_id', 'count')
)

# Drop order numbers with insufficient observations
# Derive threshold: where CI width stabilizes
order_rr['ci_width'] = 1.96 * order_stats.groupby('order_number')['reorder_pct'].std() / np.sqrt(order_rr['n_orders'])
# 75th percentile cutoff filters out noisy tail order numbers with few users
ci_stable = order_rr[order_rr['ci_width'] < order_rr['ci_width'].quantile(0.75)]

# Step 2: Find inflection point (second derivative)
rr_values = ci_stable['median_rr'].values
second_deriv = np.gradient(np.gradient(rr_values))
# Inflection = order number where second derivative is most negative (curve flattening fastest)
inflection_idx = np.argmin(second_deriv)
inflection_order = ci_stable.index[inflection_idx]

# Step 3: Decompose by segment
for seg in segments['segment'].unique():
    seg_users = segments[segments['segment'] == seg]['user_id']
    seg_orders = order_stats[order_stats['user_id'].isin(seg_users)]
    seg_rr = seg_orders.groupby('order_number')['reorder_pct'].median()

    # Test for plateau in post-inflection region
    # Require at least 5 data points for reliable regression
    post = seg_rr[seg_rr.index >= inflection_order]
    if len(post) >= 5:
        slope, _, _, p, _ = linregress(range(len(post)), post.values)
        # p > 0.10: slope not significantly different from zero = plateau
        if p > 0.10:
            print(f"Segment {seg}: PLATEAU detected — slope {slope:.4f}, p={p:.3f}")
