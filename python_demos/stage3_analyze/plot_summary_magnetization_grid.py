#!/usr/bin/env python3
"""Plot summary magnetization manifold as a model-by-parameter grid with 95% CI bands."""

from __future__ import annotations

import argparse
import csv
import math
import time
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

SummaryRow = Dict[str, float | str]
ParamPoint = Tuple[float, float, float]  # (J, h, T)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot summary magnetization grid (models x parameter points).")
    parser.add_argument("--artifact-prefix", default="artifacts", help="Base folder for generated artifacts")
    parser.add_argument("--summary-csv", default=None, help="Path to magnetization_summary.csv")
    parser.add_argument("--output", default=None, help="Output image path")
    parser.add_argument(
        "--output-metrics-csv",
        default=None,
        help="Output CSV path for model-vs-model_1 summary metrics.",
    )
    parser.add_argument(
        "--models",
        default=None,
        help="Optional comma-separated model order (defaults to models present in CSV).",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Optional cap on number of parameter rows to render (for very large grids).",
    )
    parser.add_argument(
        "--transient-frac",
        type=float,
        default=0.5,
        help="Fraction of earliest timesteps used for transient RMSE (default: 0.5).",
    )
    parser.add_argument(
        "--steady-window",
        type=int,
        default=5,
        help="Number of final timesteps used to estimate steady-state mean (default: 5).",
    )
    parser.add_argument(
        "--convergence-tol",
        type=float,
        default=0.02,
        help="Absolute tolerance to define convergence to steady state (default: 0.02).",
    )
    return parser.parse_args()


def load_summary_rows(summary_csv: Path) -> List[SummaryRow]:
    rows: List[SummaryRow] = []
    with summary_csv.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(
                {
                    "model": row["model"],
                    "coupling": float(row["coupling"]),
                    "field": float(row["field"]),
                    "temperature": float(row["temperature"]),
                    "t": int(row["t"]),
                    "mean_m": float(row["mean_m"]),
                    "var_m": float(row["var_m"]),
                    "n": int(row["n"]),
                }
            )
    return rows


def list_models(rows: Sequence[SummaryRow], requested: str | None) -> List[str]:
    available = sorted({str(r["model"]) for r in rows})
    if requested is None:
        return available
    chosen = [m.strip() for m in requested.split(",") if m.strip()]
    return [m for m in chosen if m in available]


def list_param_points(rows: Sequence[SummaryRow]) -> List[ParamPoint]:
    points = {
        (float(r["coupling"]), float(r["field"]), float(r["temperature"]))
        for r in rows
    }
    return sorted(points)


def series_for(rows: Sequence[SummaryRow], model: str, point: ParamPoint) -> List[SummaryRow]:
    c, h, temp = point
    out = [
        r
        for r in rows
        if str(r["model"]) == model
        and abs(float(r["coupling"]) - c) < 1e-9
        and abs(float(r["field"]) - h) < 1e-9
        and abs(float(r["temperature"]) - temp) < 1e-9
    ]
    out.sort(key=lambda r: int(r["t"]))
    return out


def mean_and_ci95(row: SummaryRow) -> Tuple[float, float, float]:
    mu = float(row["mean_m"])
    var = max(0.0, float(row["var_m"]))
    n = max(1, int(row["n"]))
    se = math.sqrt(var / n)
    half = 1.96 * se
    return mu, mu - half, mu + half


def _series_to_arrays(series: Sequence[SummaryRow]) -> Tuple[List[int], List[float], List[float]]:
    ts = [int(r["t"]) for r in series]
    mean = [float(r["mean_m"]) for r in series]
    var = [float(r["var_m"]) for r in series]
    return ts, mean, var


def _rmse(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b:
        return float("nan")
    n = min(len(a), len(b))
    if n <= 0:
        return float("nan")
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(n)) / n)


def convergence_time(means: Sequence[float], steady_mean: float, tol: float) -> int:
    if not means:
        return 0
    for i in range(len(means)):
        if all(abs(v - steady_mean) <= tol for v in means[i:]):
            return i
    return len(means) - 1


def compute_metrics_against_model_1(
    rows: Sequence[SummaryRow],
    points: Sequence[ParamPoint],
    models: Sequence[str],
    transient_frac: float,
    steady_window: int,
    convergence_tol: float,
) -> List[Dict[str, float | str]]:
    if "model_1" not in models:
        return []

    metrics_rows: List[Dict[str, float | str]] = []
    frac = min(1.0, max(0.0, transient_frac))
    for point in points:
        _, ref_mean, ref_var = _series_to_arrays(series_for(rows, "model_1", point))
        if not ref_mean:
            continue
        steady_n_ref = max(1, min(steady_window, len(ref_mean)))
        ref_steady = sum(ref_mean[-steady_n_ref:]) / steady_n_ref
        ref_conv_t = convergence_time(ref_mean, ref_steady, convergence_tol)

        for model in models:
            t0 = time.perf_counter()
            _, model_mean, model_var = _series_to_arrays(series_for(rows, model, point))
            if not model_mean:
                continue
            n = min(len(ref_mean), len(model_mean))
            transient_n = max(1, int(math.ceil(n * frac)))
            transient_rmse = _rmse(model_mean[:transient_n], ref_mean[:transient_n])

            steady_n = max(1, min(steady_window, len(model_mean)))
            model_steady = sum(model_mean[-steady_n:]) / steady_n
            steady_bias = model_steady - ref_steady
            model_conv_t = convergence_time(model_mean, model_steady, convergence_tol)
            variance_mismatch = _rmse(model_var[:n], ref_var[:n])
            runtime_seconds = time.perf_counter() - t0

            c, h, temp = point
            metrics_rows.append(
                {
                    "model": model,
                    "coupling": c,
                    "field": h,
                    "temperature": temp,
                    "runtime_seconds": runtime_seconds,
                    "transient_rmse_vs_model_1": transient_rmse,
                    "steady_state_bias_vs_model_1": steady_bias,
                    "convergence_time": model_conv_t,
                    "convergence_time_diff_vs_model_1": model_conv_t - ref_conv_t,
                    "variance_mismatch_vs_model_1": variance_mismatch,
                }
            )
    return metrics_rows


def write_metrics_csv(path: Path, rows: Sequence[Dict[str, float | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "model",
        "coupling",
        "field",
        "temperature",
        "runtime_seconds",
        "transient_rmse_vs_model_1",
        "steady_state_bias_vs_model_1",
        "convergence_time",
        "convergence_time_diff_vs_model_1",
        "variance_mismatch_vs_model_1",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


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
        else Path(args.artifact_prefix) / "plots" / "magnetization_summary_grid.png"
    )
    output_metrics_csv = (
        Path(args.output_metrics_csv)
        if args.output_metrics_csv
        else Path(args.artifact_prefix) / "metrics" / "magnetization_summary_metrics.csv"
    )

    rows = load_summary_rows(summary_csv)
    if not rows:
        raise SystemExit(f"No rows found in {summary_csv}")

    models = list_models(rows, args.models)
    if not models:
        raise SystemExit("No matching models found in summary CSV for --models selection.")

    points = list_param_points(rows)
    if args.max_rows is not None:
        points = points[: max(0, args.max_rows)]
    if not points:
        raise SystemExit("No parameter points to plot after applying --max-rows.")

    metrics_rows = compute_metrics_against_model_1(
        rows=rows,
        points=points,
        models=models,
        transient_frac=args.transient_frac,
        steady_window=max(1, args.steady_window),
        convergence_tol=max(0.0, args.convergence_tol),
    )
    if metrics_rows:
        write_metrics_csv(output_metrics_csv, metrics_rows)
        print(f"Wrote summary metrics to {output_metrics_csv}")

    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError as exc:
        raise SystemExit("Missing plotting dependency. Install with: pip install matplotlib") from exc

    n_rows = len(points)
    n_cols = len(models)
    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(3.4 * n_cols, 2.1 * n_rows),
        sharex=True,
        sharey=True,
        constrained_layout=True,
    )
    if n_rows == 1 and n_cols == 1:
        axes_grid = [[axes]]
    elif n_rows == 1:
        axes_grid = [list(axes)]
    elif n_cols == 1:
        axes_grid = [[ax] for ax in axes]
    else:
        axes_grid = [list(row_axes) for row_axes in axes]

    for r_idx, point in enumerate(points):
        c, h, temp = point
        for c_idx, model in enumerate(models):
            ax = axes_grid[r_idx][c_idx]
            series = series_for(rows, model=model, point=point)
            if series:
                ts = [int(r["t"]) for r in series]
                means = []
                lo = []
                hi = []
                for row in series:
                    mu, lb, ub = mean_and_ci95(row)
                    means.append(mu)
                    lo.append(lb)
                    hi.append(ub)
                ax.plot(ts, means, color="tab:blue", linewidth=1.6)
                ax.fill_between(ts, lo, hi, color="tab:blue", alpha=0.20)
            else:
                ax.text(0.5, 0.5, "no data", ha="center", va="center", transform=ax.transAxes, fontsize=8)

            if r_idx == 0:
                ax.set_title(model)
            if c_idx == 0:
                ax.set_ylabel(f"m\nJ={c:.2f}\nh={h:.2f}\nT={temp:.2f}", fontsize=8)
            ax.set_ylim(-1.05, 1.05)
            ax.grid(alpha=0.15, linewidth=0.5)
            if r_idx == n_rows - 1:
                ax.set_xlabel("t")

    fig.suptitle("Summary magnetization manifold (mean with 95% CI)", fontsize=11)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=170)
    plt.close(fig)
    print(f"Wrote summary grid plot to {output_path}")


if __name__ == "__main__":
    main()
