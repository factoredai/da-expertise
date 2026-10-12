"""
OR-13: High-Volume Low-Loyalty Quadrant Analysis
Business problem: Find high-volume products with low repeat purchasing.
Required columns: product_id, total_orders, reorder_rate, department in product_stats.
Output: Four-quadrant classification, department concentration test.
"""
import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency

qualified = product_stats[product_stats['total_orders'] >= min_orders].copy()
vol_median = qualified['total_orders'].median()
rr_median = qualified['reorder_rate'].median()

qualified['quadrant'] = 'niche'
qualified.loc[(qualified['total_orders'] >= vol_median) & (qualified['reorder_rate'] >= rr_median), 'quadrant'] = 'core'
qualified.loc[(qualified['total_orders'] >= vol_median) & (qualified['reorder_rate'] < rr_median), 'quadrant'] = 'high_vol_low_loyalty'
qualified.loc[(qualified['total_orders'] < vol_median) & (qualified['reorder_rate'] >= rr_median), 'quadrant'] = 'hidden_gem'

ct = pd.crosstab(qualified['quadrant'], qualified['department'])
chi2, p, dof, expected = chi2_contingency(ct)
