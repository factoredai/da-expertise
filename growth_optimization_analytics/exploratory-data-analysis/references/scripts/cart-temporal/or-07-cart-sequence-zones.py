"""
OR-7: Cart Sequence Behavioral Zone Profiling
Business problem: Test if cart addition order carries behavioral signal.
Required columns: order_id, product_id, add_to_cart_order, reordered, department.
Output: Reorder rate by position, zone boundaries, department distribution per zone.
"""
import pandas as pd
import numpy as np
from scipy.stats import spearmanr

pos_rr = order_products.groupby('add_to_cart_order').agg(
    n_reordered=('reordered', 'sum'), n_total=('reordered', 'count'))
pos_rr['reorder_rate'] = pos_rr['n_reordered'] / pos_rr['n_total']
pos_rr['ci_width'] = 1.96 * np.sqrt(pos_rr['reorder_rate'] * (1 - pos_rr['reorder_rate']) / pos_rr['n_total'])
stable = pos_rr[pos_rr['ci_width'] < pos_rr['ci_width'].quantile(0.75)]

rho, p = spearmanr(stable.index, stable['reorder_rate'])
rr_values = stable['reorder_rate'].values
second_deriv = np.gradient(np.gradient(rr_values))
inflections = np.where(np.abs(second_deriv) > np.std(second_deriv))[0]
