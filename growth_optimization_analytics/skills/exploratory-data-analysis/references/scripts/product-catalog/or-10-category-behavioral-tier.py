"""
OR-10: Category Behavioral Tier Classification
Business problem: Classify categories by purchase logic using volume-weighted reorder rates.
Required columns: product_id, department, reorder_rate, total_orders in product_stats.
Output: Tier assignments, bootstrap null test, BIC-optimal tier count.
"""
import pandas as pd
import numpy as np
from sklearn.mixture import GaussianMixture

cat_rr = product_stats.groupby('department').apply(
    lambda g: np.average(g['reorder_rate'], weights=g['total_orders'])
).reset_index(name='weighted_rr')

n_boot = 1000
observed_range = cat_rr['weighted_rr'].max() - cat_rr['weighted_rr'].min()
null_ranges = []
for _ in range(n_boot):
    shuffled = product_stats.copy()
    shuffled['department'] = np.random.permutation(shuffled['department'].values)
    null_rr = shuffled.groupby('department').apply(
        lambda g: np.average(g['reorder_rate'], weights=g['total_orders']))
    null_ranges.append(null_rr.max() - null_rr.min())
p_value = np.mean(np.array(null_ranges) >= observed_range)

for n_tiers in [2, 3, 4]:
    gmm = GaussianMixture(n_components=n_tiers, random_state=42)
    gmm.fit(cat_rr[['weighted_rr']])
    print(f"{n_tiers} tiers: BIC={gmm.bic(cat_rr[['weighted_rr']]):.1f}")
