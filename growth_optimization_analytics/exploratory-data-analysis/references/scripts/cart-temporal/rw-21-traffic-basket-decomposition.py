"""
RW-21 — Traffic × Basket DOW Decomposition

Decomposes the day-of-week sales pattern into traffic (transaction count)
and basket (units per transaction) components. Different high-sales days
may achieve their volume through different mechanisms.

Requirements:
  - Daily unit sales (from item-level fact table)
  - Daily transaction counts (from separate POS summary or transactions table)
  - Both at the store or network level

Outputs:
  - DOW table with Sales Index, Traffic Index, Basket Index
  - Classification of each day: traffic-driven, basket-driven, or balanced
  - Optional: segment breakdown by store type or geography
"""

import pandas as pd
import numpy as np


def compute_dow_decomposition(daily_sales, daily_transactions, date_col='date'):
    """
    Decompose DOW pattern into traffic and basket components.

    Parameters
    ----------
    daily_sales : pd.DataFrame
        Must contain `date_col` and 'total_unit_sales' columns.
    daily_transactions : pd.DataFrame
        Must contain `date_col` and 'total_transactions' columns.

    Returns
    -------
    pd.DataFrame with columns:
        day_of_week, avg_sales, avg_txn, avg_upt,
        sales_idx, traffic_idx, basket_idx, classification
    """
    # Merge
    sales = daily_sales.copy()
    sales[date_col] = pd.to_datetime(sales[date_col])
    txn = daily_transactions.copy()
    txn[date_col] = pd.to_datetime(txn[date_col])

    merged = sales.merge(txn, on=date_col, how='inner')
    merged['upt'] = merged['total_unit_sales'] / merged['total_transactions']
    merged['dow'] = merged[date_col].dt.day_name()

    dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                 'Friday', 'Saturday', 'Sunday']

    result = (
        merged.groupby('dow')
        .agg(
            avg_sales=('total_unit_sales', 'mean'),
            avg_txn=('total_transactions', 'mean'),
            avg_upt=('upt', 'mean'),
        )
        .reindex(dow_order)
    )

    # Index to weekly mean
    for col, idx_col in [('avg_sales', 'sales_idx'),
                         ('avg_txn', 'traffic_idx'),
                         ('avg_upt', 'basket_idx')]:
        result[idx_col] = (result[col] / result[col].mean() * 100).round(1)

    # Classify each day
    def classify(row):
        traffic_dev = row['traffic_idx'] - 100
        basket_dev = row['basket_idx'] - 100
        if abs(traffic_dev) < 3 and abs(basket_dev) < 3:
            return 'balanced'
        if traffic_dev > basket_dev + 3:
            return 'traffic-driven'
        if basket_dev > traffic_dev + 3:
            return 'basket-driven'
        return 'balanced'

    result['classification'] = result.apply(classify, axis=1)
    return result.reset_index()


def compute_growth_decomposition(daily_sales, daily_transactions,
                                  date_col='date', n_months=12):
    """
    Decompose long-term sales growth into traffic and basket components.

    Compares the first `n_months` to the last `n_months`.

    Returns
    -------
    dict with keys: sales_growth_pct, traffic_growth_pct, basket_growth_pct
    """
    sales = daily_sales.copy()
    sales[date_col] = pd.to_datetime(sales[date_col])
    txn = daily_transactions.copy()
    txn[date_col] = pd.to_datetime(txn[date_col])

    merged = sales.merge(txn, on=date_col, how='inner')
    merged['upt'] = merged['total_unit_sales'] / merged['total_transactions']
    merged['ym'] = merged[date_col].dt.to_period('M').astype(str)

    monthly = merged.groupby('ym').agg(
        total_sales=('total_unit_sales', 'sum'),
        total_txn=('total_transactions', 'sum'),
        avg_upt=('upt', 'mean'),
    )

    first = monthly.head(n_months)
    last = monthly.iloc[-n_months - 1:-1] if len(monthly) > n_months + 1 else monthly.tail(n_months)

    return {
        'sales_growth_pct': (last['total_sales'].mean() / first['total_sales'].mean() - 1) * 100,
        'traffic_growth_pct': (last['total_txn'].mean() / first['total_txn'].mean() - 1) * 100,
        'basket_growth_pct': (last['avg_upt'].mean() / first['avg_upt'].mean() - 1) * 100,
    }
