#!/usr/bin/env python3
"""Visualize trajectory matching using learned parameter maps.

Given raw/summary manifold CSVs and a fitted parameter-map CSV, this script:
1) Finds mapped target parameters for a chosen source parameter point.
2) Selects trajectories with similar initial spin-up fractions.
3) Plots per-seed trajectories + mean bands for source and mapped target models.
4) Plots evaluation artifacts (fit-error histogram and time-resolved manifold residual).
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Dict, List, Tuple

RawKey = Tuple[str, float, float, float, int]  # model, J, h, T, seed
SummaryKey = Tuple[str, float, float, float, int]  # model, J, h, T, t


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualize trajectory matching and mapping artifacts.")
    parser.add_argument("--artifact-prefix", default="artifacts", help="Base folder for generated artifacts")
    parser.add_argument("--raw-csv", default=None)
    parser.add_argument("--summary-csv", default=None)
    parser.add_argument("--map-csv", default=None)

    parser.add_argument("--source-model", default="model_1")
    parser.add_argument("--target-model", default="model_2")
    parser.add_argument("--coupling", type=float, required=True)
    parser.add_argument("--field", type=float, required=True)
    parser.add_argument("--temperature", type=float, required=True)

    parser.add_argument("--init-up-frac", type=float, default=None, help="Target initial up-spin fraction (0..1)")
    parser.add_argument("--init-up-frac-tol", type=float, default=0.15)
    parser.add_argument("--max-seeds", type=int, default=12)

    parser.add_argument("--output-traj", default=None)
    parser.add_argument("--output-artifacts", default=None)
    return parser.parse_args()


def nearest_map_row(map_csv: Path, source_c: float, source_h: float, source_t: float) -> Dict[str, float]:
    best = None
    best_dist = float("inf")
    with map_csv.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sc = float(row["source_coupling"])
            sh = float(row["source_field"])
            st = float(row["source_temperature"])
            d = (sc - source_c) ** 2 + (sh - source_h) ** 2 + (st - source_t) ** 2
            if d < best_dist:
                best_dist = d
                best = {k: float(v) for k, v in row.items()}
    if best is None:
        raise SystemExit(f"No rows found in {map_csv}")
    return best


def load_raw(raw_csv: Path) -> Tuple[Dict[RawKey, Dict[int, float]], Dict[RawKey, float]]:
    series: Dict[RawKey, Dict[int, float]] = defaultdict(dict)
    init_frac: Dict[RawKey, float] = {}
    with raw_csv.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key: RawKey = (
                row["model"],
                float(row["coupling"]),
                float(row["field"]),
                float(row["temperature"]),
                int(row["seed"]),
            )
            t = int(row["t"])
            series[key][t] = float(row["m"])
            if "initial_up_fraction" in row and row["initial_up_fraction"] != "":
                init_frac[key] = float(row["initial_up_fraction"])
            elif t == 0:
                init_frac[key] = (float(row["m"]) + 1.0) / 2.0
    return series, init_frac


def load_summary(summary_csv: Path) -> Dict[SummaryKey, Tuple[float, float]]:
    out: Dict[SummaryKey, Tuple[float, float]] = {}
    with summary_csv.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key: SummaryKey = (
                row["model"],
                float(row["coupling"]),
                float(row["field"]),
                float(row["temperature"]),
                int(row["t"]),
            )
            out[key] = (float(row["mean_m"]), float(row["var_m"]))
    return out


def select_seed_keys(
    all_series: Dict[RawKey, Dict[int, float]],
    init_frac: Dict[RawKey, float],
    model: str,
    c: float,
    h: float,
    temp: float,
    target_init_frac: float,
    tol: float,
    max_seeds: int,
) -> List[RawKey]:
    candidates = [
        key
        for key in all_series.keys()
        if key[0] == model and abs(key[1] - c) < 1e-9 and abs(key[2] - h) < 1e-9 and abs(key[3] - temp) < 1e-9
    ]
    candidates.sort(key=lambda k: abs(init_frac.get(k, 0.5) - target_init_frac))
    filtered = [k for k in candidates if abs(init_frac.get(k, 0.5) - target_init_frac) <= tol]
    return filtered[:max_seeds]


def mean_series(keys: List[RawKey], all_series: Dict[RawKey, Dict[int, float]]) -> Tuple[List[int], List[float]]:
    if not keys:
        return [], []
    common_t = sorted(set.intersection(*(set(all_series[k].keys()) for k in keys)))
    mu = [mean([all_series[k][t] for k in keys]) for t in common_t]
    return common_t, mu


def main() -> None:
    args = parse_args()

    raw_csv = (
        Path(args.raw_csv)
        if args.raw_csv
        else Path(args.artifact_prefix) / "data" / "raw" / "magnetization_timeseries.csv"
    )
    summary_csv = (
        Path(args.summary_csv)
        if args.summary_csv
        else Path(args.artifact_prefix) / "data" / "summary" / "magnetization_summary.csv"
    )
    map_csv = Path(args.map_csv) if args.map_csv else Path(args.artifact_prefix) / "maps" / "parameter_map.csv"
    output_traj = (
        Path(args.output_traj)
        if args.output_traj
        else Path(args.artifact_prefix) / "plots" / "trajectory_matching.png"
    )
    output_artifacts = (
        Path(args.output_artifacts)
        if args.output_artifacts
        else Path(args.artifact_prefix) / "plots" / "matching_artifacts.png"
    )

    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise SystemExit("Missing plotting dependency. Install with: pip install matplotlib") from exc

    map_row = nearest_map_row(map_csv, args.coupling, args.field, args.temperature)
    target_c = map_row["target_coupling"]
    target_h = map_row["target_field"]
    target_t = map_row["target_temperature"]

    print("Mapped parameter report")
    print(
        f"  source ({args.source_model}): J={args.coupling:.3f}, h={args.field:.3f}, T={args.temperature:.3f}"
    )
    print(f"  target ({args.target_model}): J={target_c:.3f}, h={target_h:.3f}, T={target_t:.3f}")
    print(f"  fit error (nearest map row): {map_row['fit_error']:.6f}")

    raw, init_frac = load_raw(raw_csv)
    summary = load_summary(summary_csv)

    if args.init_up_frac is None:
        source_seed_keys = [
            key
            for key in raw.keys()
            if key[0] == args.source_model
            and abs(key[1] - args.coupling) < 1e-9
            and abs(key[2] - args.field) < 1e-9
            and abs(key[3] - args.temperature) < 1e-9
        ]
        source_seed_keys = source_seed_keys[:1]
        target_init_frac = init_frac.get(source_seed_keys[0], 0.5) if source_seed_keys else 0.5
    else:
        target_init_frac = args.init_up_frac

    source_keys = select_seed_keys(
        all_series=raw,
        init_frac=init_frac,
        model=args.source_model,
        c=args.coupling,
        h=args.field,
        temp=args.temperature,
        target_init_frac=target_init_frac,
        tol=args.init_up_frac_tol,
        max_seeds=args.max_seeds,
    )
    target_keys = select_seed_keys(
        all_series=raw,
        init_frac=init_frac,
        model=args.target_model,
        c=target_c,
        h=target_h,
        temp=target_t,
        target_init_frac=target_init_frac,
        tol=args.init_up_frac_tol,
        max_seeds=args.max_seeds,
    )

    if not source_keys or not target_keys:
        raise SystemExit(
            "No matching seed trajectories found; increase --init-up-frac-tol or regenerate raw CSV with more seeds."
        )

    # Plot seed-level trajectories + mean lines.
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)
    for key in source_keys:
        ts = sorted(raw[key].keys())
        ys = [raw[key][t] for t in ts]
        axes[0].plot(ts, ys, alpha=0.25, color="tab:blue")
    for key in target_keys:
        ts = sorted(raw[key].keys())
        ys = [raw[key][t] for t in ts]
        axes[1].plot(ts, ys, alpha=0.25, color="tab:orange")

    ts_s, mu_s = mean_series(source_keys, raw)
    ts_t, mu_t = mean_series(target_keys, raw)
    axes[0].plot(ts_s, mu_s, color="tab:blue", linewidth=2.5, label=f"mean {args.source_model}")
    axes[1].plot(ts_t, mu_t, color="tab:orange", linewidth=2.5, label=f"mean {args.target_model}")

    axes[0].set_title(
        f"Source: {args.source_model}\nJ={args.coupling:.2f}, h={args.field:.2f}, T={args.temperature:.2f}"
    )
    axes[1].set_title(f"Mapped target: {args.target_model}\nJ={target_c:.2f}, h={target_h:.2f}, T={target_t:.2f}")
    for ax in axes:
        ax.set_xlabel("t")
        ax.set_ylabel("m")
        ax.set_ylim(-1.05, 1.05)

    fig.suptitle(
        f"Trajectories with similar initial up-fraction (~{target_init_frac:.2f}, tol={args.init_up_frac_tol:.2f})",
        fontsize=11,
    )
    output_traj.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_traj, dpi=170)
    plt.close(fig)

    # Plot evaluation artifacts.
    map_rows = []
    with map_csv.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            map_rows.append({k: float(v) for k, v in row.items()})

    artifact_fig, artifact_axes = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)

    errors = [row["fit_error"] for row in map_rows]
    artifact_axes[0].hist(errors, bins=12, color="tab:purple", alpha=0.8)
    artifact_axes[0].set_title("Map fit-error distribution")
    artifact_axes[0].set_xlabel("fit error")
    artifact_axes[0].set_ylabel("count")

    src_series = {
        t: summary[(args.source_model, args.coupling, args.field, args.temperature, t)][0]
        for (model, c, h, temp, t) in summary.keys()
        if model == args.source_model and abs(c - args.coupling) < 1e-9 and abs(h - args.field) < 1e-9 and abs(temp - args.temperature) < 1e-9
    }
    dst_series = {
        t: summary[(args.target_model, target_c, target_h, target_t, t)][0]
        for (model, c, h, temp, t) in summary.keys()
        if model == args.target_model and abs(c - target_c) < 1e-9 and abs(h - target_h) < 1e-9 and abs(temp - target_t) < 1e-9
    }
    common_t = sorted(set(src_series.keys()) & set(dst_series.keys()))
    residual = [abs(src_series[t] - dst_series[t]) for t in common_t]
    artifact_axes[1].plot(common_t, residual, marker="o", color="tab:red")
    artifact_axes[1].set_title("|mean-m residual| over time")
    artifact_axes[1].set_xlabel("t")
    artifact_axes[1].set_ylabel("absolute residual")

    output_artifacts.parent.mkdir(parents=True, exist_ok=True)
    artifact_fig.savefig(output_artifacts, dpi=170)
    plt.close(artifact_fig)

    print(f"Wrote trajectory comparison plot to {output_traj}")
    print(f"Wrote evaluation artifact plot to {output_artifacts}")


if __name__ == "__main__":
    main()
