"""
P6: Commercially Significant Subset Test
Business problem: Verify findings survive restriction to commercially relevant entities.
Required: Analysis results on full population, commercial significance metric.
Output: Full population vs core business comparison.
"""
import pandas as pd

def test_commercial_significance(df, metric_col, commercial_col, threshold_pct=80):
    sorted_df = df.sort_values(commercial_col, ascending=False)
    cumshare = sorted_df[commercial_col].cumsum() / sorted_df[commercial_col].sum()
    core = sorted_df[cumshare <= threshold_pct / 100]
    return {
        'full_population': df[metric_col].describe(),
        'core_business': core[metric_col].describe(),
        'core_size': len(core),
        'full_size': len(df),
    }
