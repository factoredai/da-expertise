"""
OR-11: Universal Staple Identification with Segment Urgency Weighting
Business problem: Find must-not-stockout products with segment-specific urgency.
Required columns: product_id, unique_users in product_stats; segment_product_stats with segment, product_id, total_orders, n_reordered.
Output: Staple products, segment reorder rates, urgency multipliers.
"""
import pandas as pd
import numpy as np
from scipy.stats import kruskal

breadth = product_stats[['product_id', 'unique_users']].copy()
breadth['user_pct'] = breadth['unique_users'] / total_users * 100
b_sorted = breadth.sort_values('user_pct', ascending=False).reset_index(drop=True)
grad2 = np.gradient(np.gradient(b_sorted['user_pct'].values))
inflection = np.argmax(np.abs(grad2[10:]) > np.std(grad2) * 2) + 10
threshold = b_sorted.loc[inflection, 'user_pct']
staples = breadth[breadth['user_pct'] >= threshold]

seg_rr = segment_product_stats[segment_product_stats['product_id'].isin(staples['product_id'])]
seg_rr['rr'] = seg_rr['n_reordered'] / seg_rr['total_orders']

for pid in staples['product_id']:
    prod_data = seg_rr[seg_rr['product_id'] == pid]
    if len(prod_data) >= 3:
        groups = [g['rr'].values for _, g in prod_data.groupby('segment')]
        stat, p = kruskal(*groups)
        rr_range = prod_data['rr'].max() - prod_data['rr'].min()
        print(f"Product {pid}: range={rr_range:.2f}, p={p:.4f}")
