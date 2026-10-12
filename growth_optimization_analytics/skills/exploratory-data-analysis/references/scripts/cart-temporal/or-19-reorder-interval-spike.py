"""
OR-19: Reorder Interval Spike Analysis
Business problem: Identify true ordering rhythms vs right-censoring artifacts.
Required columns: user_id, days_since_prior_order.
Output: Genuine cadence peaks after excluding censored values.
"""
import pandas as pd
import numpy as np
from scipy.signal import find_peaks

intervals = orders['days_since_prior_order'].dropna()
counts = intervals.value_counts().sort_index()

# Check for right-censoring at maximum value
max_val = intervals.max()
max_count = counts.get(max_val, 0)
second_max_count = counts.drop(max_val, errors='ignore').max()
if max_count > second_max_count * 1.5:
    print(f"WARNING: Likely right-censored at {max_val} days")
    intervals_clean = intervals[intervals < max_val]

hist_vals = counts.drop(max_val, errors='ignore').values
peaks, properties = find_peaks(hist_vals, height=hist_vals.mean(), distance=3)
