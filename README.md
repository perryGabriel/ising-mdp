# Ising MDP demos

This repository contains:

- A React/Tailwind simulator in `src/` for exploring lattice dynamics.
- A Python package in `python_demos/` for four Ising-inspired model demos.

## Install (editable)

```bash
pip install -e .
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

Generate animated heatmaps (all four models, same layout/init):

```bash
ising-heatmap-gif --steps 20 --fps 4 --rows 2 --cols 2 --seed 7 --output python_demos/ising_heatmaps.gif
```

The GIF includes all four models in the same 2x2 atom arrangement with shared initialization:

1. Model 1 single-spin chain,
2. Model 2 mean-field over `K=#up`,
3. Model 3 local 2x2 probabilities,
4. Model 4 full state-space expected spins,

and overlays a parameter key (`T`, `J`, `h`, mixing, mean-field size).
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
