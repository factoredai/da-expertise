"""
P2: Cohort-Relative Scoring
Business problem: Remove age/time bias by ranking within same-age cohort.
Required: Entity DataFrame with cohort field and performance metric.
Output: Percentile rank within cohort (0.0 to 1.0).
"""
import pandas as pd

def cohort_score(df, cohort_col, metric_col):
    df['cohort_percentile'] = df.groupby(cohort_col)[metric_col].rank(pct=True)
    df['cohort_size'] = df.groupby(cohort_col)[metric_col].transform('count')
    return df
