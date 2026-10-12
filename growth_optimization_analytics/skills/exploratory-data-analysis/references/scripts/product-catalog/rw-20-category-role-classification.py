"""
RW-20: Category Role Classification
Business problem: Classify categories as traffic drivers, margin generators, core strategic, or convenience.
Required columns: transaction_id, category, margin_pct.
Output: Role per category based on penetration × margin quadrant.
"""
import pandas as pd
import numpy as np

cat_roles = df.groupby('category').agg(
    penetration=('transaction_id', lambda x: x.nunique() / df['transaction_id'].nunique()),
    margin_pct=('margin_pct', 'median'),
)
# Quartile-based boundaries (data-derived)
pen_q75 = cat_roles['penetration'].quantile(0.75)
margin_q75 = cat_roles['margin_pct'].quantile(0.75)
cat_roles['role'] = 'convenience'
cat_roles.loc[cat_roles['penetration'] >= pen_q75, 'role'] = 'traffic_driver'
cat_roles.loc[cat_roles['margin_pct'] >= margin_q75, 'role'] = 'margin_generator'
cat_roles.loc[(cat_roles['penetration'] >= pen_q75) & (cat_roles['margin_pct'] >= margin_q75), 'role'] = 'core_strategic'
