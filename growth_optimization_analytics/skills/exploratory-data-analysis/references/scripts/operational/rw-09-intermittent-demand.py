"""
RW-9: Intermittent Demand Forecasting (Croston's Method)
Business problem: Forecast slow-moving SKUs with many zero-demand periods.
Required columns: sku_id, date, quantity (daily or weekly).
Output: 12-week demand forecasts per SKU.
"""
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import CrostonOptimized

ts = df.groupby(['sku_id', pd.Grouper(key='date', freq='W')])['quantity'].sum().reset_index()
ts.columns = ['unique_id', 'ds', 'y']
sf = StatsForecast(models=[CrostonOptimized()], freq='W', n_jobs=-1)
forecasts = sf.fit_predict(ts, h=12)
