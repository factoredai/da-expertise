"""
RW-16: Customer Basket Migration Tracking
Business problem: Detect trading down, trading out, or consolidation under inflation.
Required columns: customer_id, month, category, quantity.
Output: Period-over-period category share changes per customer.
"""
import pandas as pd

customer_monthly = df.groupby(['customer_id', 'month', 'category'])['quantity'].sum()
customer_basket_share = customer_monthly / customer_monthly.groupby(['customer_id', 'month']).transform('sum')
# Trade-down signal: increasing private-label share + decreasing premium-brand share
