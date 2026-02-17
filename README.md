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
ising-four-models --steps 4 --exp-atoms 4
```

Run tests:

```bash
python -m unittest python_demos/test_ising_four_models.py
```

Generate animated heatmaps (all four models, same layout/init):

```bash
ising-heatmap-gif --steps 20 --fps 4 --rows 2 --cols 2 --seed 7 --output python_demos/ising_heatmaps.gif
```

The GIF includes all four models in the same 2x2 atom arrangement with shared initialization.
