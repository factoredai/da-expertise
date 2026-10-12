"""
RW-12: Supplier Scorecard and Negotiation Analytics
Business problem: Score suppliers on reliability, margin, and terms.
Required columns: supplier, ordered_qty, received_qty, lead_time_days, margin_pct, total_cost, order_id.
Output: Composite supplier score, negotiation leverage data.
"""
import pandas as pd
import numpy as np

supplier_score = purchases.groupby('supplier').agg(
    fill_rate=('received_qty', lambda x: (x / purchases.loc[x.index, 'ordered_qty']).mean()),
    avg_lead_time=('lead_time_days', 'mean'),
    lead_time_cv=('lead_time_days', lambda x: x.std() / x.mean() if x.mean() > 0 else np.inf),
    avg_margin=('margin_pct', 'median'),
    total_spend=('total_cost', 'sum'),
    n_orders=('order_id', 'nunique'),
)
