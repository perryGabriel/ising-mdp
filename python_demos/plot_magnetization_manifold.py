#!/usr/bin/env python3
"""Plot trajectory bands and residual maps from manifold CSV outputs."""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot manifold trajectory bands and parameter-map residuals.")
    parser.add_argument("--summary-csv", default="python_demos/magnetization_summary.csv")
    parser.add_argument("--map-csv", default="python_demos/parameter_map.csv")

    parser.add_argument("--coupling", type=float, default=0.7)
    parser.add_argument("--field", type=float, default=0.0)
    parser.add_argument("--temperature", type=float, default=1.0)

    parser.add_argument("--source-model", default="model_1")
    parser.add_argument("--target-model", default="model_2")

    parser.add_argument("--output-traj", default="python_demos/magnetization_trajectory_bands.png")
    parser.add_argument("--output-residual", default="python_demos/magnetization_residual_map.png")
    return parser.parse_args()


def load_summary(path: Path) -> Dict[Tuple[str, float, float, float], Dict[int, Tuple[float, float]]]:
    data: Dict[Tuple[str, float, float, float], Dict[int, Tuple[float, float]]] = defaultdict(dict)
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (
                row["model"],
                float(row["coupling"]),
                float(row["field"]),
                float(row["temperature"]),
            )
            t = int(row["t"])
            data[key][t] = (float(row["mean_m"]), float(row["var_m"]))
    return data


def nearest_params(data: Dict[Tuple[str, float, float, float], Dict[int, Tuple[float, float]]], model: str, c: float, h: float, temp: float) -> Tuple[float, float, float]:
    candidates = [k[1:] for k in data.keys() if k[0] == model]
    if not candidates:
        raise ValueError(f"No entries for model {model}")
    return min(candidates, key=lambda p: (p[0] - c) ** 2 + (p[1] - h) ** 2 + (p[2] - temp) ** 2)


def plot_trajectory_bands(summary_csv: Path, coupling: float, field: float, temperature: float, output_path: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise SystemExit("Missing plotting dependency. Install with: pip install matplotlib") from exc

    data = load_summary(summary_csv)
    models = sorted({key[0] for key in data.keys()})

    fig, ax = plt.subplots(figsize=(10, 5), constrained_layout=True)
    for model in models:
        c_star, h_star, t_star = nearest_params(data, model, coupling, field, temperature)
        series = data[(model, c_star, h_star, t_star)]
        ts = sorted(series.keys())
        means = [series[t][0] for t in ts]
        stds = [math.sqrt(max(series[t][1], 0.0)) for t in ts]
        lo = [m - s for m, s in zip(means, stds)]
        hi = [m + s for m, s in zip(means, stds)]

        ax.plot(ts, means, label=f"{model} @ ({c_star:.2f},{h_star:.2f},{t_star:.2f})")
        ax.fill_between(ts, lo, hi, alpha=0.2)

    ax.set_title("Magnetization trajectory bands (mean ± std)")
    ax.set_xlabel("t")
    ax.set_ylabel("m")
    ax.legend(fontsize=8)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def plot_residual_map(map_csv: Path, source_model: str, target_model: str, output_path: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise SystemExit("Missing plotting dependency. Install with: pip install matplotlib") from exc

    rows: List[Dict[str, float]] = []
    with map_csv.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append({k: float(v) for k, v in row.items()})

    if not rows:
        raise SystemExit(f"No rows found in {map_csv}")

    # Average residuals over temperature for each (J,h) source point.
    by_jh: Dict[Tuple[float, float], List[float]] = defaultdict(list)
    for row in rows:
        key = (row["source_coupling"], row["source_field"])
        by_jh[key].append(row["fit_error"])

    couplings = sorted({key[0] for key in by_jh.keys()})
    fields = sorted({key[1] for key in by_jh.keys()})
    grid = [[0.0 for _ in fields] for _ in couplings]
    for i, c in enumerate(couplings):
        for j, h in enumerate(fields):
            vals = by_jh.get((c, h), [])
            grid[i][j] = sum(vals) / max(1, len(vals))

    fig, ax = plt.subplots(figsize=(6, 5), constrained_layout=True)
    im = ax.imshow(grid, origin="lower", aspect="auto", cmap="viridis")
    ax.set_title(f"Residual map: {source_model} → {target_model}")
    ax.set_xlabel("source field h")
    ax.set_ylabel("source coupling J")
    ax.set_xticks(range(len(fields)))
    ax.set_xticklabels([f"{v:.2f}" for v in fields], rotation=45, ha="right")
    ax.set_yticks(range(len(couplings)))
    ax.set_yticklabels([f"{v:.2f}" for v in couplings])
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("mean fit error")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    plot_trajectory_bands(
        summary_csv=Path(args.summary_csv),
        coupling=args.coupling,
        field=args.field,
        temperature=args.temperature,
        output_path=Path(args.output_traj),
    )
    plot_residual_map(
        map_csv=Path(args.map_csv),
        source_model=args.source_model,
        target_model=args.target_model,
        output_path=Path(args.output_residual),
    )

    print(f"Wrote trajectory plot to {args.output_traj}")
    print(f"Wrote residual map to {args.output_residual}")


if __name__ == "__main__":
    main()
