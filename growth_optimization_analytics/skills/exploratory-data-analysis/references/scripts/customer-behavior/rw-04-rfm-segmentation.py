"""
RW-4: RFM Segmentation
Business problem: Identify most valuable, at-risk, and reactivation-target customers.
Required columns: customer_id, date, amount (or quantity), transaction_id. Optional: cpi_index, segment.
Output: RFM scores, segment labels, churn risk ratios.
"""
import pandas as pd
import numpy as np

# CRITICAL: Run within detected segments, not across full population
b2b = df[df['segment'] == 'B2B'].copy()

snapshot_date = b2b['date'].max() + pd.Timedelta(days=1)
rfm = b2b.groupby('customer_id').agg(
    recency=('date', lambda x: (snapshot_date - x.max()).days),
    frequency=('transaction_id', 'nunique'),
    monetary=('amount', 'sum'),
)

# Fallback: unit volume is inflation-immune when deflator unavailable
rfm['monetary_units'] = b2b.groupby('customer_id')['quantity'].sum()

# Score using quintiles (data-derived, not fixed thresholds)
for col in ['recency', 'frequency', 'monetary']:
    ascending = (col == 'recency')
    rfm[f'{col}_score'] = pd.qcut(rfm[col], q=5, labels=[5,4,3,2,1] if ascending else [1,2,3,4,5])

# Churn early warning
customer_dates = b2b.sort_values('date').groupby('customer_id')['date']
ipi = customer_dates.diff().dt.days.groupby(b2b['customer_id']).median()
last_purchase = customer_dates.max()
days_since = (snapshot_date - last_purchase).dt.days
churn_risk = days_since / ipi  # ratio > 2.0 = elevated risk
