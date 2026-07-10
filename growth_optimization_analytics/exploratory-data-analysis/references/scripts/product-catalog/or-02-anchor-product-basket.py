"""
OR-2: Anchor Product Basket Premium Analysis
Business problem: Identify high-penetration products that predict larger basket sizes.
Required columns: product_id, unique_users in product_stats; order_id, product_id in order_products; order_id, basket_size in basket_stats.
Output: Premium per candidate, anchor classification via GMM.
"""
import pandas as pd
import numpy as np
from sklearn.mixture import GaussianMixture

penetration = product_stats[['product_id', 'unique_users']].copy()
penetration['user_pct'] = penetration['unique_users'] / total_users * 100
threshold_pct = penetration['user_pct'].quantile(0.75)
candidates = penetration[penetration['user_pct'] >= threshold_pct]

premiums = []
for pid in candidates['product_id']:
    orders_with = set(order_products[order_products['product_id'] == pid]['order_id'])
    median_with = basket_stats[basket_stats['order_id'].isin(orders_with)]['basket_size'].median()
    median_without = basket_stats[~basket_stats['order_id'].isin(orders_with)]['basket_size'].median()
    premium = (median_with / median_without - 1) * 100
    premiums.append({'product_id': pid, 'premium_pct': premium, 'n_orders_with': len(orders_with)})
premium_df = pd.DataFrame(premiums)

gmm = GaussianMixture(n_components=2, random_state=42)
premium_df['anchor_label'] = gmm.fit_predict(premium_df[['premium_pct']])
