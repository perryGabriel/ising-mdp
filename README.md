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
python python_demos/ising_four_models.py --steps 4 --exp-atoms 4
```

Run tests:

```bash
python -m unittest python_demos/test_ising_four_models.py
```


Generate cross-model magnetization datasets (raw + summary manifold):

```bash
python python_demos/ising_magnetization_compare.py --rows 2 --cols 2 --steps 20 --seeds 30 --output-raw python_demos/magnetization_timeseries.csv --output-summary python_demos/magnetization_summary.csv
```

Generate animated heatmaps (all four models on the same rows×cols lattice and shared seed):

```bash
python .\python_demos\ising_heatmap_gif.py --steps 20 --fps 4 --rows 2 --cols 2 --seed 7 --hold-frames 4 --intro-label-frames 6 --output python_demos/ising_heatmaps.gif
```

The GIF includes all four models on the same lattice shape, all seeded from the same initial state:

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
