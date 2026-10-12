"""
OR-20: Segment-Conditional Recommendation Strategy Matrix
Business problem: Identify which metrics need segment-specific vs population-level strategies.
Required columns: user_id, basket_size, n_reordered, days_since_prior, segment.
Output: Strategy matrix with divergence ratios and SEGMENT-SPECIFIC/POPULATION-OK labels.
"""
import pandas as pd
import numpy as np

# Step 1: Define key metrics
# Each metric captures a different behavioral dimension
metrics = {
    'median_basket_size': lambda g: g['basket_size'].median(),
    'reorder_rate': lambda g: g['n_reordered'].sum() / g['basket_size'].sum(),
    'single_item_rate': lambda g: (g['basket_size'] == 1).mean(),
    'median_interval': lambda g: g['days_since_prior'].median(),
}

# Step 2: Compute per-segment and population
results = {}
for name, func in metrics.items():
    pop_val = func(full_data)
    seg_vals = {}
    for seg in segments['segment'].unique():
        seg_data = full_data[full_data['user_id'].isin(
            segments[segments['segment'] == seg]['user_id'])]
        seg_vals[seg] = func(seg_data)

    # Divergence ratio: max segment value / min segment value
    # Higher ratio = segments behave very differently on this metric
    ratio = max(seg_vals.values()) / min(seg_vals.values()) if min(seg_vals.values()) > 0 else np.inf
    results[name] = {'population': pop_val, 'segments': seg_vals,
                     'divergence_ratio': ratio}

# Derive the divergence threshold from the data:
# Use the median divergence ratio across all metrics as the boundary
# This avoids arbitrary fixed thresholds — the data determines what counts as "divergent"
ratios = [r['divergence_ratio'] for r in results.values()]
divergence_threshold = np.median(ratios)
for name, r in results.items():
    r['strategy'] = ('SEGMENT-SPECIFIC' if r['divergence_ratio'] > divergence_threshold
                     else 'POPULATION-OK')
