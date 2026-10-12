"""
OR-3: Shopping Mission Type Analysis
Business problem: Determine if business is planned stock-up or top-up convenience.
Required columns: order_id, basket_size. Optional: user_id, segment.
Output: Mission boundary, single-item rates by segment, bimodality test results.
"""
import pandas as pd
import numpy as np
from scipy.stats import gaussian_kde, chi2_contingency
from scipy.signal import find_peaks

# Step 1: Examine basket size distribution for bimodality
basket_sizes = basket_stats['basket_size'].values
kde = gaussian_kde(basket_sizes)
x_range = np.arange(1, basket_sizes.max())
density = kde(x_range)
# height threshold at 5% of max to ignore noise; distance=3 prevents adjacent false peaks
peaks, _ = find_peaks(density, height=density.max() * 0.05, distance=3)

# Hartigan's dip test for bimodality (if diptest package available)
try:
    from diptest import diptest
    dip_stat, dip_p = diptest(basket_sizes)
except ImportError:
    dip_stat, dip_p = None, None

# Step 2: If bimodal, derive mission boundary from valley between modes
if len(peaks) >= 2:
    valley_idx = np.argmin(density[peaks[0]:peaks[1]]) + peaks[0]
    mission_boundary = x_range[valley_idx]
else:
    # No clear bimodality — use median as reference point
    mission_boundary = np.median(basket_sizes)

# Step 3: Single-item rate by segment
single_rate = basket_stats.merge(segments, on='user_id')
seg_single = single_rate.groupby('segment').apply(
    lambda g: (g['basket_size'] == 1).mean()
).reset_index(name='single_item_rate')

# Step 4: Test segment differences
ct = pd.crosstab(single_rate['segment'], single_rate['basket_size'] == 1)
chi2, p, dof, expected = chi2_contingency(ct)
# Cramer's V: effect size for categorical association (0=none, 1=perfect)
cramers_v = np.sqrt(chi2 / (ct.sum().sum() * (min(ct.shape) - 1)))

# Rate ratio across segments — >2x suggests segment-specific behavior
rate_ratio = seg_single['single_item_rate'].max() / seg_single['single_item_rate'].min()
