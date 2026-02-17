#!/usr/bin/env python3
"""Core simulation and visualization helpers for four Ising-inspired models."""

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


def random_initial_probabilities(n_atoms: int, seed: int = 7) -> List[float]:
    """Generate reproducible per-site up-spin probabilities in [0, 1]."""

    rng = random.Random(seed)
    return [rng.random() for _ in range(n_atoms)]


def sample_state_from_probabilities(initial_probs: Sequence[float], seed: int = 7) -> State:
    """Sample a concrete spin state from per-site up-spin probabilities."""

    rng = random.Random(seed)
    return tuple(1 if rng.random() <= p else -1 for p in initial_probs)


def initial_k_distribution(initial_probs: Sequence[float]) -> Dict[int, float]:
    """Compute P(K=k) from independent Bernoulli site probabilities."""

    dist: Dict[int, float] = {0: 1.0}
    for p in initial_probs:
        nxt: Dict[int, float] = defaultdict(float)
        for k, mass in dist.items():
            nxt[k] += mass * (1.0 - p)
            nxt[k + 1] += mass * p
        dist = dict(nxt)
    total = sum(dist.values())
    return {k: v / total for k, v in dist.items()}


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
    initial_probs: Sequence[float], params: IsingParams, steps: int, n_cols: int = 2
) -> List[List[List[float]]]:
    """Return model-1 lattice heatmap frames from shared site initialization.

    Each site follows the same independent single-spin chain dynamics.
    """

    trans = model_1_single_spin(params)
    probs = list(initial_probs)
    frames: List[List[List[float]]] = [spins_to_grid([2.0 * p - 1.0 for p in probs], n_cols=n_cols)]
    p_up_after = trans[(1,)][(1,)]
    for _ in range(steps):
        probs = [p * p_up_after + (1.0 - p) * p_up_after for p in probs]
        frames.append(spins_to_grid([2.0 * p - 1.0 for p in probs], n_cols=n_cols))
    return frames


# -----------------------------------------
# Model 2: mean-field model on K=#(up spins)
# -----------------------------------------
def model_2_mean_field(
    n_spins: int,
    params: IsingParams,
    current_k_dist: Dict[int, float],
) -> Dict[int, float]:
    """Advance mean-field distribution over K=#up by one step."""

    beta = 1.0 / max(params.temperature, 1e-6)
    next_dist: Dict[int, float] = defaultdict(float)

    for k, pk in current_k_dist.items():
        magnetization = (2 * k - n_spins) / n_spins
        mean_field = params.coupling * magnetization + params.field
        p_up_if_flipped = logistic(2.0 * beta * mean_field)

        p_pick_up = k / n_spins
        p_pick_down = 1.0 - p_pick_up

        if k > 0:
            next_dist[k] += pk * p_pick_up * p_up_if_flipped
            next_dist[k - 1] += pk * p_pick_up * (1.0 - p_up_if_flipped)

        if k < n_spins:
            next_dist[k + 1] += pk * p_pick_down * p_up_if_flipped
            next_dist[k] += pk * p_pick_down * (1.0 - p_up_if_flipped)

    total = sum(next_dist.values())
    return {k: v / total for k, v in next_dist.items()}


def model_2_heatmap_trajectory(
    n_spins: int,
    params: IsingParams,
    steps: int,
    initial_probs: Sequence[float],
    n_cols: int = 2,
) -> List[List[List[float]]]:
    """Return model-2 heatmap frames mapped onto the shared lattice arrangement.

    Model 2 tracks only K=#up. We convert each step to one expected magnetization
    value and fill all sites with it, so layout matches other panels.
    """

    k_dist = initial_k_distribution(initial_probs)

    def mean_magnetization(dist: Dict[int, float]) -> float:
        exp_k = sum(k * p for k, p in dist.items())
        return (2.0 * exp_k / n_spins) - 1.0

    frames: List[List[List[float]]] = []
    frames.append(spins_to_grid([mean_magnetization(k_dist)] * n_spins, n_cols=n_cols))
    for _ in range(steps):
        k_dist = model_2_mean_field(n_spins=n_spins, params=params, current_k_dist=k_dist)
        frames.append(spins_to_grid([mean_magnetization(k_dist)] * n_spins, n_cols=n_cols))
    return frames


# -------------------------------------------------
# Model 3: local-neighborhood probability evolution
# -------------------------------------------------
def neighbors_2x2(index: int) -> List[int]:
    """Return 4-neighborhood (without diagonals) on a 2x2 grid index."""

    if index == 0:
        return [1, 2]
    if index == 1:
        return [0, 3]
    if index == 2:
        return [0, 3]
    return [1, 2]


def model_3_local_probabilities(
    current_probs: Sequence[float],
    params: IsingParams,
    mixing: float = 0.2,
    n_cols: int = 2,
) -> List[float]:
    """Advance per-site up-spin probabilities for the local model by one step."""

    # Local-neighborhood approximation currently implemented for 2x2 layout.
    if len(current_probs) != 4 or n_cols != 2:
        raise ValueError("Model 3 currently supports a 2x2 lattice (4 atoms) only.")

    beta = 1.0 / max(params.temperature, 1e-6)
    next_probs: List[float] = []
    for i, p_up in enumerate(current_probs):
        neigh = neighbors_2x2(i)
        neigh_mag = sum(2.0 * current_probs[j] - 1.0 for j in neigh) / len(neigh)
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
    n_cols: int = 2,
) -> List[List[List[float]]]:
    """Return trajectory of model-3 expected spins as heatmap frames."""

    probs = list(initial_probs)
    frames: List[List[List[float]]] = [spins_to_grid([2.0 * p - 1.0 for p in probs], n_cols=n_cols)]
    for _ in range(steps):
        probs = model_3_local_probabilities(probs, params=params, mixing=mixing, n_cols=n_cols)
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
    """Return one-step random-site Gibbs transition distribution from a state."""

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

    print_model_header("Model 2: Mean-field chain over K=#(up spins)")
    n_spins = args.mean_field_spins
    k_dist = {n_spins // 2: 1.0}
    for step in range(args.steps):
        k_dist = model_2_mean_field(n_spins=n_spins, params=params, current_k_dist=k_dist)
        top = sorted(k_dist.items(), key=lambda kv: kv[1], reverse=True)[:5]
        print(f"Step {step + 1:2d}: " + ", ".join(f"K={k}: {p:.3f}" for k, p in top))

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
    n_atoms = min(args.exp_atoms, 4)
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
        help="Number of atoms for the exponential model (capped at 4 for tractability).",
    )
    return parser


def demo_entry() -> None:
    """Console-script entry point for terminal model demos."""

    demo(build_parser().parse_args())


if __name__ == "__main__":
    demo_entry()
