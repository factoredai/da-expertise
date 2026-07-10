"""
OR-18: Aisle-Level Co-occurrence Affinity Map
Business problem: Find which aisles appear together in baskets.
Required columns: order_id, product_id, aisle.
Output: Co-occurrence matrix with lift, top affinities.
"""
import pandas as pd
import numpy as np
from itertools import combinations

aisle_per_order = order_products.merge(
    products[['product_id', 'aisle']], on='product_id'
).groupby('order_id')['aisle'].apply(set)

co_occur = {}
for aisles in aisle_per_order:
    for a1, a2 in combinations(sorted(aisles), 2):
        co_occur[(a1, a2)] = co_occur.get((a1, a2), 0) + 1

aisle_prob = order_products.merge(products[['product_id', 'aisle']], on='product_id').groupby('aisle')['order_id'].nunique() / total_orders

co_df = pd.DataFrame([
    {'aisle_1': k[0], 'aisle_2': k[1], 'co_count': v,
     'lift': v / total_orders / (aisle_prob[k[0]] * aisle_prob[k[1]])}
    for k, v in co_occur.items()
])
lift_threshold = co_df['lift'].quantile(0.90)
strong_affinities = co_df[co_df['lift'] > lift_threshold]
