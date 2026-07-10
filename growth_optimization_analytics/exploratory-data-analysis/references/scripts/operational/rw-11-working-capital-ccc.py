"""
RW-11: Working Capital and Cash Conversion Cycle
Business problem: Measure inventory-to-cash efficiency across inflationary periods.
Required columns: date, amount, cost, inventory_value. Optional: accounts_receivable, accounts_payable.
Output: Monthly DIO, DSO, DPO, CCC. Early warning signals.
"""
import pandas as pd

monthly = df.groupby(pd.Grouper(key='date', freq='M')).agg(
    revenue=('amount', 'sum'), cogs=('cost', 'sum'), avg_inventory=('inventory_value', 'mean'))
monthly['DIO'] = monthly['avg_inventory'] / monthly['cogs'] * 30
# Use unit-based DIO when possible (inflation-immune)
# Early warning: rising DIO + stable DSO + falling DPO = cash consumed by inventory
