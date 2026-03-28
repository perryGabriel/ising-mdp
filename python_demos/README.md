# Python Ising demos (4 models)

This package demonstrates **four Ising-inspired models**:

1. Single-spin 2-state chain (model 1).
2. Mean-field chain over `K=#up` (model 2).
3. Local-neighborhood probability dynamics on rows×cols lattices (model 3).
4. Full exponential state-space Gibbs model (model 4, typically with `N<=16`).
5. A probabilistic model built heuristically from the expected effect each parameter should have.

## Phase-based layout

For first-time users, scripts are organized by dependency order:

- `foundation/`: core model definitions and shared simulation utilities.
- `stage1_generate/`: data and animation generation from the core models.
- `stage2_map/`: model-to-model parameter-map fitting (consumes stage1 summaries).
- `stage3_analyze/`: plotting, trajectory comparison, and renormalization diagnostics (consumes stage1/stage2 outputs).
- `stage4_report/`: orchestration and manifest generation for reproducible report runs.
- `tests/`: unit tests aligned to the same workflow.

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
python .\python_demos\foundation\ising_four_models.py --steps 4 --exp-atoms 16
```

## Heatmap GIF animation

Create an animated GIF with selected models (defaults to **all five**) sharing one lattice size + initial condition:

```bash
python .\python_demos\stage1_generate\ising_heatmap_gif.py --artifact-prefix artifacts --steps 20 --fps 4 --rows 4 --cols 4 --seed 7 --hold-frames 4 --intro-label-frames 6 --models 1,2,3,5 --output artifacts/plots/ising_heatmaps.gif
```

The animation panels are:

- **Model 1**: independent-spin lattice heatmap on `rows`x`cols`.
- **Model 2**: mean-field lattice heatmap on `rows`x`cols`.
- **Model 3**: local-neighborhood expected-spin heatmap on `rows`x`cols`.
- **Model 4**: full-state expected-spin heatmap on `rows`x`cols` (currently `rows*cols<=16`, i.e. up to 4x4).
- **Model 5**: restricted-interval affine operator model on per-site probabilities.

Use `--models` to include a subset (for example, omit model 4 on larger lattices).

Color scale values are in `[-1, 1]`.

## Magnetization comparison dataset

Build raw trajectory data and a grouped manifold summary over `(J, h, T, t)`:

```bash
python .\python_demos\stage1_generate\ising_magnetization_compare.py --artifact-prefix artifacts --output-raw artifacts/data/raw/magnetization_timeseries.csv --output-summary artifacts/data/summary/magnetization_summary.csv
```

The raw file stores `m(t)` per model/seed, and the summary file stores mean/variance of `m` at each `(model, J, h, T, t)` grid point.

## Parameter-map fitting

Fit `phi_{i->j}` by nearest-neighbor manifold matching with an affine approximation:

```bash
python .\python_demos\stage2_map\fit_parameter_map.py --artifact-prefix artifacts --source-model model_1 --target-model model_5 --output-map artifacts/maps/parameter_map_1_5.csv --output-affine artifacts/maps/parameter_map_affine_1_5.json
```

Optional: fit the affine map in a tanh/arctanh-normalized space for bounded parameters:

```bash
python .\python_demos\stage2_map\fit_parameter_map.py --artifact-prefix artifacts --source-model model_1 --target-model model_5 --fit-space tanh-normalized --coupling-min -1 --coupling-max 1 --field-min -1 --field-max 1 --temperature-min 0 --temperature-max 1
```

Optional: fit the affine map in a tanh/arctanh-normalized space for bounded parameters:

```bash
python .\python_demos\stage2_map\fit_parameter_map.py --artifact-prefix artifacts --source-model model_1 --target-model model_2 --fit-space tanh-normalized --coupling-min -1 --coupling-max 1 --field-min -1 --field-max 1 --temperature-min 0 --temperature-max 1
```

## Manifold plotting

Render trajectory bands and residual maps from generated CSVs:

```bash
python .\python_demos\stage3_analyze\plot_magnetization_manifold.py --artifact-prefix artifacts --source-model model_1 --target-model model_5 --output-traj artifacts/plots/magnetization_trajectory_bands.png --output-residual artifacts/plots/magnetization_residual_map_1_5.png
```

Plot the full summary manifold as a grid (rows = parameter settings, columns = models) with mean and 95% CI fill bands:

```bash
python .\python_demos\stage3_analyze\plot_summary_magnetization_grid.py --artifact-prefix artifacts --output artifacts/plots/magnetization_summary_grid.png
```

## Trajectory matching visualization

Compare source vs mapped-target trajectories for seeds with similar initial up-spin fraction, and produce evaluation artifacts:

```bash
python .\python_demos\stage3_analyze\visualize_trajectory_matching.py --artifact-prefix artifacts --source-model model_2 --target-model model_3 --coupling 0.0 --field 0.0 --temperature 0.0 --output-traj artifacts/plots/trajectory_matching_2_3.png --output-artifacts artifacts/plots/matching_artifacts_2_3.png
```

This reports mapped parameters for each model and writes two figures: (1) seed-level trajectory overlay + means, (2) fit-error histogram + time-resolved manifold residual.

## Explicit renormalization operator demo

Compare `evolve_full_then_project` vs `project_then_evolve_coarse` and report residuals:

```bash
python .\python_demos\stage3_analyze\renormalization_operator_demo.py --artifact-prefix artifacts --rows 3 --cols 3 --steps 20 --seed 7 --output-csv artifacts/operator/renormalization_operator.csv --output-plot artifacts/operator/renormalization_operator.png
```

This writes a per-time residual CSV and (optionally) a two-panel plot of trajectories and absolute residuals.

## Notebook walkthrough

Open `notebooks/renormalization_demo.ipynb` for a pedagogical side-by-side projection + residual workflow.

## End-to-end pipeline

Run the full report-oriented workflow in one command:

```bash
python .\python_demos\stage4_report\run_report_pipeline.py --artifact-prefix artifacts --rows 3 --cols 3 --steps 20 --seeds 30
# add --skip-plots if matplotlib is unavailable
```

The pipeline also writes `reports/figure_manifest.json` for reproducibility tracking.

## Testing

From repo root:

```bash
python -m unittest python_demos.tests.test_ising_four_models
# or run the full suite:
python -m unittest discover -s python_demos/tests -p "test_*.py"
```

From inside `python_demos/`:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

All models use the same seeded random lattice initialization (`--seed`).
