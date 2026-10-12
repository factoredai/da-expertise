"""
P3: Pre/Post Event Split for Trend Validation
Business problem: Confirm trend exists before structural break, not only after.
Required: Time series with known event date.
Output: Pre-event and post-event trend slopes with R-squared.
"""
import pandas as pd
import numpy as np
from scipy.stats import linregress

def validate_trend(series, event_date, date_col='date', value_col='value'):
    pre = series[series[date_col] < event_date]
    post = series[series[date_col] >= event_date]
    results = {}
    if len(pre) >= 3:
        slope, _, r, p, _ = linregress(range(len(pre)), pre[value_col].values)
        results['pre'] = {'slope': slope, 'r2': r**2, 'p': p}
    if len(post) >= 3:
        slope, _, r, p, _ = linregress(range(len(post)), post[value_col].values)
        results['post'] = {'slope': slope, 'r2': r**2, 'p': p}
    return results
