#!/usr/bin/env python3
"""Core simulation and visualization helpers for Ising-inspired models.

This module includes:
1) A single-spin two-state chain.
2) A mean-field chain over K=#(up spins).
3) A local-neighborhood probability model on an arbitrary rows x cols lattice.
4) A full exponential-state Gibbs model (recommended with N<=16).
5) A restricted-interval affine operator model over per-site spin probabilities.

It also exposes convenience trajectory builders for terminal demos and heatmaps.
"""

from __future__ import annotations

import argparse
import itertools
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

Spin = int
State = Tuple[Spin, ...]
Distribution = Dict[State, float]

# Practical cap for full-state (model 4) demos.
MAX_ATOMS = 16
MODEL_2_TEMPERATURE_SCALE = 1.5 # Scale temperature for model 2 to roughly match model-1 convergence time.
MODEL_3_TEMPERATURE_SCALE = 1.5 # Scale temperature for model 3 to roughly match model-1 convergence time.
MODEL_3_TIME_ADJUSTMENT = 6 # Adjust model-3 steps to roughly match model-1 convergence time.
MODEL_4_TIME_ADJUSTMENT = 8 # Adjust model-4 steps to roughly match model-1 convergence time. 
MODEL_5_FIELD_SCALE = 8 # Scale field strength for model 5 to roughly match model-1 steady state.
MODEL_5_TEMPERATURE_SCALE = 1.0 # Scale temperature for model 5 to roughly match model-1 convergence time.

@dataclass(frozen=True)
class IsingParams:
    """Physical-ish parameters shared by all models."""

    temperature: float = 1.0
    coupling: float = 0.8
    field: float = 0.0


def logistic(x: float) -> float:
    """Return logistic sigmoid 1/(1+exp(-x))."""

    return 1.0 / (1.0 + math.exp(-x))


def normalize(dist: Distribution) -> Distribution:
    """Normalize a state distribution and clip tiny negatives to zero."""

    total = sum(max(p, 0.0) for p in dist.values())
    if total <= 0:
        raise ValueError("Distribution mass must be positive.")
    return {s: max(p, 0.0) / total for s, p in dist.items()}


def sample_from_distribution(rng: random.Random, dist: Distribution) -> State:
    """Sample one state from a distribution dictionary."""

    r = rng.random()
    acc = 0.0
    last_state = None
    for state, prob in dist.items():
        acc += prob
        last_state = state
        if r <= acc:
            return state
    assert last_state is not None
    return last_state


def state_probability_bars(dist: Distribution, width: int = 24, top_k: int = 6) -> str:
    """Render an ASCII bar chart for the top-k states in a distribution."""

    rows = []
    for state, prob in sorted(dist.items(), key=lambda item: item[1], reverse=True)[:top_k]:
        label = "".join("↑" if s == 1 else "↓" for s in state)
        bar = "█" * max(1, int(round(prob * width)))
        rows.append(f"{label:<10} {bar:<{width}} {prob:>6.3f}")
    return "\n".join(rows)


def render_lattice(state: State, n_cols: int = 2) -> str:
    """Render a spin state as an up/down lattice string."""

    chars = ["↑" if s == 1 else "↓" for s in state]
    rows = [chars[i : i + n_cols] for i in range(0, len(chars), n_cols)]
    return "\n".join(" ".join(row) for row in rows)


def spins_to_grid(values: Sequence[float], n_cols: int = 2) -> List[List[float]]:
    """Convert a flat list of values to a row-major 2D grid."""

    return [list(values[i : i + n_cols]) for i in range(0, len(values), n_cols)]


def expected_site_magnetization(dist: Distribution) -> List[float]:
    """Compute expected spin E[s_i] for each site under a distribution."""

    if not dist:
        return []
    n = len(next(iter(dist.keys())))
    return [sum(state[i] * p for state, p in dist.items()) for i in range(n)]


# ---------------------------
# Model 1: single-spin chain
# ---------------------------
def model_1_single_spin(params: IsingParams) -> Dict[State, Distribution]:
    """Return transition distributions for a single-spin chain."""

    beta = 1.0 / max(params.temperature, 1e-6)
    p_up = logistic(2.0 * beta * params.field)
    return {
        (1,): {(1,): p_up, (-1,): 1.0 - p_up},
        (-1,): {(1,): p_up, (-1,): 1.0 - p_up},
    }


def model_1_heatmap_trajectory(
    params: IsingParams,
    steps: int,
    initial_spins: Sequence[int] | None = None,
    n_cols: int = 2,
) -> List[List[List[float]]]:
    """Return model-1 heatmap frames.

    If `initial_spins` is omitted, returns the legacy 1x2 `[P(↓), P(↑)]` strip.
    If `initial_spins` is provided, returns a lattice-shaped trajectory.
    """

    if initial_spins is not None:
        beta = 1.0 / max(params.temperature, 1e-6)
        p_up = logistic(2.0 * beta * params.field)
        eq_spin = 2.0 * p_up - 1.0
        init_vals = [1.0 if s == 1 else -1.0 for s in initial_spins]
        eq_vals = [eq_spin for _ in initial_spins]
        frames: List[List[List[float]]] = [spins_to_grid(init_vals, n_cols=n_cols)]
        for _ in range(steps):
            frames.append(spins_to_grid(eq_vals, n_cols=n_cols))
        return frames

    trans = model_1_single_spin(params)
    dist: Distribution = {(1,): 1.0}
    frames: List[List[List[float]]] = []

    def to_row(d: Distribution) -> List[List[float]]:
        p_up = d.get((1,), 0.0)
        p_down = d.get((-1,), 0.0)
        return [[2.0 * p_down - 1.0, 2.0 * p_up - 1.0]]

    frames.append(to_row(dist))
    for _ in range(steps):
        next_dist: Distribution = defaultdict(float)
        for state, p_state in dist.items():
            for nxt, p_next in trans[state].items():
                next_dist[nxt] += p_state * p_next
        dist = normalize(next_dist)
        frames.append(to_row(dist))
    return frames


# -----------------------------------------
# Model 2: mean-field model on K=#(up spins)
# -----------------------------------------
def model_2_mean_field(
    params: IsingParams,
    current_magnetization: float,
) -> float:
    """Advance mean-field magnetization state by one step.

    If you are looking for the proposal equation written directly in terms of
    (J, T, h) and magnetization m_t, this is the corresponding implementation:
        m_{t+1} = tanh((J * m_t + h) / T)
    implemented numerically as tanh(beta * (J * m_t + h)) with beta = 1/T.
    """

    beta = 1.0 / max(params.temperature * MODEL_2_TEMPERATURE_SCALE, 1e-6)
    return math.tanh(beta * (params.coupling * current_magnetization + params.field))


def model_2_heatmap_trajectory(
    params: IsingParams,
    steps: int,
    n_rows: int = 2,
    n_cols: int = 2,
    initial_magnetization: float = 0.0,
) -> List[List[List[float]]]:
    """Return model-2 heatmap frames by projecting scalar magnetization to a lattice."""

    n_spins = n_rows * n_cols
    trajectory = model_2_magnetization_trajectory(
        params=params,
        steps=steps,
        initial_magnetization=initial_magnetization,
    )
    return [spins_to_grid([magnetization] * n_spins, n_cols=n_cols) for magnetization in trajectory]


def model_2_magnetization_trajectory(
    params: IsingParams,
    steps: int,
    initial_magnetization: float = 0.0,
) -> List[float]:
    """Return model-2 scalar magnetization trajectory."""

    series: List[float] = [max(-1.0, min(1.0, initial_magnetization))]
    for _ in range(steps):
        series.append(model_2_mean_field(params=params, current_magnetization=series[-1]))
    return series


# -------------------------------------------------
# Model 3: local-neighborhood probability evolution
# -------------------------------------------------
def grid_neighbors(index: int, n_rows: int, n_cols: int) -> List[int]:
    """Return 4-neighborhood (without diagonals) on an n_rows x n_cols grid."""

    row, col = divmod(index, n_cols)
    neighbors: List[int] = []
    if row > 0:
        neighbors.append((row - 1) * n_cols + col)
    if row < n_rows - 1:
        neighbors.append((row + 1) * n_cols + col)
    if col > 0:
        neighbors.append(row * n_cols + (col - 1))
    if col < n_cols - 1:
        neighbors.append(row * n_cols + (col + 1))
    return neighbors


def grid_edges(n_rows: int, n_cols: int) -> List[Tuple[int, int]]:
    """Return undirected nearest-neighbor edges for an n_rows x n_cols lattice."""

    edges: List[Tuple[int, int]] = []
    for row in range(n_rows):
        for col in range(n_cols):
            idx = row * n_cols + col
            if row + 1 < n_rows:
                edges.append((idx, (row + 1) * n_cols + col))
            if col + 1 < n_cols:
                edges.append((idx, row * n_cols + (col + 1)))
    return edges


def model_3_local_probabilities(
    current_probs: Sequence[float],
    params: IsingParams,
    mixing: float = 0.2,
    n_rows: int = 2,
    n_cols: int = 2,
) -> List[float]:
    """Advance per-site up-spin probabilities for the local model by one step."""

    if len(current_probs) != n_rows * n_cols:
        raise ValueError("current_probs length must equal n_rows * n_cols")

    beta = 1.0 / max(params.temperature * MODEL_3_TEMPERATURE_SCALE, 1e-6)
    next_probs: List[float] = []
    for i, p_up in enumerate(current_probs):
        neigh = grid_neighbors(i, n_rows=n_rows, n_cols=n_cols)
        neigh_mag = 0.0 if not neigh else sum(2.0 * current_probs[j] - 1.0 for j in neigh) / len(neigh)
        local_field = params.coupling * neigh_mag + params.field
        target = logistic(2.0 * beta * local_field)
        next_probs.append((1.0 - mixing) * p_up + mixing * target)
    return next_probs


def probs_to_state_distribution(probs: Sequence[float]) -> Distribution:
    """Convert independent Bernoulli site probabilities into a full distribution."""

    dist: Distribution = {}
    n = len(probs)
    for bits in itertools.product([-1, 1], repeat=n):
        p = 1.0
        for i, spin in enumerate(bits):
            p *= probs[i] if spin == 1 else (1.0 - probs[i])
        dist[tuple(bits)] = p
    return normalize(dist)


def model_3_heatmap_trajectory(
    initial_probs: Sequence[float],
    params: IsingParams,
    steps: int,
    mixing: float = 0.2,
    n_rows: int = 2,
    n_cols: int = 2,
) -> List[List[List[float]]]:
    """Return trajectory of model-3 expected spins as heatmap frames."""

    if len(initial_probs) != n_rows * n_cols:
        raise ValueError("initial_probs length must equal n_rows * n_cols")

    probs = list(initial_probs)
    frames: List[List[List[float]]] = [spins_to_grid([2.0 * p - 1.0 for p in probs], n_cols=n_cols)]
    for _ in range(steps):
        for __ in range(MODEL_3_TIME_ADJUSTMENT):
            probs = model_3_local_probabilities(
                probs,
                params=params,
                mixing=mixing,
                n_rows=n_rows,
                n_cols=n_cols,
            )
        frames.append(spins_to_grid([2.0 * p - 1.0 for p in probs], n_cols=n_cols))
    return frames


# --------------------------------------------
# Model 4: full exponential state-space (2^N)
# --------------------------------------------
def ising_energy(state: State, params: IsingParams, edges: Sequence[Tuple[int, int]]) -> float:
    """Compute Ising energy for diagnostics/reference."""

    interaction = -params.coupling * sum(state[i] * state[j] for i, j in edges)
    external = -params.field * sum(state)
    return interaction + external


def gibbs_next_distribution(state: State, params: IsingParams, edges: Sequence[Tuple[int, int]]) -> Distribution:
    """Return one-step random-site Gibbs transition distribution from a state.

    This is the state-level single-site Gibbs conditional:
    P(s_i=+1 | neighbors) = logistic(2*beta*(J*sum_neighbors + h)).

    Note: if the proposal equation is the magnetization-only mean-field update
    m_{t+1} = tanh((J*m_t + h)/T), that is implemented by model_2_mean_field.
    """

    n = len(state)
    beta = 1.0 / max(params.temperature, 1e-6)
    dist: Distribution = defaultdict(float)

    for i in range(n):
        local_sum = 0
        for u, v in edges:
            if u == i:
                local_sum += state[v]
            elif v == i:
                local_sum += state[u]

        p_up = logistic(2.0 * beta * (params.coupling * local_sum + params.field))

        up_state = list(state)
        up_state[i] = 1
        down_state = list(state)
        down_state[i] = -1

        dist[tuple(up_state)] += (1.0 / n) * p_up
        dist[tuple(down_state)] += (1.0 / n) * (1.0 - p_up)

    return normalize(dist)


def model_4_full_state_space(
    start: State,
    params: IsingParams,
    edges: Sequence[Tuple[int, int]],
    steps: int,
) -> List[Distribution]:
    """Propagate full-state distribution for model 4."""

    all_states = list(itertools.product([-1, 1], repeat=len(start)))
    current: Distribution = {start: 1.0}
    traj = [current]

    for _ in range(steps):
        for __ in range(MODEL_4_TIME_ADJUSTMENT):
            next_dist: Distribution = {s: 0.0 for s in all_states}
            for state, p_state in current.items():
                trans = gibbs_next_distribution(state, params, edges)
                for next_state, p_next in trans.items():
                    next_dist[next_state] += p_state * p_next
            current = normalize(next_dist)
        traj.append(current)

    return traj


def model_4_heatmap_trajectory(
    start: State,
    params: IsingParams,
    edges: Sequence[Tuple[int, int]],
    steps: int,
    n_cols: int = 2,
) -> List[List[List[float]]]:
    """Return trajectory of model-4 expected spins as heatmap frames."""

    dist_traj = model_4_full_state_space(start=start, params=params, edges=edges, steps=steps)
    return [spins_to_grid(expected_site_magnetization(dist), n_cols=n_cols) for dist in dist_traj]


# ------------------------------------------------------------
# Model 5: restricted-interval affine operator (proposal form)
# ------------------------------------------------------------
def clamp_params_restricted_interval(params: IsingParams) -> IsingParams:
    """Clamp parameters to the model-5 restricted intervals."""

    return IsingParams(
        temperature=max(0.0, min(1.0, params.temperature)),
        coupling=max(-1.0, min(1.0, params.coupling)),
        field=max(-1.0, min(1.0, params.field)),
    )


def model_5_restricted_interval_probabilities(
    current_probs: Sequence[float],
    params: IsingParams,
    n_rows: int = 2,
    n_cols: int = 2,
) -> List[float]:
    """Advance p_i(+1) with the restricted-interval operator from the proposal image."""

    if len(current_probs) != n_rows * n_cols:
        raise ValueError("current_probs length must equal n_rows * n_cols")

    # p = clamp_params_restricted_interval(params)
    j = math.tanh(params.coupling) # [-1, 1] coupling interval implemented by tanh nonlinearity.
    h = math.tanh(params.field * MODEL_5_FIELD_SCALE) # [-1, 1] external field interval implemented by tanh nonlinearity.
    t = logistic(params.temperature * MODEL_5_TEMPERATURE_SCALE) # [0, 1] temperature interval implemented by logistic nonlinearity.
    abs_h = abs(h)

    next_probs: List[float] = []
    for i, p_up_i in enumerate(current_probs):
        p_down_i = 1.0 - p_up_i
        one_block_sum = p_up_i + p_down_i

        one_up = 0.5 * one_block_sum
        one_down = 0.5 * one_block_sum
        h_up = ((1.0 + h) / 2.0) * one_block_sum
        h_down = ((1.0 - h) / 2.0) * one_block_sum

        neighbors = grid_neighbors(i, n_rows=n_rows, n_cols=n_cols) if j != 0.0 else []
        j_star_up = 0.5
        j_star_down = 0.5
        if neighbors:
            acc_up = 0.0
            acc_down = 0.0
            for n_idx in neighbors:
                p_up_j = current_probs[n_idx]
                p_down_j = 1.0 - p_up_j
                acc_up += ((1.0 + j) / 2.0) * p_up_j + ((1.0 - j) / 2.0) * p_down_j
                acc_down += ((1.0 - j) / 2.0) * p_up_j + ((1.0 + j) / 2.0) * p_down_j
            deg = float(len(neighbors))
            j_star_up = acc_up / deg
            j_star_down = acc_down / deg

        next_up = (t / 2.0) * one_up + (1.0 - t) * (abs_h * h_up + (1.0 - abs_h) * j_star_up)
        next_down = (t / 2.0) * one_down + (1.0 - t) * (abs_h * h_down + (1.0 - abs_h) * j_star_down)
        norm = max(1e-12, next_up + next_down)
        next_probs.append(max(0.0, min(1.0, next_up / norm)))
    return next_probs


def model_5_heatmap_trajectory(
    initial_probs: Sequence[float],
    params: IsingParams,
    steps: int,
    n_rows: int = 2,
    n_cols: int = 2,
) -> List[List[List[float]]]:
    """Return trajectory of model-5 expected spins as heatmap frames."""

    probs = list(initial_probs)
    frames: List[List[List[float]]] = [spins_to_grid([2.0 * p - 1.0 for p in probs], n_cols=n_cols)]
    for _ in range(steps):
        probs = model_5_restricted_interval_probabilities(probs, params=params, n_rows=n_rows, n_cols=n_cols)
        frames.append(spins_to_grid([2.0 * p - 1.0 for p in probs], n_cols=n_cols))
    return frames


def print_model_header(name: str) -> None:
    """Pretty-print a section header."""

    print("\n" + "=" * 72)
    print(name)
    print("=" * 72)


def demo(args: argparse.Namespace) -> None:
    """Run command-line demonstration output for all four models."""

    rng = random.Random(args.seed)
    params = IsingParams(temperature=args.temperature, coupling=args.coupling, field=args.field)

    print_model_header("Model 1: Single-spin 2-state chain")
    m1 = model_1_single_spin(params)
    m1_dist = m1[(1,)]
    print("Transition distribution from either state:")
    print(state_probability_bars(m1_dist, top_k=2))
    print(f"Sampled next state: {render_lattice(sample_from_distribution(rng, m1_dist), 1)}")

    print_model_header("Model 2: Mean-field scalar magnetization dynamics")
    magnetization = 0.0
    for step in range(args.steps):
        magnetization = model_2_mean_field(params=params, current_magnetization=magnetization)
        print(f"Step {step + 1:2d}: m={magnetization:.3f}")

    print_model_header("Model 3: Local-neighborhood probability model (2x2 lattice)")
    probs = [0.8, 0.2, 0.5, 0.1]
    for step in range(args.steps):
        probs = model_3_local_probabilities(probs, params=params)
        dist = probs_to_state_distribution(probs)
        sampled = sample_from_distribution(rng, dist)
        print(f"Step {step + 1:2d}: p_up={', '.join(f'{p:.3f}' for p in probs)}")
        print("Top states:")
        print(state_probability_bars(dist, top_k=4))
        print("Sampled lattice:")
        print(render_lattice(sampled, n_cols=2))

    print_model_header("Model 4: Full exponential state-space Gibbs model")
    n_atoms = min(args.exp_atoms, MAX_ATOMS)
    start = tuple([1] * (n_atoms // 2) + [-1] * (n_atoms - n_atoms // 2))
    edges = [(i, (i + 1) % n_atoms) for i in range(n_atoms)] if n_atoms > 1 else []
    traj = model_4_full_state_space(start=start, params=params, edges=edges, steps=args.steps)
    for step, dist in enumerate(traj[1:], start=1):
        sampled = sample_from_distribution(rng, dist)
        print(f"Step {step:2d}: top distribution mass")
        print(state_probability_bars(dist, top_k=min(8, 2**n_atoms)))
        print(f"Sampled next state (N={n_atoms}):")
        print(render_lattice(sampled, n_cols=2 if n_atoms > 1 else 1))


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for the terminal demo script."""

    parser = argparse.ArgumentParser(description="Run four Ising-model demos from the project outline.")
    parser.add_argument("--steps", type=int, default=4, help="Number of simulation steps per model.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for state sampling.")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--coupling", type=float, default=0.8)
    parser.add_argument("--field", type=float, default=0.1)
    parser.add_argument("--mean-field-spins", type=int, default=12)
    parser.add_argument(
        "--exp-atoms",
        type=int,
        default=4,
        help=f"Number of atoms for the exponential model (capped at {MAX_ATOMS} for tractability).",
    )
    return parser


def demo_entry() -> None:
    """Console-script entry point for terminal model demos."""

    demo(build_parser().parse_args())


if __name__ == "__main__":
    demo_entry()
