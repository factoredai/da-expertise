"""
RW-13: Promotional Effectiveness (Interrupted Time Series)
Business problem: Measure true promo impact including post-promo demand dip.
Required columns: date, quantity, amount, category, dow.
Output: Uplift, post-promo dip, net uplift, Return on Promotion.
"""
import pandas as pd
from scipy.stats import ttest_ind

promo_period = df[(df['date'] >= promo_start) & (df['date'] <= promo_end)]
baseline_period = df[(df['date'] < promo_start) & (df['dow'].isin(promo_period['dow'].unique()))]

promo_daily = promo_period.groupby('date')['quantity'].sum()
baseline_daily = baseline_period.groupby('date')['quantity'].sum()

uplift = promo_daily.mean() / baseline_daily.mean() - 1
post_promo = df[(df['date'] > promo_end) & (df['date'] <= promo_end + pd.Timedelta(days=14))]
post_dip = post_promo.groupby('date')['quantity'].sum().mean() / baseline_daily.mean() - 1
net_uplift = uplift + post_dip
# RoP = (incremental_gross_margin - promo_cost) / promo_cost
