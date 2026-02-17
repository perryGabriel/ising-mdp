#!/usr/bin/env python3
"""Generate an animated GIF heatmap for all four Ising demo models."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from python_demos.ising_four_models import (
        IsingParams,
        model_1_heatmap_trajectory,
        model_2_heatmap_trajectory,
        model_3_heatmap_trajectory,
        model_4_heatmap_trajectory,
    )
except ModuleNotFoundError:
    from ising_four_models import (  # type: ignore
        IsingParams,
        model_1_heatmap_trajectory,
        model_2_heatmap_trajectory,
        model_3_heatmap_trajectory,
        model_4_heatmap_trajectory,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for GIF generation."""

    parser = argparse.ArgumentParser(description="Create a GIF of Ising heatmaps over time.")
    parser.add_argument("--output", default="python_demos/ising_heatmaps.gif", help="Output GIF path")
    parser.add_argument("--steps", type=int, default=20, help="Animation steps")
    parser.add_argument("--fps", type=int, default=4, help="Frames per second")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--coupling", type=float, default=0.8)
    parser.add_argument("--field", type=float, default=0.1)
    parser.add_argument("--mixing", type=float, default=0.2, help="Model-3 mixing coefficient")
    parser.add_argument("--mean-field-spins", type=int, default=12)
    parser.add_argument(
        "--exp-atoms",
        type=int,
        default=4,
        help="Atoms for model-4 trajectory (use 4 for a 2x2 heatmap).",
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

    n_atoms = max(1, min(args.exp_atoms, 4))
    start = tuple([1] * (n_atoms // 2) + [-1] * (n_atoms - n_atoms // 2))
    edges = [(i, (i + 1) % n_atoms) for i in range(n_atoms)] if n_atoms > 1 else []

    model1_frames = model_1_heatmap_trajectory(params=params, steps=args.steps)
    model2_frames = model_2_heatmap_trajectory(
        n_spins=max(2, args.mean_field_spins), params=params, steps=args.steps
    )
    model3_frames = model_3_heatmap_trajectory(
        initial_probs=[0.8, 0.2, 0.5, 0.1],
        params=params,
        steps=args.steps,
        mixing=args.mixing,
        n_cols=2,
    )
    model4_frames = model_4_heatmap_trajectory(
        start=start, params=params, edges=edges, steps=args.steps, n_cols=2
    )

    n_frames = min(len(model1_frames), len(model2_frames), len(model3_frames), len(model4_frames))

    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    fig.suptitle("Ising model heatmaps over time", fontsize=12)
    ax = axes.ravel()

    im1 = ax[0].imshow(model1_frames[0], vmin=-1.0, vmax=1.0, cmap="coolwarm", aspect="auto", animated=True)
    im2 = ax[1].imshow(model2_frames[0], vmin=-1.0, vmax=1.0, cmap="coolwarm", aspect="auto", animated=True)
    im3 = ax[2].imshow(model3_frames[0], vmin=-1.0, vmax=1.0, cmap="coolwarm", animated=True)
    im4 = ax[3].imshow(model4_frames[0], vmin=-1.0, vmax=1.0, cmap="coolwarm", animated=True)

    ax[0].set_title("Model 1: Single-spin chain")
    ax[1].set_title("Model 2: Mean-field K")
    ax[2].set_title("Model 3: Local probs")
    ax[3].set_title(f"Model 4: Full state space (N={n_atoms})")

    ax[0].set_yticks([])
    ax[0].set_xticks([0, 1], ["P(↓)", "P(↑)"])
    ax[1].set_yticks([])
    ax[1].set_xlabel("K = #up")
    ax[2].set_xticks([])
    ax[2].set_yticks([])
    ax[3].set_xticks([])
    ax[3].set_yticks([])

    cbar = fig.colorbar(im4, ax=ax.tolist(), fraction=0.03, pad=0.02)
    cbar.set_label("Scaled value in [-1, 1]")

    param_text = fig.text(
        0.5,
        0.01,
        (
            f"T={args.temperature:.3g} | J={args.coupling:.3g} | h={args.field:.3g} "
            f"| mixing={args.mixing:.3g} | mean_field_spins={args.mean_field_spins}"
        ),
        ha="center",
    )
    step_text = fig.text(0.02, 0.01, "step = 0", ha="left")

    def update(frame_idx: int):
        im1.set_data(model1_frames[frame_idx])
        im2.set_data(model2_frames[frame_idx])
        im3.set_data(model3_frames[frame_idx])
        im4.set_data(model4_frames[frame_idx])
        step_text.set_text(f"step = {frame_idx}")
        return [im1, im2, im3, im4, step_text, param_text]

    animation = FuncAnimation(fig, update, frames=n_frames, interval=max(1, int(1000 / args.fps)), blit=True)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    animation.save(output_path, writer=PillowWriter(fps=args.fps))
    print(f"Saved GIF to {output_path}")


if __name__ == "__main__":
    main()
