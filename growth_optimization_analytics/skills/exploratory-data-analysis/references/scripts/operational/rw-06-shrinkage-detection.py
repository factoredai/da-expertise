"""
RW-6: Shrinkage and Ticket Anomaly Detection
Business problem: Find inventory loss from theft, scanning errors, or admin failures.
Required columns: transaction_id, cashier_id, datetime, sku_id, quantity, unit_price, amount.
Output: Anomalous transactions, flagged cashiers, department shrinkage.
"""
import pandas as pd
import numpy as np

txn = df.groupby('transaction_id').agg(
    total=('amount', 'sum'), items=('quantity', 'sum'),
    cashier=('cashier_id', 'first'),
    hour=('datetime', lambda x: x.iloc[0].hour))
txn['value_per_item'] = txn['total'] / txn['items']

# Per-cashier z-scores (not global)
cashier_stats = txn.groupby('cashier')['value_per_item'].agg(['mean', 'std'])
txn = txn.merge(cashier_stats, left_on='cashier', right_index=True)
txn['z_score'] = (txn['value_per_item'] - txn['mean']) / txn['std']

# Data-derived threshold targeting 50-200 flags
target_flags = 100
anomaly_percentile = target_flags / len(txn) * 100
z_threshold = txn['z_score'].quantile(anomaly_percentile / 100)
anomalies = txn[txn['z_score'] < z_threshold]
