"""
RW-1: ABC/XYZ Inventory Classification
Business problem: Classify SKUs by value (ABC) and demand predictability (XYZ).
Required columns: sku_id, date, quantity, unit_price, unit_cost.
Output: 9-cell matrix with management actions per SKU.
"""
import pandas as pd
import numpy as np

# Unit-based ABC (immune to price changes)
sku_units = df.groupby('sku_id')['quantity'].sum().sort_values(ascending=False)
sku_units_cumshare = sku_units.cumsum() / sku_units.sum()
sku_abc_units = pd.cut(sku_units_cumshare, bins=[0, 0.80, 0.95, 1.0], labels=['A', 'B', 'C'], include_lowest=True)

# Margin-based ABC
df['gross_margin'] = (df['unit_price'] - df['unit_cost']) * df['quantity']
sku_margin = df.groupby('sku_id')['gross_margin'].sum().sort_values(ascending=False)
sku_margin_cumshare = sku_margin.cumsum() / sku_margin.sum()
sku_abc_margin = pd.cut(sku_margin_cumshare, bins=[0, 0.80, 0.95, 1.0], labels=['A', 'B', 'C'], include_lowest=True)
# Final ABC = higher of unit vs margin class

# XYZ: data-derived tercile thresholds (not fixed cutoffs)
monthly = df.groupby(['sku_id', pd.Grouper(key='date', freq='M')])['quantity'].sum().unstack(fill_value=0)
cv = monthly.std(axis=1) / monthly.mean(axis=1)
thresholds = cv.quantile([0.33, 0.67])
sku_xyz = pd.cut(cv, bins=[-np.inf, thresholds.iloc[0], thresholds.iloc[1], np.inf], labels=['X', 'Y', 'Z'])
