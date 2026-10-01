"""
OR-9: Time-of-Day Volume vs Composition Separation
Business problem: Test if hour affects what is purchased, not just volume.
Required columns: order_id, order_hour_of_day, reorder_pct.
Output: Kruskal-Wallis test, effect size vs practical significance floor.
"""
import numpy as np
from scipy.stats import kruskal

hour_rr = order_stats.groupby('order_hour_of_day')['reorder_pct']
groups = [group.values for _, group in hour_rr]
stat, p = kruskal(*groups)
# Derive practical significance floor from distribution of all effect sizes
