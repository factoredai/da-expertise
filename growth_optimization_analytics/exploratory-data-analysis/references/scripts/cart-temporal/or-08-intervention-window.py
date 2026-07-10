"""
OR-8: Intervention Window Optimization
Business problem: Find optimal pre-peak marketing intervention time.
Required columns: order_id, order_hour_of_day, user_id, segment.
Output: Peak hours, intervention window, segment-level differences.
"""
import pandas as pd
import numpy as np

hour_vol = orders.groupby('order_hour_of_day').size()
hour_index = hour_vol / hour_vol.mean()
peak_threshold = 1 + hour_index.std()
peak_hours = hour_index[hour_index > peak_threshold].index.tolist()

# Optimal intervention = BEFORE the peak
ramp = hour_index.diff()
max_ramp_hour = ramp.idxmax()
intervention_window = max_ramp_hour - 1

seg_hour = orders.merge(segments, on='user_id').groupby(
    ['segment', 'order_hour_of_day']).size().unstack(fill_value=0)
seg_hour_index = seg_hour.div(seg_hour.mean(axis=1), axis=0)
