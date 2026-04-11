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
        "--metrics-output",
        default=None,
        help="Output CSV path for per-model metrics (defaults to artifacts/metrics/magnetization_summary_metrics.csv).",
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


def _mean(values: Sequence[float]) -> float:
    return sum(values) / max(1, len(values))


def _rmse(a: Sequence[float], b: Sequence[float]) -> float:
    n = min(len(a), len(b))
    if n == 0:
        return float("nan")
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(n)) / n)


def convergence_time(series: Sequence[float], tol: float = 0.05) -> int:
    if not series:
        return 0
    n = len(series)
    tail = series[-max(3, n // 5):]
    steady = _mean(tail)
    for t in range(n):
        if all(abs(v - steady) <= tol for v in series[t:]):
            return t
    return n - 1


def compute_metrics_for_point(
    rows: Sequence[SummaryRow], point: ParamPoint, model: str, ground_truth: str = "model_1"
) -> Dict[str, float | str]:
    started = time.perf_counter()
    series = series_for(rows, model=model, point=point)
    gt_series = series_for(rows, model=ground_truth, point=point)
    c, h, temp = point

    model_means = [float(r["mean_m"]) for r in series]
    gt_means = [float(r["mean_m"]) for r in gt_series]
    model_vars = [float(r["var_m"]) for r in series]
    gt_vars = [float(r["var_m"]) for r in gt_series]

    n = min(len(model_means), len(gt_means))
    transient_n = max(1, n // 2)
    transient_rmse = _rmse(model_means[:transient_n], gt_means[:transient_n]) if n else float("nan")

    steady_window = max(3, n // 5) if n else 0
    if n and steady_window > 0:
        steady_bias = _mean(model_means[n - steady_window:n]) - _mean(gt_means[n - steady_window:n])
    else:
        steady_bias = float("nan")

    conv_t = convergence_time(model_means) if model_means else float("nan")
    gt_conv_t = convergence_time(gt_means) if gt_means else float("nan")
    conv_diff = (conv_t - gt_conv_t) if isinstance(conv_t, int) and isinstance(gt_conv_t, int) else float("nan")

    if n:
        var_mismatch = _mean([abs(model_vars[i] - gt_vars[i]) for i in range(n)])
    else:
        var_mismatch = float("nan")

    runtime_seconds = time.perf_counter() - started
    if model == ground_truth and n:
        transient_rmse = 0.0
        steady_bias = 0.0
        conv_diff = 0.0
        var_mismatch = 0.0

    return {
        "model": model,
        "coupling": c,
        "field": h,
        "temperature": temp,
        "runtime_seconds": runtime_seconds,
        "transient_rmse_vs_model_1": transient_rmse,
        "steady_state_bias_vs_model_1": steady_bias,
        "convergence_time": conv_t,
        "convergence_time_diff_vs_model_1": conv_diff,
        "variance_mismatch_vs_model_1": var_mismatch,
    }


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
    metrics_output_path = (
        Path(args.metrics_output)
        if args.metrics_output
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

    plotting_available = True
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        plotting_available = False

    if plotting_available:
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
                    ax.set_title(model, fontsize=14)

                if c_idx == 0:
                    ax.set_ylabel(
                        f"m\nJ={c:.2f}\nh={h:.2f}\nT={temp:.2f}",
                        fontsize=12,
                        rotation=0,
                        labelpad=35,
                        va="center"
                    )

                ax.set_ylim(-1.05, 1.05)
                ax.grid(alpha=0.15, linewidth=0.5)

                if r_idx == n_rows - 1:
                    ax.set_xlabel("t", fontsize=12)

        fig.suptitle("Summary magnetization manifold (mean with 95% CI)", fontsize=11)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=170)
        plt.close(fig)

    metric_rows: List[Dict[str, float | str]] = []
    for point in points:
        for model in models:
            metric_rows.append(compute_metrics_for_point(rows, point=point, model=model, ground_truth="model_1"))
    write_metrics_csv(metrics_output_path, metric_rows)

    if plotting_available:
        print(f"Wrote summary grid plot to {output_path}")
    else:
        print("matplotlib unavailable; skipped grid plot generation.")
    print(f"Wrote summary metrics to {metrics_output_path}")


if __name__ == "__main__":
    main()
