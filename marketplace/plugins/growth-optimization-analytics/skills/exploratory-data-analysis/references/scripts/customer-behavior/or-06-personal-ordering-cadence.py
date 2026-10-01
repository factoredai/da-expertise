"""
OR-6: Personal Ordering Cadence Distribution
Business problem: Identify true ordering rhythms and whether population-level timing works.
Required columns: user_id, order_id, days_since_prior_order, segment.
Output: Cadence peaks, bucket boundaries, segment-level cadence profiles.
"""
import pandas as pd
import numpy as np
from scipy.signal import find_peaks

# Step 1: Compute per-user dominant cadence (mode of inter-order intervals)
# Mode chosen over mean/median because ordering rhythms are discrete (weekly, biweekly, monthly)
user_intervals = orders.groupby('user_id')['days_since_prior_order'].apply(
    lambda x: x.dropna().mode().iloc[0] if len(x.dropna().mode()) > 0 else np.nan
).dropna()

# Step 2: Examine population distribution of cadences
# Bins from 1-31 to capture daily through monthly rhythms
hist_vals, bin_edges = np.histogram(user_intervals, bins=range(1, 32))
# height at 10% of max filters noise; distance=3 prevents adjacent false peaks
peaks, _ = find_peaks(hist_vals, height=hist_vals.max() * 0.1, distance=3)

# Hartigan's dip test for multi-modality
try:
    from diptest import diptest
    dip_stat, dip_p = diptest(user_intervals.values)
except ImportError:
    dip_stat, dip_p = None, None

# Step 3: If peaks exist, derive bucket boundaries from valleys between peaks
if len(peaks) >= 2:
    for i in range(len(peaks) - 1):
        valley = np.argmin(hist_vals[peaks[i]:peaks[i+1]]) + peaks[i]
        print(f"Cadence boundary at day {bin_edges[valley]}")

# Step 4: Cross with behavioral segments
cadence_by_seg = orders.merge(segments, on='user_id').groupby('segment')['days_since_prior_order'].describe()
