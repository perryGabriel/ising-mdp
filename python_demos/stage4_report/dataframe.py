import pandas as pd

df = pd.read_csv('artifacts/data/raw/magnetization_timeseries.csv')

print(df.head())

# group by model, output average runtime_seconds
grouped = df.groupby(['model'])['runtime_seconds'].mean().reset_index()
print(grouped)

df = pd.read_csv('artifacts/metrics/magnetization_summary_metrics.csv')
grouped = df.groupby(['model'])['runtime_ratio_vs_model_1'].mean().reset_index()
print(grouped)