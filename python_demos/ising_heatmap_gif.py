#!/usr/bin/env python3
"""Generate evolving Ising heatmaps as an animated GIF.

This script visualizes magnetization trajectories for:
- Model 3 (local-neighborhood probability model, fixed 2x2)
- Model 4 (full exponential state-space model, typically N=4)
"""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from python_demos.ising_four_models import (
        IsingParams,
        model_3_heatmap_trajectory,
        model_4_heatmap_trajectory,
    )
except ModuleNotFoundError:
    from ising_four_models import (  # type: ignore
        IsingParams,
        model_3_heatmap_trajectory,
        model_4_heatmap_trajectory,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a GIF of Ising heatmaps over time.")
    parser.add_argument("--output", default="python_demos/ising_heatmaps.gif", help="Output GIF path")
    parser.add_argument("--steps", type=int, default=20, help="Animation steps")
    parser.add_argument("--fps", type=int, default=4, help="Frames per second")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--coupling", type=float, default=0.8)
    parser.add_argument("--field", type=float, default=0.1)
    parser.add_argument("--mixing", type=float, default=0.2, help="Model-3 mixing coefficient")
    parser.add_argument(
        "--exp-atoms",
        type=int,
        default=4,
        help="Atoms for model-4 trajectory (use 4 for a 2x2 heatmap).",
    )
    return parser


def main() -> None:
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

    model3_frames = model_3_heatmap_trajectory(
        initial_probs=[0.8, 0.2, 0.5, 0.1],
        params=params,
        steps=args.steps,
        mixing=args.mixing,
        n_cols=2,
    )
    model4_frames = model_4_heatmap_trajectory(
        start=start,
        params=params,
        edges=edges,
        steps=args.steps,
        n_cols=2,
    )

    n_frames = min(len(model3_frames), len(model4_frames))

    fig, axes = plt.subplots(1, 2, figsize=(8, 4), constrained_layout=True)
    fig.suptitle("Ising magnetization heatmaps over time", fontsize=12)

    im1 = axes[0].imshow(model3_frames[0], vmin=-1.0, vmax=1.0, cmap="coolwarm", animated=True)
    im2 = axes[1].imshow(model4_frames[0], vmin=-1.0, vmax=1.0, cmap="coolwarm", animated=True)

    axes[0].set_title("Model 3: Local probs")
    axes[1].set_title(f"Model 4: Full state space (N={n_atoms})")
    for ax in axes:
        ax.set_xticks([])
        ax.set_yticks([])

    cbar = fig.colorbar(im2, ax=axes.ravel().tolist(), fraction=0.046, pad=0.04)
    cbar.set_label("Expected spin (magnetization)")

    step_text = fig.text(0.5, 0.02, "step = 0", ha="center")

    def update(frame_idx: int):
        im1.set_data(model3_frames[frame_idx])
        im2.set_data(model4_frames[frame_idx])
        step_text.set_text(f"step = {frame_idx}")
        return [im1, im2, step_text]

    animation = FuncAnimation(fig, update, frames=n_frames, interval=max(1, int(1000 / args.fps)), blit=True)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    animation.save(output_path, writer=PillowWriter(fps=args.fps))
    print(f"Saved GIF to {output_path}")


if __name__ == "__main__":
    main()
