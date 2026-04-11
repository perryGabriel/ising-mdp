# Metrics artifacts

Generated metric CSVs include:
- `magnetization_summary_metrics.csv`: per-parameter, per-model metrics from `plot_summary_magnetization_grid.py`, using `model_1` as ground truth for mismatch/error columns.

Columns:
- `model`, `coupling`, `field`, `temperature`
- `runtime_seconds` (per-row metric computation runtime in `plot_summary_magnetization_grid.py`)
- `transient_rmse_vs_model_1` (RMSE over the transient half of the trajectory, using model 1 means as ground truth)
- `steady_state_bias_vs_model_1` (difference in late-window means: model minus model 1)
- `convergence_time` (first time index after which the trajectory stays within tolerance of its own steady-state mean)
- `convergence_time_diff_vs_model_1`
- `variance_mismatch_vs_model_1` (mean absolute variance difference over time versus model 1)
