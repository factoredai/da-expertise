"""
RW-7: Demand Pattern Analysis
Business problem: Identify day/hour demand patterns for staffing and replenishment.
Required columns: transaction_id, datetime, quantity, amount. Optional: category, segment, cashier_id.
Output: DOW index, hour patterns, staffing recommendations.
"""
import pandas as pd
import numpy as np

df['dow'] = df['datetime'].dt.dayofweek
df['hour'] = df['datetime'].dt.hour

dow_pattern = df.groupby('dow').agg(
    transactions=('transaction_id', 'nunique'),
    total_units=('quantity', 'sum'),
    avg_ticket=('amount', 'mean'),
).reset_index()
dow_pattern['txn_index'] = dow_pattern['transactions'] / dow_pattern['transactions'].mean()

hour_pattern = df.groupby(['hour', df['dow'].isin([5,6]).map({True:'Weekend', False:'Weekday'})]).agg(
    transactions=('transaction_id', 'nunique')).reset_index()

# Staffing: derive throughput from data, not fixed benchmark
cashier_hourly_txn = df.groupby(['hour', 'cashier_id'])['transaction_id'].nunique()
avg_txn_per_cashier_per_hour = cashier_hourly_txn.median()
hourly_txn = df.groupby('hour')['transaction_id'].nunique()
min_cashiers = np.ceil(hourly_txn / avg_txn_per_cashier_per_hour)
