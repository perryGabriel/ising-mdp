# Python Ising demos (4 models)

This folder contains a standalone script that demonstrates **four Markov models** inspired by the project outline:

1. Single-spin 2-state chain.
2. Mean-field chain over the number of up spins `K`.
3. Local-neighborhood probability evolution on a 2x2 lattice.
4. Full exponential state-space Gibbs model (`2^N` states), capped to `N<=4` by default.

## Run

```bash
python python_demos/ising_four_models.py --steps 4 --exp-atoms 4
```

Useful options:

- `--temperature`, `--coupling`, `--field`
- `--mean-field-spins`
- `--seed`

The script prints top probabilities at each step and samples one next state so you can visualize likely outcomes in the terminal.

## Heatmap GIF animation

Yes — a GIF is a great fit here. The repo now includes `ising_heatmap_gif.py` to animate expected magnetization heatmaps over time for model 3 and model 4.

Install plotting deps:

```bash
pip install matplotlib pillow
```

Generate a GIF:

```bash
python python_demos/ising_heatmap_gif.py --steps 20 --fps 4 --output python_demos/ising_heatmaps.gif
```

Notes:

- Model 3 is shown as a 2x2 local-probability heatmap.
- Model 4 is shown as a 2x2 expected-spin heatmap when `--exp-atoms 4` (default).
- Color scale is expected spin / magnetization in `[-1, 1]`.


## Testing

Run from repo root:

```bash
python -m unittest python_demos/test_ising_four_models.py
```

Or from inside `python_demos/`:

```bash
python test_ising_four_models.py
```
