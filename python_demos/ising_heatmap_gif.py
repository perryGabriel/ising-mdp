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
        random_initial_probabilities,
        sample_state_from_probabilities,
    )
except ModuleNotFoundError:
    from ising_four_models import (  # type: ignore
        IsingParams,
        model_1_heatmap_trajectory,
        model_2_heatmap_trajectory,
        model_3_heatmap_trajectory,
        model_4_heatmap_trajectory,
        random_initial_probabilities,
        sample_state_from_probabilities,
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
    parser.add_argument("--rows", type=int, default=2, help="Lattice rows (all models)")
    parser.add_argument("--cols", type=int, default=2, help="Lattice cols (all models)")
    parser.add_argument("--seed", type=int, default=7, help="Seed for shared random initialization")
    # Backwards-compatibility options from earlier CLI versions.
    parser.add_argument("--mean-field-spins", type=int, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--exp-atoms", type=int, default=None, help=argparse.SUPPRESS)
    return parser


def main() -> None:
    """Generate and save the GIF with model panels and parameter key."""

    args = build_parser().parse_args()
    params = IsingParams(temperature=args.temperature, coupling=args.coupling, field=args.field)

    try:
        import matplotlib.pyplot as plt
        from matplotlib.animation import FuncAnimation, PillowWriter
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing visualization dependency. Install with: pip install matplotlib pillow"
        ) from exc

    # Compatibility bridge: allow old flags without breaking newer layout flags.
    if args.exp_atoms is not None and (args.rows, args.cols) == (2, 2):
        if args.exp_atoms != 4:
            raise SystemExit("Only --exp-atoms 4 is supported with unified 2x2 layout.")

    if args.rows <= 0 or args.cols <= 0:
        raise SystemExit("rows and cols must be positive integers")

    n_atoms = args.rows * args.cols
    if n_atoms != 4:
        raise SystemExit(
            "Current model set alignment supports 2x2 (4 atoms) so all four models share the same layout. "
            "Please use --rows 2 --cols 2."
        )

    initial_probs = random_initial_probabilities(n_atoms=n_atoms, seed=args.seed)
    start = sample_state_from_probabilities(initial_probs, seed=args.seed)
    edges = [(0, 1), (0, 2), (1, 3), (2, 3)]

    model1_frames = model_1_heatmap_trajectory(
        initial_probs=initial_probs, params=params, steps=args.steps, n_cols=args.cols
    )
    model2_frames = model_2_heatmap_trajectory(
        n_spins=n_atoms,
        params=params,
        steps=args.steps,
        initial_probs=initial_probs,
        n_cols=args.cols,
    )
    model3_frames = model_3_heatmap_trajectory(
        initial_probs=initial_probs,
        params=params,
        steps=args.steps,
        mixing=args.mixing,
        n_cols=args.cols,
    )
    model4_frames = model_4_heatmap_trajectory(
        start=start,
        params=params,
        edges=edges,
        steps=args.steps,
        n_cols=args.cols,
    )

    n_frames = min(len(model1_frames), len(model2_frames), len(model3_frames), len(model4_frames))

    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    fig.suptitle("Ising model heatmaps over time", fontsize=12)
    ax = axes.ravel()

    im1 = ax[0].imshow(model1_frames[0], vmin=-1.0, vmax=1.0, cmap="coolwarm", animated=True)
    im2 = ax[1].imshow(model2_frames[0], vmin=-1.0, vmax=1.0, cmap="coolwarm", animated=True)
    im3 = ax[2].imshow(model3_frames[0], vmin=-1.0, vmax=1.0, cmap="coolwarm", animated=True)
    im4 = ax[3].imshow(model4_frames[0], vmin=-1.0, vmax=1.0, cmap="coolwarm", animated=True)

    ax[0].set_title("Model 1: Single-spin chain")
    ax[1].set_title("Model 2: Mean-field")
    ax[2].set_title("Model 3: Local probs")
    ax[3].set_title("Model 4: Full state space")

    for a in ax:
        a.set_xticks([])
        a.set_yticks([])

    cbar = fig.colorbar(im4, ax=ax.tolist(), fraction=0.03, pad=0.02)
    cbar.set_label("Expected spin / polarization in [-1, 1]")

    init_text = ", ".join(f"{p:.2f}" for p in initial_probs)
    param_text = fig.text(
        0.5,
        0.01,
        (
            f"T={args.temperature:.3g} | J={args.coupling:.3g} | h={args.field:.3g} "
            f"| mixing={args.mixing:.3g} | layout={args.rows}x{args.cols} | seed={args.seed} "
            f"| init_probs=[{init_text}]"
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
