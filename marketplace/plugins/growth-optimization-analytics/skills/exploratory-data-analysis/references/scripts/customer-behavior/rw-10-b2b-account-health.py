"""
RW-10: B2B Account Health Scoring
Business problem: Identify healthy, deteriorating, and at-risk B2B accounts.
Required columns: customer_id, date, amount, quantity, category.
Output: Health score (0-1), Green/Yellow/Red classification.
"""
import pandas as pd
import numpy as np
from scipy.stats import linregress

snapshot_date = b2b['date'].max() + pd.Timedelta(days=1)
health = b2b.groupby('customer_id').agg(
    freq_slope=('date', lambda x: linregress(range(len(x.dt.to_period('M').unique())),
                x.groupby(x.dt.to_period('M')).count().values)[0]
               if len(x.dt.to_period('M').unique()) >= 3 else 0),
    breadth=('category', 'nunique'),
    recency=('date', lambda x: (snapshot_date - x.max()).days),
)
for col in health.columns:
    if col == 'recency':
        health[f'{col}_norm'] = 1 - health[col].rank(pct=True)
    else:
        health[f'{col}_norm'] = health[col].rank(pct=True)
health['score'] = health[[c for c in health.columns if c.endswith('_norm')]].mean(axis=1)
health['status'] = pd.cut(health['score'], bins=[0, 0.33, 0.67, 1.0],
                          labels=['Red', 'Yellow', 'Green'])
