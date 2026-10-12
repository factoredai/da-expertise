"""
OR-21: Product Lifecycle Stage Classification
Business problem: Classify products as gateway, staple, universal, or exploration.
Required columns: product_id, total_orders, first_order_counts, mature_order_counts.
Output: Lifecycle stage per product.
"""
import pandas as pd

product_lifecycle = pd.DataFrame({
    'product_id': product_stats['product_id'],
    'first_order_share': first_order_counts / product_stats['total_orders'],
    'mature_order_share': mature_order_counts / product_stats['total_orders'],
    'total_orders': product_stats['total_orders']
})

fo_med = product_lifecycle['first_order_share'].median()
mo_med = product_lifecycle['mature_order_share'].median()

product_lifecycle['lifecycle_stage'] = 'exploration'
product_lifecycle.loc[product_lifecycle['first_order_share'] > fo_med, 'lifecycle_stage'] = 'gateway'
product_lifecycle.loc[product_lifecycle['mature_order_share'] > mo_med, 'lifecycle_stage'] = 'staple'
product_lifecycle.loc[(product_lifecycle['first_order_share'] > fo_med) &
                       (product_lifecycle['mature_order_share'] > mo_med), 'lifecycle_stage'] = 'universal'
