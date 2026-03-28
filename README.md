# Ising MDP demos

This repository contains:

- A React/Tailwind simulator in `src/` for exploring lattice dynamics.
- A Python package in `python_demos/` for four Ising-inspired model demos.

## Install (editable)

```bash
pip install -e .
```

Import in Python after install:

```python
from isingmdp import IsingParams, model_1_heatmap_trajectory
```

Optional visualization dependencies:

```bash
pip install -e .[viz]
```

## Python quick start

Run terminal simulations:

```bash
python .\python_demos\ising_four_models.py --steps 4 --exp-atoms 4
```

Run tests:

```bash
python -m unittest python_demos.tests.test_ising_four_models
# or run the full suite:
python -m unittest discover -s python_demos/tests -p "test_*.py"
```


Generate cross-model magnetization datasets (raw + summary manifold):

```bash
python .\python_demos\ising_magnetization_compare.py --artifact-prefix artifacts --rows 2 --cols 2 --steps 20 --seeds 30 --output-raw artifacts/data/raw/magnetization_timeseries.csv --output-summary artifacts/data/summary/magnetization_summary.csv
```

Generate animated heatmaps (all four models, with seeded shared lattice init for models 3/4):

```bash
python .\python_demos\ising_heatmap_gif.py --steps 20 --fps 4 --rows 2 --cols 2 --seed 7 --hold-frames 4 --intro-label-frames 6 --output python_demos/ising_heatmaps.gif
```

The GIF includes all four models, and models 3 and 4 share the same seeded 2x2 lattice initialization:

1. Model 1 independent-spin lattice,
2. Model 2 mean-field lattice,
3. Model 3 local-neighborhood probabilities on the selected lattice,
4. Model 4 full state-space expected spins on the same lattice.

and overlays a parameter key (`T`, `J`, `h`, mixing, lattice, seed).
# Ising MDP simulator

This repo now targets **GitHub Pages via `/docs`**.

## Local development

```bash
npm install
npm run dev
```

## Build for Pages

```bash
npm run build
```

The Vite build output is written to `docs/`. Commit that folder, then in GitHub set:

- **Settings → Pages → Source**: `Deploy from a branch`
- **Branch**: `main`
- **Folder**: `/docs`

The app renders four independent simulation panels, each with isolated controls and initial-state tuning.


Model-translation deliverables now include:
- `python_demos/fit_parameter_map.py` for `phi_{i->j}` fitting,
- `python_demos/plot_magnetization_manifold.py` for trajectory bands + residual maps, and
- `python_demos/renormalization_demo.ipynb` for a walkthrough notebook.
