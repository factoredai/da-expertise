"""
OR-16: Core Catalog Overlap Across Segments
Business problem: Measure shared vs segment-exclusive core catalog.
Required columns: segment, product_id, total_orders in seg_product_stats.
Output: Universal core set, segment-exclusive counts, overlap percentage.
"""
import pandas as pd

core_sets = {}
for seg in segments['segment'].unique():
    seg_data = seg_product_stats[seg_product_stats['segment'] == seg].sort_values('total_orders', ascending=False)
    cum_share = seg_data['total_orders'].cumsum() / seg_data['total_orders'].sum()
    elbow = (cum_share <= 0.50).sum()
    core_sets[seg] = set(seg_data.head(elbow)['product_id'])

universal = set.intersection(*core_sets.values())
any_core = set.union(*core_sets.values())
overlap_pct = len(universal) / len(any_core) * 100

for seg in core_sets:
    exclusive = core_sets[seg] - set.union(*(core_sets[s] for s in core_sets if s != seg))
    print(f"{seg}: {len(exclusive)} exclusive core products")
