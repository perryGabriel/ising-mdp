#!/usr/bin/env python3
"""Plot one-at-a-time parameter sweeps across Ising summary trajectories.

Layout: k x 3 subplots where each row is a base parameter triplet and columns are:
1) sweep temperature T at fixed (J, h),
2) sweep field h at fixed (J, T),
3) sweep coupling J at fixed (h, T).
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Dict, List, Sequence, Tuple

SummaryKey = Tuple[str, float, float, float, int]  # model, J, h, T, t
ParamPoint = Tuple[float, float, float]
SeriesByPoint = Dict[Tuple[float, float, float], Dict[int, float]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot one-at-a-time parameter sweeps for summary magnetization.")
    parser.add_argument("--artifact-prefix", default="artifacts", help="Base folder for generated artifacts")
    parser.add_argument("--summary-csv", default=None, help="Path to magnetization_summary.csv")
    parser.add_argument("--output", default=None, help="Output image path")
    parser.add_argument("--reference-model", default="model_1", help="Model used as reference for RMSE in legends")
    parser.add_argument("--models", default="model_1,model_2,model_3,model_4,model_5")
    parser.add_argument("--num-base-points", type=int, default=3, help="Number of base rows k in the kx3 layout")
    return parser.parse_args()


def load_summary(summary_csv: Path) -> Dict[SummaryKey, float]:
    out: Dict[SummaryKey, float] = {}
    with summary_csv.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key: SummaryKey = (
                row["model"],
                float(row["coupling"]),
                float(row["field"]),
                float(row["temperature"]),
                int(row["t"]),
            )
            out[key] = float(row["mean_m"])
    return out


def grouped_by_model_point(data: Dict[SummaryKey, float]) -> Dict[str, SeriesByPoint]:
    grouped: DefaultDict[str, SeriesByPoint] = defaultdict(dict)
    by_series: DefaultDict[Tuple[str, float, float, float], Dict[int, float]] = defaultdict(dict)
    for (model, c, h, temp, t), m in data.items():
        by_series[(model, c, h, temp)][t] = m
    for (model, c, h, temp), series in by_series.items():
        grouped[model][(c, h, temp)] = series
    return dict(grouped)


def steady_state_mean(series: Dict[int, float]) -> float:
    if not series:
        return float("nan")
    ts = sorted(series.keys())
    values = [series[t] for t in ts]
    tail = values[-max(3, len(values) // 5):]
    return sum(tail) / len(tail)


def series_rmse(a: Dict[int, float], b: Dict[int, float]) -> float:
    common_t = sorted(set(a.keys()) & set(b.keys()))
    if not common_t:
        return float("nan")
    mse = sum((a[t] - b[t]) ** 2 for t in common_t) / len(common_t)
    return math.sqrt(mse)


def build_sweep_points(
    series_by_model: Dict[str, SeriesByPoint],
    model: str,
    base: ParamPoint,
    sweep_axis: str,
) -> List[Tuple[float, Dict[int, float]]]:
    c0, h0, t0 = base
    out: List[Tuple[float, Dict[int, float]]] = []
    for (c, h, temp), series in series_by_model.get(model, {}).items():
        if sweep_axis == "temperature" and abs(c - c0) < 1e-9 and abs(h - h0) < 1e-9:
            out.append((temp, series))
        elif sweep_axis == "field" and abs(c - c0) < 1e-9 and abs(temp - t0) < 1e-9:
            out.append((h, series))
        elif sweep_axis == "coupling" and abs(h - h0) < 1e-9 and abs(temp - t0) < 1e-9:
            out.append((c, series))
    out.sort(key=lambda x: x[0])
    return out


def flattened_rmse_vs_reference(
    model_points: List[Tuple[float, Dict[int, float]]],
    reference_points: List[Tuple[float, Dict[int, float]]],
) -> float:
    ref_by_x = {x: series for x, series in reference_points}
    all_sq_err: List[float] = []
    for x, series in model_points:
        if x not in ref_by_x:
            continue
        ref_series = ref_by_x[x]
        common_t = set(series.keys()) & set(ref_series.keys())
        for t in common_t:
            all_sq_err.append((series[t] - ref_series[t]) ** 2)
    if not all_sq_err:
        return float("nan")
    return math.sqrt(sum(all_sq_err) / len(all_sq_err))


def main() -> None:
    args = parse_args()
    summary_csv = (
        Path(args.summary_csv)
        if args.summary_csv
        else Path(args.artifact_prefix) / "data" / "summary" / "magnetization_summary.csv"
    )
    output_path = (
        Path(args.output)
        if args.output
        else Path(args.artifact_prefix) / "plots" / "magnetization_one_at_a_time_sweeps.png"
    )
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    if args.reference_model not in models:
        models = [args.reference_model] + [m for m in models if m != args.reference_model]

    data = load_summary(summary_csv)
    if not data:
        raise SystemExit(f"No rows found in {summary_csv}")
    series_by_model = grouped_by_model_point(data)
    ref_points = sorted(series_by_model.get(args.reference_model, {}).keys())
    if not ref_points:
        raise SystemExit(f"No points found for reference model {args.reference_model}")
    base_points = ref_points[: max(1, args.num_base_points)]

    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise SystemExit("Missing plotting dependency. Install with: pip install matplotlib") from exc

    axes_labels = [("temperature", "T"), ("field", "h"), ("coupling", "J")]
    n_rows = len(base_points)
    fig, axes = plt.subplots(n_rows, 3, figsize=(13, 3.7 * n_rows), constrained_layout=True, sharey=True)
    if n_rows == 1:
        axes_grid = [list(axes)]
    else:
        axes_grid = [list(row) for row in axes]

    for r_idx, base in enumerate(base_points):
        c0, h0, t0 = base
        for c_idx, (axis_name, axis_label) in enumerate(axes_labels):
            ax = axes_grid[r_idx][c_idx]
            ref_sweep = build_sweep_points(series_by_model, args.reference_model, base, axis_name)
            if not ref_sweep:
                ax.text(0.5, 0.5, "no data", ha="center", va="center", transform=ax.transAxes)
                continue

            for model in models:
                points = build_sweep_points(series_by_model, model, base, axis_name)
                if not points:
                    continue
                xs = [x for x, _ in points]
                ys = [steady_state_mean(series) for _, series in points]
                rmse = flattened_rmse_vs_reference(points, ref_sweep)
                if model == args.reference_model:
                    label = f"{model} (RMSE=0)"
                    style = {"linewidth": 2.2, "alpha": 0.95}
                else:
                    label = f"{model} (RMSE={rmse:.3f})" if not math.isnan(rmse) else f"{model} (RMSE=n/a)"
                    style = {"linewidth": 1.6, "alpha": 0.9}
                ax.plot(xs, ys, marker="o", label=label, **style)

            if r_idx == 0:
                ax.set_title(f"Sweep {axis_label}", fontsize=12)
            if c_idx == 0:
                ax.set_ylabel(f"steady m\n(base J={c0:.2f}, h={h0:.2f}, T={t0:.2f})")
            ax.set_xlabel(axis_label)
            ax.grid(alpha=0.2, linewidth=0.6)
            ax.legend(fontsize=7)

    fig.suptitle("One-at-a-time parameter sweeps (reference vs surrogates)", fontsize=13)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    print(f"Wrote one-at-a-time sweep plot to {output_path}")


if __name__ == "__main__":
    main()

