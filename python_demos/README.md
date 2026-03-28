# Python Ising demos (4 models)

This package demonstrates **four Ising-inspired models**:

1. Single-spin 2-state chain (model 1).
2. Mean-field chain over `K=#up` (model 2).
3. Local-neighborhood 2x2 probability dynamics (model 3).
4. Full exponential state-space Gibbs model (model 4, typically with `N<=4`).

## Install

From repo root:

```bash
pip install -e .
```

For GIF generation:

```bash
pip install -e .[viz]
```

## Run terminal demo

```bash
python .\python_demos\ising_four_models.py --steps 4 --exp-atoms 4
```

## Heatmap GIF animation

Create an animated GIF with **all four models sharing one lattice size + initial condition**:

```bash
python .\python_demos\ising_heatmap_gif.py --artifact-prefix artifacts --steps 20 --fps 4 --rows 2 --cols 2 --seed 7 --hold-frames 4 --intro-label-frames 6 --output artifacts/gifs/ising_heatmaps.gif
```

The animation panels are:

- **Model 1**: independent-spin lattice heatmap on `rows`x`cols`.
- **Model 2**: mean-field lattice heatmap on `rows`x`cols`.
- **Model 3**: local-neighborhood expected-spin heatmap on `rows`x`cols`.
- **Model 4**: full-state expected-spin heatmap on `rows`x`cols` (currently `rows*cols<=9`).

Color scale values are in `[-1, 1]`.

## Magnetization comparison dataset

Build raw trajectory data and a grouped manifold summary over `(J, h, T, t)`:

```bash
python .\python_demos\ising_magnetization_compare.py --artifact-prefix artifacts --rows 2 --cols 2 --steps 20 --seeds 30 --output-raw artifacts/data/raw/magnetization_timeseries.csv --output-summary artifacts/data/summary/magnetization_summary.csv
```

The raw file stores `m(t)` per model/seed, and the summary file stores mean/variance of `m` at each `(model, J, h, T, t)` grid point.

## Parameter-map fitting

Fit `phi_{i->j}` by nearest-neighbor manifold matching with an affine approximation:

```bash
python .\python_demos\fit_parameter_map.py --artifact-prefix artifacts --source-model model_1 --target-model model_2 --output-map artifacts/maps/parameter_map.csv --output-affine artifacts/maps/parameter_map_affine.json
```

## Manifold plotting

Render trajectory bands and residual maps from generated CSVs:

```bash
python .\python_demos\plot_magnetization_manifold.py --artifact-prefix artifacts --source-model model_1 --target-model model_2 --output-traj artifacts/plots/magnetization_trajectory_bands.png --output-residual artifacts/plots/magnetization_residual_map.png
```

## Trajectory matching visualization

Compare source vs mapped-target trajectories for seeds with similar initial up-spin fraction, and produce evaluation artifacts:

```bash
python .\python_demos\visualize_trajectory_matching.py --artifact-prefix artifacts --source-model model_1 --target-model model_2 --coupling 0.7 --field 0.0 --temperature 1.0 --output-traj artifacts/plots/trajectory_matching.png --output-artifacts artifacts/plots/matching_artifacts.png
```

This reports mapped parameters for each model and writes two figures: (1) seed-level trajectory overlay + means, (2) fit-error histogram + time-resolved manifold residual.

## Explicit renormalization operator demo

Compare `evolve_full_then_project` vs `project_then_evolve_coarse` and report residuals:

```bash
python .\python_demos\renormalization_operator_demo.py --artifact-prefix artifacts --rows 2 --cols 2 --steps 20 --seed 7 --output-csv artifacts/operator/renormalization_operator.csv --output-plot artifacts/operator/renormalization_operator.png
```

This writes a per-time residual CSV and (optionally) a two-panel plot of trajectories and absolute residuals.

## Notebook walkthrough

Open `notebooks/renormalization_demo.ipynb` for a pedagogical side-by-side projection + residual workflow.

## End-to-end pipeline

Run the full report-oriented workflow in one command:

```bash
python .\python_demos\run_report_pipeline.py --artifact-prefix artifacts --rows 2 --cols 2 --steps 20 --seeds 30
# add --skip-plots if matplotlib is unavailable
```

The pipeline also writes `reports/figure_manifest.json` for reproducibility tracking.

## Testing

From repo root:

```bash
python -m unittest .\python_demos\test_ising_four_models.py
```

From inside `python_demos/`:

```bash
python .\python_demos\test_ising_four_models.py
```

All models use the same seeded random lattice initialization (`--seed`).
