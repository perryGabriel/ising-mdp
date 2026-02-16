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
