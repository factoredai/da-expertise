"""
P5: Three-Screen Scouting List
Business problem: Find high-potential entities meeting quality + undiscoveredness + momentum.
Required: Entity DataFrame with quality, reach, and time-series metrics.
Output: High-potential pool (all 3 screens) and watch list (2 of 3).
"""
import pandas as pd
from scipy.stats import linregress

def scout(df, quality_col, reach_col, min_r2=0.25):
    quality_pass = df[quality_col] > df[quality_col].median()
    reach_pass = df[reach_col] < df[reach_col].median()
    df['screens_passed'] = quality_pass.astype(int) + reach_pass.astype(int)
    # Add momentum screen from time series slope with R² >= min_r2
    high_potential = df[df['screens_passed'] == 3]
    watch_list = df[df['screens_passed'] == 2]
    return high_potential, watch_list
