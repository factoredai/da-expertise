"""
RW-19: Payment Behavior Scoring for B2B Credit
Business problem: Identify credit risk and payment stress in B2B accounts.
Required columns: customer_id, days_to_payment, is_late, days_overdue, outstanding_amount.
Output: Payment score per customer, red flags.
"""
import pandas as pd
import numpy as np
from scipy.stats import linregress

payment_score = receivables.groupby('customer_id').agg(
    avg_days_to_pay=('days_to_payment', 'mean'),
    payment_trend=('days_to_payment', lambda x: linregress(range(len(x)), x.values)[0]
                   if len(x) >= 3 else 0),
    pct_late=('is_late', 'mean'),
    max_overdue_days=('days_overdue', 'max'),
    total_outstanding=('outstanding_amount', 'sum'),
)
# Red flag: payment_trend > 0 AND pct_late > 0.3 AND increasing outstanding
