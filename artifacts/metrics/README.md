# Metrics artifacts

Generated metric CSVs include:
- `magnetization_summary_metrics.csv`: per-parameter, per-model metrics from `plot_summary_magnetization_grid.py`, using `model_1` as ground truth for mismatch/error columns.

Columns:
- `model`, `coupling`, `field`, `temperature`
- `runtime_seconds`
- `transient_rmse_vs_model_1`
- `steady_state_bias_vs_model_1`
- `convergence_time`
- `convergence_time_diff_vs_model_1`
- `variance_mismatch_vs_model_1`
