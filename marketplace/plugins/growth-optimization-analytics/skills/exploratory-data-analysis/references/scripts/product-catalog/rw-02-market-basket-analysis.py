"""
RW-2: Market Basket Analysis (Apriori)
Business problem: Find frequently co-purchased products.
Required columns: transaction_id, product_name, segment.
Output: Association rules with lift, confidence, Kulczynski.
"""
import pandas as pd
import numpy as np
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

# CRITICAL: Segment B2B/B2C BEFORE running Apriori
b2b_transactions = df[df['segment'] == 'B2B'].groupby('transaction_id')['product_name'].apply(list)
te = TransactionEncoder()
te_array = te.fit_transform(b2b_transactions)
basket_df = pd.DataFrame(te_array, columns=te.columns_)

freq_items = apriori(basket_df, min_support=0.01, use_colnames=True)
rules = association_rules(freq_items, metric='lift', min_threshold=1.0)
rules['kulc'] = 0.5 * (rules['confidence'] + rules['consequent support'] * rules['lift'])

# Data-derived thresholds
lift_threshold = rules['lift'].quantile(0.75)
support_threshold = rules['support'].quantile(0.25)
actionable = rules[(rules['lift'] > lift_threshold) & (rules['support'] > support_threshold)]
