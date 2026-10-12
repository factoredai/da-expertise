"""
RW-3: B2B/B2C Customer Detection from Ticket Signals
Business problem: Segment customers into B2B/B2C from transaction patterns when no customer type flag exists.
Required columns: transaction_id, amount, quantity, sku_id, category, datetime.
Output: Transaction-level segment labels (B2B/B2C), bimodality test, GMM model.
"""
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from sklearn.mixture import GaussianMixture

# Transaction-level features
txn = df.groupby('transaction_id').agg(
    total=('amount', 'sum'),
    items=('quantity', 'sum'),
    unique_skus=('sku_id', 'nunique'),
    categories=('category', 'nunique'),
    hour=('datetime', lambda x: x.iloc[0].hour),
    dow=('datetime', lambda x: x.iloc[0].dayofweek),
    max_qty_single_sku=('quantity', 'max'),
)

# The bimodal test: ticket value distribution should show two modes
# Log-transform to handle right-skew; clip at 1 to avoid log(0)
hist_vals, bin_edges = np.histogram(np.log10(txn['total'].clip(lower=1)), bins=100)
# height threshold at 0.5% of total transactions; distance=10 to separate real modes
peaks, properties = find_peaks(hist_vals, height=len(txn)*0.005, distance=10)

# Gaussian Mixture Model for data-derived threshold
# log1p transform normalizes skewed features for GMM
features = txn[['total', 'items', 'unique_skus', 'max_qty_single_sku']].apply(np.log1p)
# n_components=2 for B2B/B2C binary split; random_state for reproducibility
gmm = GaussianMixture(n_components=2, random_state=42)
txn['segment_label'] = gmm.fit_predict(features)

# Assign labels based on cluster means (higher-value cluster = B2B)
cluster_means = txn.groupby('segment_label')['total'].mean()
b2b_label = cluster_means.idxmax()
txn['segment'] = txn['segment_label'].map({b2b_label: 'B2B', 1 - b2b_label: 'B2C'})
