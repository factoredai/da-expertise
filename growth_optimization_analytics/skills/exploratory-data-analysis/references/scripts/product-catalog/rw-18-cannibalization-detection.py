"""
RW-18: Cannibalization Detection for New Products
Business problem: Determine if new product grew category or just redistributed demand.
Required columns: sku_id, date, quantity, category.
Output: Category growth rate, new product share, cannibalization assessment.
"""
import pandas as pd

# Set these to the specific engagement values
intro_date = pd.Timestamp('...')  # new product launch date
category = '...'  # target category
new_sku_id = '...'

pre = df[(df['date'] < intro_date) & (df['category'] == category)]
post = df[(df['date'] >= intro_date) & (df['category'] == category)]

pre_daily = pre.groupby('date')['quantity'].sum().mean()
post_daily = post.groupby('date')['quantity'].sum().mean()
category_growth = (post_daily / pre_daily - 1) * 100

new_product_share = post[post['sku_id'] == new_sku_id]['quantity'].sum() / post['quantity'].sum()
# category_growth ≈ 0 + significant share → pure cannibalization
# category_growth > 0 → at least partially incremental
