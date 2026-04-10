# Artifacts

This directory stores generated outputs from analysis scripts.

- `gifs/`: animated model heatmaps.
- `data/raw/`: seed-level trajectory CSVs.
- `data/summary/`: manifold summary CSVs.
- `maps/`: fitted parameter maps and affine approximations.
- `metrics/`: model-comparison metric CSVs (including model-vs-model_1 magnetization mismatch metrics).
- `plots/`: trajectory bands, residual maps, and matching visualizations.
- `operator/`: renormalization-operator diagnostics (`renormalization_operator.csv` + a two-panel plot with trajectories and |residual| over time).

These files are reproducible from the scripts in `python_demos/`.
