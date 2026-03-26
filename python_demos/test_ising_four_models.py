"""Tests for Ising demo models and heatmap helpers."""

import math
import unittest

import isingmdp

try:
    from python_demos.ising_heatmap_gif import build_parser as build_gif_parser
except ModuleNotFoundError:
    from ising_heatmap_gif import build_parser as build_gif_parser  # type: ignore

try:
    from python_demos.ising_heatmap_gif import build_parser as build_gif_parser
except ModuleNotFoundError:
    from ising_heatmap_gif import build_parser as build_gif_parser  # type: ignore

try:
    from python_demos.ising_four_models import (
        IsingParams,
        grid_edges,
        model_1_heatmap_trajectory,
        model_1_single_spin,
        model_2_heatmap_trajectory,
        model_2_mean_field,
        model_3_heatmap_trajectory,
        model_3_local_probabilities,
        model_4_full_state_space,
        model_4_heatmap_trajectory,
        probs_to_state_distribution,
    )
except ModuleNotFoundError:
    from ising_four_models import (  # type: ignore
        IsingParams,
        grid_edges,
        model_1_heatmap_trajectory,
        model_1_single_spin,
        model_2_heatmap_trajectory,
        model_2_mean_field,
        model_3_heatmap_trajectory,
        model_3_local_probabilities,
        model_4_full_state_space,
        model_4_heatmap_trajectory,
        probs_to_state_distribution,
    )


class IsingDemoTests(unittest.TestCase):
    """Covers normalization, bounds, and heatmap frame shapes."""

    def test_top_level_package_import_smoke(self):
        self.assertTrue(hasattr(isingmdp, "model_2_mean_field"))

    def test_model_1_distribution_sums_to_one(self):
        params = IsingParams(temperature=1.0, coupling=0.5, field=0.1)
        trans = model_1_single_spin(params)
        self.assertAlmostEqual(sum(trans[(1,)].values()), 1.0)

    def test_model_2_distribution_sums_to_one(self):
        params = IsingParams(temperature=1.0, coupling=0.5, field=0.0)
        dist = model_2_mean_field(8, params, {4: 1.0})
        self.assertAlmostEqual(sum(dist.values()), 1.0)

    def test_model_2_mean_field_uses_tanh_magnetization_update(self):
        params = IsingParams(temperature=1.0, coupling=0.0, field=0.4)
        dist = model_2_mean_field(10, params, {5: 1.0})
        next_m = sum(((2 * k - 10) / 10) * p for k, p in dist.items())
        self.assertAlmostEqual(next_m, math.tanh(0.4), places=6)

    def test_model_3_stays_bounded(self):
        params = IsingParams(temperature=0.8, coupling=0.7, field=0.2)
        probs = model_3_local_probabilities([0.1, 0.5, 0.9, 0.3], params)
        for p in probs:
            self.assertGreaterEqual(p, 0.0)
            self.assertLessEqual(p, 1.0)
        dist = probs_to_state_distribution(probs)
        self.assertAlmostEqual(sum(dist.values()), 1.0)

    def test_model_4_distribution_sums_to_one_each_step(self):
        params = IsingParams(temperature=1.2, coupling=0.8, field=0.0)
        traj = model_4_full_state_space(
            start=(1, 1, -1, -1),
            params=params,
            edges=[(0, 1), (1, 2), (2, 3)],
            steps=3,
        )
        for dist in traj:
            self.assertAlmostEqual(sum(dist.values()), 1.0)

    def test_model_1_heatmap_trajectory_shape(self):
        params = IsingParams()
        traj = model_1_heatmap_trajectory(params=params, steps=2)
        self.assertEqual(len(traj), 3)
        for frame in traj:
            self.assertEqual(len(frame), 1)
            self.assertEqual(len(frame[0]), 2)
            for v in frame[0]:
                self.assertGreaterEqual(v, -1.0)
                self.assertLessEqual(v, 1.0)

    def test_model_2_heatmap_trajectory_shape(self):
        params = IsingParams()
        traj = model_2_heatmap_trajectory(n_spins=6, params=params, steps=2)
        self.assertEqual(len(traj), 3)
        for frame in traj:
            self.assertEqual(len(frame), 1)
            self.assertEqual(len(frame[0]), 7)
            for v in frame[0]:
                self.assertGreaterEqual(v, -1.0)
                self.assertLessEqual(v, 1.0)

    def test_model_3_heatmap_trajectory_shape(self):
        params = IsingParams()
        traj = model_3_heatmap_trajectory([0.8, 0.2, 0.5, 0.1], params=params, steps=2)
        self.assertEqual(len(traj), 3)
        for frame in traj:
            self.assertEqual(len(frame), 2)
            self.assertEqual(len(frame[0]), 2)

    def test_model_4_heatmap_trajectory_shape(self):
        params = IsingParams()
        traj = model_4_heatmap_trajectory(
            start=(1, 1, -1, -1),
            params=params,
            edges=[(0, 1), (1, 2), (2, 3), (3, 0)],
            steps=2,
        )
        self.assertEqual(len(traj), 3)
        for frame in traj:
            self.assertEqual(len(frame), 2)
            self.assertEqual(len(frame[0]), 2)

    def test_heatmap_gif_parser_accepts_layout_seed_and_intro_controls(self):
        parser = build_gif_parser()
        args = parser.parse_args([
            "--rows", "2", "--cols", "2", "--seed", "7", "--hold-frames", "4", "--intro-label-frames", "6"
        ])
        self.assertEqual(args.rows, 2)
        self.assertEqual(args.cols, 2)
        self.assertEqual(args.seed, 7)
        self.assertEqual(args.hold_frames, 4)
        self.assertEqual(args.intro_label_frames, 6)

if __name__ == "__main__":
    unittest.main()
