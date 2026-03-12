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
ising-heatmap-gif --steps 20 --fps 4 --rows 2 --cols 2 --seed 7 --output python_demos/ising_heatmaps.gif
```

The animation panels are:

- **Model 1**: 1x2 strip for `[P(↓), P(↑)]`.
- **Model 2**: 1x(`N+1`) strip over `K=#up`.
- **Model 3**: `rows`x`cols` expected-spin heatmap.
- **Model 4**: `rows`x`cols` expected-spin heatmap for `N=rows*cols` (currently `N<=4`).

Color scale values are in `[-1, 1]`.

## Testing

From repo root:

```bash
python -m unittest python_demos/test_ising_four_models.py
```

From inside `python_demos/`:

```bash
python test_ising_four_models.py
```

Models 3 and 4 use the same seeded random lattice initialization (`--seed`).
