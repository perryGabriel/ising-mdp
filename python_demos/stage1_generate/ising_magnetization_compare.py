#!/usr/bin/env python3
"""Generate cross-model magnetization datasets and summary manifolds.

This script samples trajectories for selected Ising demo models over a grid of
(J, h, T) values and multiple random initializations. It writes:
1) A raw timeseries dataset for m(t), and
2) A grouped mean/variance summary manifold by (model, J, h, T, t).
"""

from __future__ import annotations

import argparse
import csv
import itertools
import random
import time
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Sequence, Tuple

try:
    from python_demos.foundation.ising_four_models import (
        IsingParams,
        grid_edges,
        MAX_ATOMS,
        model_1_heatmap_trajectory,
        model_2_heatmap_trajectory,
        model_3_heatmap_trajectory,
        model_4_heatmap_trajectory,
        model_5_heatmap_trajectory,
    )
except ModuleNotFoundError:
    from python_demos.foundation.ising_four_models import (  # type: ignore
        IsingParams,
        grid_edges,
        MAX_ATOMS,
        model_1_heatmap_trajectory,
        model_2_heatmap_trajectory,
        model_3_heatmap_trajectory,
        model_4_heatmap_trajectory,
        model_5_heatmap_trajectory,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build magnetization comparison datasets across selected models.")
    parser.add_argument("--rows", type=int, default=2, help="Number of grid rows (atoms)")
    parser.add_argument("--cols", type=int, default=3, help="Number of grid columns (atoms)")
    parser.add_argument("--steps", type=int, default=20, help="Number of time steps")
    parser.add_argument("--seeds", type=int, default=20, help="Number of seeded initializations per parameter point")

    parser.add_argument("--j-min", type=float, default=0.1, help="Min coupling strength J")
    parser.add_argument("--j-max", type=float, default=1.0, help="Max coupling strength J")
    parser.add_argument("--j-count", type=int, default=3, help="Number of J values to sample")

    parser.add_argument("--h-min", type=float, default=-0.4, help="Min external field h")
    parser.add_argument("--h-max", type=float, default=0.4, help="Max external field h")
    parser.add_argument("--h-count", type=int, default=3, help="Number of h values to sample")

    parser.add_argument("--temp-min", type=float, default=0.6, help="Min temperature")
    parser.add_argument("--temp-max", type=float, default=2.0, help="Max temperature")
    parser.add_argument("--temp-count", type=int, default=3, help="Number of temperature values to sample")

    parser.add_argument("--mixing", type=float, default=0.2, help="Mixing parameter for model 3 (between 0 and 1)")
    parser.add_argument(
        "--models",
        default="1,2,3,4,5",
        help="Comma-separated model ids to include (subset of 1,2,3,4,5).",
    )

    parser.add_argument("--artifact-prefix", default="artifacts", help="Base folder for generated artifacts")
    parser.add_argument("--output-raw", default=None, help="Output file for raw timeseries data")
    parser.add_argument("--output-summary", default=None, help="Output file for summary manifold data")
    return parser.parse_args()


def linspace(lo: float, hi: float, n: int) -> List[float]:
    if n <= 1:
        return [lo]
    step = (hi - lo) / (n - 1)
    return [lo + i * step for i in range(n)]


def mean_grid_value(frame: Sequence[Sequence[float]]) -> float:
    vals = [v for row in frame for v in row]
    return sum(vals) / max(1, len(vals))


def trajectory_magnetizations(
    params: IsingParams,
    rows: int,
    cols: int,
    steps: int,
    seed: int,
    mixing: float,
    selected_models: Sequence[str],
) -> Tuple[Dict[str, List[float]], Dict[str, float], int, float]:
    n_atoms = rows * cols
    rng = random.Random(seed)
    start = tuple(rng.choice([-1, 1]) for _ in range(n_atoms))
    initial_probs = [1.0 if s == 1 else 0.0 for s in start]
    edges = grid_edges(rows, cols)

    trajectories: Dict[str, List[float]] = {}
    runtimes: Dict[str, float] = {}
    if "1" in selected_models:
        started = time.perf_counter()
        model1 = model_1_heatmap_trajectory(params=params, steps=steps, initial_spins=start, n_cols=cols)
        trajectories["model_1"] = [mean_grid_value(frame) for frame in model1]
        runtimes["model_1"] = time.perf_counter() - started
    if "2" in selected_models:
        started = time.perf_counter()
        model2 = model_2_heatmap_trajectory(
            n_spins=n_atoms,
            params=params,
            steps=steps,
            n_rows=rows,
            n_cols=cols,
            initial_k_dist={sum(1 for s in start if s == 1): 1.0},
        )
        trajectories["model_2"] = [mean_grid_value(frame) for frame in model2]
        runtimes["model_2"] = time.perf_counter() - started
    if "3" in selected_models:
        started = time.perf_counter()
        model3 = model_3_heatmap_trajectory(
            initial_probs=initial_probs,
            params=params,
            steps=steps,
            mixing=mixing,
            n_rows=rows,
            n_cols=cols,
        )
        trajectories["model_3"] = [mean_grid_value(frame) for frame in model3]
        runtimes["model_3"] = time.perf_counter() - started
    if "4" in selected_models:
        started = time.perf_counter()
        model4 = model_4_heatmap_trajectory(start=start, params=params, edges=edges, steps=steps, n_cols=cols)
        trajectories["model_4"] = [mean_grid_value(frame) for frame in model4]
        runtimes["model_4"] = time.perf_counter() - started
    if "5" in selected_models:
        started = time.perf_counter()
        model5 = model_5_heatmap_trajectory(
            initial_probs=initial_probs,
            params=params,
            steps=steps,
            n_rows=rows,
            n_cols=cols,
        )
        trajectories["model_5"] = [mean_grid_value(frame) for frame in model5]
        runtimes["model_5"] = time.perf_counter() - started
    up_count = sum(1 for s in start if s == 1)
    up_fraction = up_count / n_atoms
    return trajectories, runtimes, up_count, up_fraction


def write_raw(path: Path, rows: Iterable[Dict[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "model",
        "coupling",
        "field",
        "temperature",
        "seed",
        "initial_up_count",
        "initial_up_fraction",
        "t",
        "m",
        "runtime_seconds",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_summary(path: Path, raw_rows: Sequence[Dict[str, float]]) -> None:
    grouped: Dict[Tuple[str, float, float, float, int], List[float]] = defaultdict(list)
    for row in raw_rows:
        key = (
            str(row["model"]),
            float(row["coupling"]),
            float(row["field"]),
            float(row["temperature"]),
            int(row["t"]),
        )
        grouped[key].append(float(row["m"]))

    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["model", "coupling", "field", "temperature", "t", "mean_m", "var_m", "n"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for key in sorted(grouped.keys()):
            values = grouped[key]
            mu = mean(values)
            var = mean([(v - mu) ** 2 for v in values]) if values else 0.0
            model, coupling, field, temperature, t = key
            writer.writerow(
                {
                    "model": model,
                    "coupling": coupling,
                    "field": field,
                    "temperature": temperature,
                    "t": t,
                    "mean_m": mu,
                    "var_m": var,
                    "n": len(values),
                }
            )


def main() -> None:
    args = parse_args()

    output_raw = (
        Path(args.output_raw)
        if args.output_raw
        else Path(args.artifact_prefix) / "data" / "raw" / "magnetization_timeseries.csv"
    )
    output_summary = (
        Path(args.output_summary)
        if args.output_summary
        else Path(args.artifact_prefix) / "data" / "summary" / "magnetization_summary.csv"
    )

    selected_models = [m.strip() for m in args.models.split(",") if m.strip()]
    if not selected_models or any(m not in {"1", "2", "3", "4", "5"} for m in selected_models):
        raise SystemExit("--models must be a comma-separated subset of {1,2,3,4,5}")

    if args.rows <= 0 or args.cols <= 0:
        raise SystemExit("--rows and --cols must be positive")
    if "4" in selected_models and args.rows * args.cols > MAX_ATOMS:
        raise SystemExit(f"rows*cols must be <= {MAX_ATOMS} for tractable full-state model trajectories")

    j_values = linspace(args.j_min, args.j_max, args.j_count)
    h_values = linspace(args.h_min, args.h_max, args.h_count)
    temp_values = linspace(args.temp_min, args.temp_max, args.temp_count)

    raw_rows: List[Dict[str, float]] = []
    total_jobs = len(j_values) * len(h_values) * len(temp_values) * args.seeds
    job_idx = 0

    for coupling, field, temperature in itertools.product(j_values, h_values, temp_values):
        params = IsingParams(temperature=temperature, coupling=coupling, field=field)
        for seed in range(args.seeds):
            job_idx += 1
            traj, runtimes, up_count, up_fraction = trajectory_magnetizations(
                params=params,
                rows=args.rows,
                cols=args.cols,
                steps=args.steps,
                seed=seed,
                mixing=args.mixing,
                selected_models=selected_models,
            )
            for model_name, series in traj.items():
                for t, m in enumerate(series):
                    raw_rows.append(
                        {
                            "model": model_name,
                            "coupling": coupling,
                            "field": field,
                            "temperature": temperature,
                            "seed": seed,
                            "initial_up_count": up_count,
                            "initial_up_fraction": up_fraction,
                            "t": t,
                            "m": m,
                            "runtime_seconds": runtimes.get(model_name, float("nan")),
                        }
                    )

            if job_idx % max(1, total_jobs // 10) == 0:
                print(f"Progress: {job_idx}/{total_jobs} parameter-seed runs")

    write_raw(output_raw, raw_rows)
    write_summary(output_summary, raw_rows)

    print(f"Wrote raw trajectories to {output_raw}")
    print(f"Wrote summary manifold to {output_summary}")


if __name__ == "__main__":
    main()
