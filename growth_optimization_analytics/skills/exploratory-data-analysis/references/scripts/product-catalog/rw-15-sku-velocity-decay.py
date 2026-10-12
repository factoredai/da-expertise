"""
RW-15: SKU Velocity Decay Detection
Business problem: Detect products showing early declining demand signs.
Required columns: sku_id, date, quantity.
Output: Decaying SKUs with slope, p-value, current vs peak velocity.
"""
import pandas as pd
import numpy as np
from scipy.stats import linregress

recent = df[df['date'] >= df['date'].max() - pd.Timedelta(days=180)]
monthly_velocity = recent.groupby(['sku_id', pd.Grouper(key='date', freq='M')])['quantity'].sum().unstack(fill_value=0)

decay_signals = []
for sku in monthly_velocity.index:
    vals = monthly_velocity.loc[sku].values
    if vals.sum() > 0:
        slope, _, _, p, _ = linregress(range(len(vals)), vals)
        decay_signals.append({'sku_id': sku, 'slope': slope, 'p': p,
                              'current_velocity': vals[-1], 'peak_velocity': vals.max()})
decay_df = pd.DataFrame(decay_signals)
decaying = decay_df[(decay_df['slope'] < 0) & (decay_df['p'] < 0.10) &
                     (decay_df['current_velocity'] < decay_df['peak_velocity'] * 0.5)]
