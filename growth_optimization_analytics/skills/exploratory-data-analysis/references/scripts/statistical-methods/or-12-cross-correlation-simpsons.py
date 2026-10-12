"""
OR-12: Feature Cross-Correlation with Simpson's Paradox Detection
Business problem: Find counterintuitive relationships that reverse within segments.
Required columns: Entity-level behavioral features (numeric), segment labels.
Output: Cross-correlation matrix, unexpected signs, Simpson's Paradox detections.
"""
import pandas as pd
import numpy as np
from scipy.stats import spearmanr

features = user_summary[['total_orders', 'avg_basket_size', 'reorder_ratio',
                          'median_days_between', 'unique_products']].dropna()
corr_matrix = features.corr(method='spearman')

# Define expected sign directions per domain
expected_signs = {
    ('unique_products', 'reorder_ratio'): -1,
    ('avg_basket_size', 'total_orders'): +1,
}
for (col1, col2), expected in expected_signs.items():
    observed = corr_matrix.loc[col1, col2]
    if np.sign(observed) != expected:
        print(f"UNEXPECTED: {col1} × {col2} = {observed:.3f}")
        for seg in segments['segment'].unique():
            seg_users = segments[segments['segment'] == seg]['user_id']
            seg_feat = features[features.index.isin(seg_users)]
            seg_rho, seg_p = spearmanr(seg_feat[col1], seg_feat[col2])
            reversal = "REVERSAL" if np.sign(seg_rho) != np.sign(observed) else "consistent"
            print(f"  {seg}: rho={seg_rho:.3f} ({reversal})")
