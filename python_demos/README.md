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

Create an animated GIF with **all four models** and a parameter key overlay:

```bash
ising-heatmap-gif --steps 20 --fps 4 --output python_demos/ising_heatmaps.gif
```

The animation panels are:

- **Model 1**: 1x2 strip for `[P(↓), P(↑)]`.
- **Model 2**: 1x(`N+1`) strip over `K=#up`.
- **Model 3**: 2x2 expected-spin heatmap.
- **Model 4**: 2x2 expected-spin heatmap for `N=4`.

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
