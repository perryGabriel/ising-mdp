#!/usr/bin/env python3
"""Explicit renormalization-operator demonstration.

Compares two workflows from a shared initial state:
A) evolve full-state model then project to mean magnetization m_t,
B) project to a coarse mean-field state first, then evolve coarse dynamics.

Outputs a CSV with per-time residuals and optionally plots both trajectories.
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from python_demos.foundation.ising_four_models import (
        IsingParams,
        Distribution,
        grid_edges,
        model_2_mean_field,
        model_4_full_state_space,
    )
except ModuleNotFoundError:
    from python_demos.foundation.ising_four_models import (  # type: ignore
        IsingParams,
        Distribution,
        grid_edges,
        model_2_mean_field,
        model_4_full_state_space,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Demonstrate projection/evolution order for renormalization.")
    parser.add_argument("--artifact-prefix", default="artifacts", help="Base folder for generated artifacts")
    parser.add_argument("--rows", type=int, default=4)
    parser.add_argument("--cols", type=int, default=4)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--coupling", type=float, default=0.8)
    parser.add_argument("--field", type=float, default=0.1)
    parser.add_argument("--output-csv", default=None)
    parser.add_argument("--output-plot", default=None)
    parser.add_argument("--no-plot", action="store_true")
    return parser


def project_dist_to_mean_m(dist: Distribution) -> float:
    if not dist:
        return 0.0
    n = len(next(iter(dist.keys())))
    return sum((sum(state) / n) * p for state, p in dist.items())


def coarse_evolution_from_m0(n_spins: int, params: IsingParams, m0: float, steps: int) -> List[float]:
    expected_k0 = (m0 * n_spins + n_spins) / 2.0
    k_low = max(0, min(n_spins, int(expected_k0)))
    k_dist: Dict[int, float] = {k_low: 1.0}

    series = [m0]
    for _ in range(steps):
        k_dist = model_2_mean_field(n_spins=n_spins, params=params, current_k_dist=k_dist)
        m = sum(((2 * k - n_spins) / n_spins) * p for k, p in k_dist.items())
        series.append(m)
    return series


def main() -> None:
    args = build_parser().parse_args()

    output_csv = (
        Path(args.output_csv)
        if args.output_csv
        else Path(args.artifact_prefix) / "operator" / "renormalization_operator.csv"
    )
    output_plot = (
        Path(args.output_plot)
        if args.output_plot
        else Path(args.artifact_prefix) / "operator" / "renormalization_operator.png"
    )

    if args.rows <= 0 or args.cols <= 0:
        raise SystemExit("--rows and --cols must be positive")
    if args.rows * args.cols > 9:
        raise SystemExit("rows*cols must be <= 9 for tractable full-state evolution")

    n_atoms = args.rows * args.cols
    rng = random.Random(args.seed)
    start = tuple(rng.choice([-1, 1]) for _ in range(n_atoms))

    params = IsingParams(temperature=args.temperature, coupling=args.coupling, field=args.field)
    edges = grid_edges(args.rows, args.cols)

    # Path A: evolve full state, then project each step.
    full_traj = model_4_full_state_space(start=start, params=params, edges=edges, steps=args.steps)
    path_a = [project_dist_to_mean_m(dist) for dist in full_traj]

    # Path B: project initial condition to coarse state, then evolve coarse model.
    m0 = sum(start) / len(start)
    path_b = coarse_evolution_from_m0(n_spins=n_atoms, params=params, m0=m0, steps=args.steps)

    rows = []
    for t in range(args.steps + 1):
        residual = abs(path_a[t] - path_b[t])
        rows.append(
            {
                "t": t,
                "m_full_then_project": path_a[t],
                "m_project_then_coarse": path_b[t],
                "abs_residual": residual,
            }
        )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["t", "m_full_then_project", "m_project_then_coarse", "abs_residual"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    mean_residual = sum(row["abs_residual"] for row in rows) / len(rows)
    print(f"Start state: {start}")
    print(f"Wrote operator comparison CSV to {output_csv}")
    print(f"Mean absolute residual over time: {mean_residual:.6f}")

    if args.no_plot:
        return

    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise SystemExit("Missing plotting dependency. Install with: pip install matplotlib") from exc

    ts = [row["t"] for row in rows]
    a = [row["m_full_then_project"] for row in rows]
    b = [row["m_project_then_coarse"] for row in rows]
    r = [row["abs_residual"] for row in rows]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    axes[0].plot(ts, a, label="Evolve full → Project", color="tab:blue")
    axes[0].plot(ts, b, label="Project → Evolve coarse", color="tab:orange", linestyle="--")
    axes[0].set_title("Renormalization operator comparison")
    axes[0].set_xlabel("t")
    axes[0].set_ylabel("m")
    axes[0].legend(fontsize=8)

    axes[1].plot(ts, r, color="tab:red")
    axes[1].set_title("|residual| over time")
    axes[1].set_xlabel("t")
    axes[1].set_ylabel("|Δm|")

    output_plot.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_plot, dpi=170)
    plt.close(fig)
    print(f"Wrote operator comparison plot to {output_plot}")


if __name__ == "__main__":
    main()
