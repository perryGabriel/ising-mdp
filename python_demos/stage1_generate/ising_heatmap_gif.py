#!/usr/bin/env python3
"""Generate an animated GIF heatmap for selected Ising demo models."""

from __future__ import annotations

import argparse
import random
from pathlib import Path

try:
    from python_demos.foundation.ising_four_models import (
        IsingParams,
        model_1_heatmap_trajectory,
        model_2_magnetization_trajectory,
        model_3_heatmap_trajectory,
        model_4_heatmap_trajectory,
        model_5_heatmap_trajectory,
        grid_edges,
        MAX_ATOMS,
        spins_to_grid,
    )
except ModuleNotFoundError:
    from python_demos.foundation.ising_four_models import (  # type: ignore
        IsingParams,
        model_1_heatmap_trajectory,
        model_2_magnetization_trajectory,
        model_3_heatmap_trajectory,
        model_4_heatmap_trajectory,
        model_5_heatmap_trajectory,
        grid_edges,
        MAX_ATOMS,
        spins_to_grid,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for GIF generation."""

    parser = argparse.ArgumentParser(description="Create a GIF of Ising heatmaps over time.")
    parser.add_argument("--artifact-prefix", default="artifacts", help="Base folder for generated artifacts")
    parser.add_argument("--output", default=None, help="Output GIF path (overrides artifact-prefix default)")
    parser.add_argument("--steps", type=int, default=20, help="Animation steps")
    parser.add_argument("--fps", type=int, default=4, help="Frames per second")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--coupling", type=float, default=0.8)
    parser.add_argument("--field", type=float, default=0.1)
    parser.add_argument("--mixing", type=float, default=0.2, help="Model-3 mixing coefficient")
    parser.add_argument("--rows", type=int, default=4, help="Lattice rows shared by all model panels")
    parser.add_argument("--cols", type=int, default=4, help="Lattice columns shared by all model panels")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for shared lattice initialization")
    parser.add_argument("--hold-frames", type=int, default=4, help="Extra initial-condition frames before dynamics")
    parser.add_argument("--intro-label-frames", type=int, default=6, help="Frames to show interpretation labels")
    parser.add_argument(
        "--models",
        default="1,2,3,4,5",
        help="Comma-separated model ids to include (subset of 1,2,3,4,5).",
    )
    return parser


def main() -> None:
    """Generate and save the GIF with model panels and parameter key."""

    try:
        import matplotlib.pyplot as plt
        from matplotlib.animation import FuncAnimation, PillowWriter
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing visualization dependency. Install with: pip install matplotlib pillow"
        ) from exc

    args = build_parser().parse_args()
    params = IsingParams(temperature=args.temperature, coupling=args.coupling, field=args.field)

    if args.rows <= 0 or args.cols <= 0:
        raise SystemExit("--rows and --cols must both be positive integers.")

    n_atoms = args.rows * args.cols
    selected_models = [m.strip() for m in args.models.split(",") if m.strip()]
    if not selected_models or any(m not in {"1", "2", "3", "4", "5"} for m in selected_models):
        raise SystemExit("--models must be a comma-separated subset of {1,2,3,4,5}")

    if "4" in selected_models and n_atoms > MAX_ATOMS:
        raise SystemExit(f"rows*cols must be <= {MAX_ATOMS} for the full-state model to remain tractable.")

    rng = random.Random(args.seed)
    start = tuple(rng.choice([-1, 1]) for _ in range(n_atoms))
    initial_probs = [1.0 if spin == 1 else 0.0 for spin in start]
    edges = grid_edges(args.rows, args.cols)

    model_frames: dict[str, list[list[list[float]]]] = {}
    model_titles: dict[str, str] = {}
    if "1" in selected_models:
        model_frames["1"] = model_1_heatmap_trajectory(params=params, steps=args.steps, initial_spins=start, n_cols=args.cols)
        model_titles["1"] = "Model 1: Independent-spin lattice"
    if "2" in selected_models:
        model2_magnetization = model_2_magnetization_trajectory(
            n_spins=n_atoms,
            params=params,
            steps=args.steps,
            initial_k_dist={sum(1 for s in start if s == 1): 1.0},
        )
        model_frames["2"] = [
            spins_to_grid([magnetization] * n_atoms, n_cols=args.cols) for magnetization in model2_magnetization
        ]
        model_titles["2"] = "Model 2: Mean-field lattice"
    if "3" in selected_models:
        model_frames["3"] = model_3_heatmap_trajectory(
            initial_probs=initial_probs,
            params=params,
            steps=args.steps,
            mixing=args.mixing,
            n_rows=args.rows,
            n_cols=args.cols,
        )
        model_titles["3"] = "Model 3: Local probs"
    if "4" in selected_models:
        model_frames["4"] = model_4_heatmap_trajectory(start=start, params=params, edges=edges, steps=args.steps, n_cols=args.cols)
        model_titles["4"] = f"Model 4: Full state space ({args.rows}x{args.cols}, N={n_atoms})"
    if "5" in selected_models:
        model_frames["5"] = model_5_heatmap_trajectory(
            initial_probs=initial_probs,
            params=params,
            steps=args.steps,
            n_rows=args.rows,
            n_cols=args.cols,
        )
        model_titles["5"] = "Model 5: Restricted-interval operator"

    n_frames = min(len(model_frames[mid]) for mid in selected_models)

    hold_frames = max(0, args.hold_frames)
    total_frames = hold_frames + n_frames

    n_panels = len(selected_models)
    n_cols_plot = 2 if n_panels > 1 else 1
    n_rows_plot = (n_panels + n_cols_plot - 1) // n_cols_plot
    fig, axes = plt.subplots(n_rows_plot, n_cols_plot, figsize=(4.5 * n_cols_plot, 4.5 * n_rows_plot), constrained_layout=True)
    fig.suptitle(f"Ising model heatmaps over time, (T={args.temperature:.3g}, J={args.coupling:.3g}, h={args.field:.3g})", fontsize=12)
    ax = axes.ravel() if hasattr(axes, "ravel") else [axes]

    images = []
    for idx, model_id in enumerate(selected_models):
        im = ax[idx].imshow(model_frames[model_id][0], vmin=-1.0, vmax=1.0, cmap="coolwarm", aspect="equal", animated=True)
        ax[idx].set_title(model_titles[model_id])
        ax[idx].set_box_aspect(1)
        ax[idx].set_xticks([])
        ax[idx].set_yticks([])
        images.append(im)
    for idx in range(len(selected_models), len(ax)):
        ax[idx].set_visible(False)

    cbar = fig.colorbar(images[-1], ax=[a for a in ax if a.get_visible()], fraction=0.03, pad=0.02)
    cbar.set_label("Scaled value in [-1, 1]")

    param_text = fig.text(
        0.5,
        0.01,
        (
            f"T={args.temperature:.3g} | J={args.coupling:.3g} | h={args.field:.3g} "
            f"| mixing={args.mixing:.3g} "
            f"| models={','.join(selected_models)} "
            f"| lattice={args.rows}x{args.cols} | seed={args.seed}"
        ),
        ha="center",
    )
    step_text = fig.text(0.02, 0.01, "step = 0 (initial hold)", ha="left")
    intro_text = fig.text(
        0.5,
        0.965,
        "Intro: shared seeded initial condition across all models",
        ha="center",
        va="top",
        fontsize=10,
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.75},
    )

    def update(frame_idx: int):
        model_idx = 0 if frame_idx < hold_frames else frame_idx - hold_frames
        for im, model_id in zip(images, selected_models):
            im.set_data(model_frames[model_id][model_idx])

        if frame_idx < hold_frames:
            step_text.set_text(f"step = 0 (initial hold {frame_idx + 1}/{hold_frames})")
        else:
            step_text.set_text(f"step = {model_idx}")

        if frame_idx < max(0, args.intro_label_frames):
            intro_text.set_text("Intro: seeded start • red=up (+1), blue=down (-1), all panels share rows×cols")
            intro_text.set_visible(True)
        else:
            intro_text.set_visible(False)

        return [*images, step_text, param_text, intro_text]

    animation = FuncAnimation(fig, update, frames=total_frames, interval=max(1, int(1000 / args.fps)), blit=True)

    output_path = Path(args.output) if args.output else Path(args.artifact_prefix) / "gifs" / "ising_heatmaps.gif"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    animation.save(output_path, writer=PillowWriter(fps=args.fps))
    print(f"Saved GIF to {output_path}")


if __name__ == "__main__":
    main()
