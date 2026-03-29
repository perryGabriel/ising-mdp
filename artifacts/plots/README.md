# Plot artifacts

Generated figures include:
- residual heatmaps,
- manifold trajectory bands,
- mapped trajectory overlays,
- matching/evaluation artifact dashboards.

## `magnetization_residual_map.png`

This heatmap summarizes *where the cross-model parameter mapping is easiest vs hardest*.

- **x-axis**: source external field `h`
- **y-axis**: source coupling `J`
- **colorbar**: mean `fit_error` for that `(J, h)` source point, averaged across all source temperatures `T`.

For each source point `(J, h, T)` in `parameter_map.csv`, `fit_error` is computed as the
time-averaged weighted squared distance between source and best-matched target magnetization
statistics (mean + variance trajectory terms). Lower values indicate that the target model can
reproduce the source trajectory manifold more closely at that region of parameter space.
