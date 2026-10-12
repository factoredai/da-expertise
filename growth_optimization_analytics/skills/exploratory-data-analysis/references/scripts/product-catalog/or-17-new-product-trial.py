"""
OR-17: New-Product Trial and Adoption Tracking
Business problem: Measure first-trial to reorder conversion probability.
Required columns: user_id, product_id, order_number, reordered in order_products; order_id, user_id, order_number in orders.
Output: Adoption rate overall and by category/segment.
"""
import pandas as pd

first_encounters = order_products[order_products['reordered'] == 0].copy()
trials = first_encounters.groupby(['user_id', 'product_id'])['order_number'].min().reset_index()
trials.columns = ['user_id', 'product_id', 'trial_order']

all_purchases = order_products.merge(orders[['order_id', 'user_id', 'order_number']], on='order_id')
repeat = all_purchases.merge(trials, on=['user_id', 'product_id'])
repeat = repeat[repeat['order_number'] > repeat['trial_order']]
adopted = repeat.groupby(['user_id', 'product_id']).size().reset_index(name='n_repeats')

trials['adopted'] = trials.set_index(['user_id', 'product_id']).index.isin(
    adopted.set_index(['user_id', 'product_id']).index)
adoption_rate = trials['adopted'].mean()
