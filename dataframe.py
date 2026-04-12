import pandas as pd


# python .\python_demos\stage3_analyze\plot_summary_magnetization_grid.py --artifact-prefix artifacts --output artifacts/plots/magnetization_summary_grid.png
# python .\python_demos\stage3_analyze\plot_summary_magnetization_grid.py --artifact-prefix artifacts --output artifacts/plots/magnetization_summary_grid.png
# python .\python_demos\stage3_analyze\plot_one_at_a_time_sweeps.py --artifact-prefix artifacts --num-base-points 5 --output artifacts/plots/magnetization_one_at_a_time_sweeps.png
# python dataframe.py 

df = pd.read_csv('artifacts/data/raw/magnetization_timeseries.csv')
print(df.head())

# group by model, output average runtime_seconds
grouped = df.groupby(['model'])['runtime_seconds'].mean().reset_index()
print(grouped)

# model,coupling,field,temperature,
# runtime_seconds,runtime_ratio_vs_model_1,transient_rmse_vs_model_1,
# steady_state_bias_vs_model_1,convergence_time,convergence_time_diff_vs_model_1,variance_mismatch_vs_model_1

df = pd.read_csv('artifacts/metrics/magnetization_summary_metrics.csv')
rmse = df.groupby(['model'])['transient_rmse_vs_model_1'].mean().reset_index()
bias = df.groupby(['model'])['steady_state_bias_vs_model_1'].mean().reset_index()
var = df.groupby(['model'])['variance_mismatch_vs_model_1'].mean().reset_index()
trans = df.groupby(['model'])['convergence_time_diff_vs_model_1'].mean().reset_index()
time = df.groupby(['model'])['runtime_ratio_vs_model_1'].mean().reset_index()
# stack these columns together
grouped = pd.merge(rmse, bias, on='model')
grouped = pd.merge(grouped, var, on='model')
grouped = pd.merge(grouped, trans, on='model')
grouped = pd.merge(grouped, time, on='model')
print(grouped)
