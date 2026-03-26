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
ising-four-models --steps 4 --exp-atoms 4
```

## Heatmap GIF animation

Create an animated GIF with **all four models sharing one lattice size + initial condition**:

```bash
python .\python_demos\ising_heatmap_gif.py --steps 20 --fps 4 --rows 2 --cols 2 --seed 7 --hold-frames 4 --intro-label-frames 6 --output python_demos/ising_heatmaps.gif
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
python .\python_demos\ising_magnetization_compare.py --rows 2 --cols 2 --steps 20 --seeds 30 --output-raw magnetization_timeseries.csv --output-summary magnetization_summary.csv
```

The raw file stores `m(t)` per model/seed, and the summary file stores mean/variance of `m` at each `(model, J, h, T, t)` grid point.

## Parameter-map fitting

Fit `phi_{i->j}` by nearest-neighbor manifold matching with an affine approximation:

```bash
python fit_parameter_map.py --summary-csv magnetization_summary.csv --source-model model_1 --target-model model_2 --output-map parameter_map.csv --output-affine parameter_map_affine.json
```

## Manifold plotting

Render trajectory bands and residual maps from generated CSVs:

```bash
python plot_magnetization_manifold.py --summary-csv magnetization_summary.csv --map-csv parameter_map.csv --source-model model_1 --target-model model_2 --output-traj traj_bands.png --output-residual residual_map.png
```

## Notebook walkthrough

Open `renormalization_demo.ipynb` for a pedagogical side-by-side projection + residual workflow.

## Testing

From repo root:

```bash
python -m unittest python_demos/test_ising_four_models.py
```

From inside `python_demos/`:

```bash
python test_ising_four_models.py
```

All models use the same seeded random lattice initialization (`--seed`).
