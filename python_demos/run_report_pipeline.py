#!/usr/bin/env python3
"""Run a reproducible report-oriented pipeline across project phases."""

from __future__ import annotations

import argparse
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run manifold + mapping + visualization report pipeline.")
    parser.add_argument("--artifact-prefix", default="artifacts")
    parser.add_argument("--rows", type=int, default=2)
    parser.add_argument("--cols", type=int, default=2)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--source-model", default="model_1")
    parser.add_argument("--target-model", default="model_2")
    parser.add_argument("--coupling", type=float, default=0.7)
    parser.add_argument("--field", type=float, default=0.0)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--skip-plots", action="store_true", help="Skip matplotlib-dependent plotting steps")
    return parser.parse_args()


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    args = parse_args()

    run(
        [
            sys.executable,
            "python_demos/ising_magnetization_compare.py",
            "--artifact-prefix",
            args.artifact_prefix,
            "--rows",
            str(args.rows),
            "--cols",
            str(args.cols),
            "--steps",
            str(args.steps),
            "--seeds",
            str(args.seeds),
        ]
    )

    run(
        [
            sys.executable,
            "python_demos/fit_parameter_map.py",
            "--artifact-prefix",
            args.artifact_prefix,
            "--source-model",
            args.source_model,
            "--target-model",
            args.target_model,
        ]
    )

    if not args.skip_plots:
        run(
            [
                sys.executable,
                "python_demos/plot_magnetization_manifold.py",
                "--artifact-prefix",
                args.artifact_prefix,
                "--source-model",
                args.source_model,
                "--target-model",
                args.target_model,
                "--coupling",
                str(args.coupling),
                "--field",
                str(args.field),
                "--temperature",
                str(args.temperature),
            ]
        )

        run(
            [
                sys.executable,
                "python_demos/visualize_trajectory_matching.py",
                "--artifact-prefix",
                args.artifact_prefix,
                "--source-model",
                args.source_model,
                "--target-model",
                args.target_model,
                "--coupling",
                str(args.coupling),
                "--field",
                str(args.field),
                "--temperature",
                str(args.temperature),
            ]
        )

    run(
        [
            sys.executable,
            "python_demos/renormalization_operator_demo.py",
            "--artifact-prefix",
            args.artifact_prefix,
            "--rows",
            str(args.rows),
            "--cols",
            str(args.cols),
            "--steps",
            str(args.steps),
            "--no-plot",
        ]
    )

    run(
        [
            sys.executable,
            "python_demos/generate_figure_manifest.py",
            "--artifact-prefix",
            args.artifact_prefix,
            "--output",
            "reports/figure_manifest.json",
        ]
    )

    print("Pipeline complete. See artifacts/ and reports/ for outputs and structure.")


if __name__ == "__main__":
    main()
