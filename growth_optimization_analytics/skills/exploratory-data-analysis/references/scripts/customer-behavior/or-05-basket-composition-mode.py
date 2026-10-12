"""
OR-5: Basket Composition Mode Distribution
Business problem: Classify orders into reorder mode, discovery mode, or mixed.
Required columns: order_id, order_number, n_reordered, basket_size, user_id, segment.
Output: Mode distribution by segment, Cramer's V for segment differences.
"""
import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency

# Step 1: Compute reorder percentage per non-first order
# First orders excluded because they have no prior history to reorder from
order_comp = order_stats[order_stats['order_number'] > 1].copy()
order_comp['reorder_pct'] = order_comp['n_reordered'] / order_comp['basket_size']

# Step 2: Classify modes from distribution
# Three-way classification: pure habit (100% reorder), pure discovery (0%), and mixed
order_comp['mode'] = 'mixed'
order_comp.loc[order_comp['reorder_pct'] == 1.0, 'mode'] = 'pure_habit'
order_comp.loc[order_comp['reorder_pct'] == 0.0, 'mode'] = 'pure_discovery'

# Step 3: Segment decomposition
mode_by_seg = pd.crosstab(order_comp.merge(segments, on='user_id')['segment'],
                           order_comp.merge(segments, on='user_id')['mode'],
                           normalize='index')

# Chi-squared test for segment differences
ct = pd.crosstab(order_comp.merge(segments, on='user_id')['segment'],
                  order_comp.merge(segments, on='user_id')['mode'])
chi2, p, dof, expected = chi2_contingency(ct)
# Cramer's V: effect size for categorical association (0=none, 1=perfect)
cramers_v = np.sqrt(chi2 / (ct.sum().sum() * (min(ct.shape) - 1)))
