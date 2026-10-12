"""
RW-8: Gross Margin Analysis
Business problem: Find where the business actually makes money.
Required columns: sku_id, quantity, unit_price, unit_cost, date, category.
Output: Margin by category, margin traps, loss leader assessment.
"""
import pandas as pd
import numpy as np

df['gross_margin'] = (df['unit_price'] - df['unit_cost']) * df['quantity']
df['margin_pct'] = (df['unit_price'] - df['unit_cost']) / df['unit_price'] * 100

cat_margin = df.groupby('category').agg(
    revenue=('amount', 'sum'), margin=('gross_margin', 'sum'),
    margin_pct=('margin_pct', 'median'), transactions=('transaction_id', 'nunique'),
).assign(margin_contribution=lambda x: x['margin'] / x['margin'].sum() * 100)

# Margin traps: high revenue, low margin
sku_margin = df.groupby('sku_id').agg(
    revenue=('amount', 'sum'), margin=('gross_margin', 'sum'), margin_pct=('margin_pct', 'median'))
margin_traps = sku_margin[(sku_margin['revenue'] > sku_margin['revenue'].quantile(0.75)) &
                           (sku_margin['margin_pct'] < 5)]
