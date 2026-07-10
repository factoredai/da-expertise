"""
P1: Subset Fingerprinting
Business problem: Identify what distinguishes a high-performing subset from full population.
Required: Entity DataFrame with categorical attributes, success flag.
Output: Overrepresentation ratios per attribute with Bonferroni correction.
"""
import pandas as pd
import numpy as np

def fingerprint(df, success_col, attributes, alpha=0.05):
    success = df[df[success_col]]
    results = []
    for attr in attributes:
        for val in df[attr].unique():
            pop_pct = (df[attr] == val).mean()
            success_pct = (success[attr] == val).mean()
            ratio = success_pct / pop_pct if pop_pct > 0 else np.inf
            results.append({'attribute': attr, 'value': val, 'ratio': ratio,
                           'pop_count': (df[attr] == val).sum(),
                           'success_count': (success[attr] == val).sum()})
    return pd.DataFrame(results)
