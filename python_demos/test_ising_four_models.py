"""Tests for Ising demo models and heatmap helpers."""

import unittest

try:
    from python_demos.ising_four_models import (
        IsingParams,
        initial_k_distribution,
        model_1_heatmap_trajectory,
        model_1_single_spin,
        model_2_heatmap_trajectory,
        model_2_mean_field,
        model_3_heatmap_trajectory,
        model_3_local_probabilities,
        model_4_full_state_space,
        model_4_heatmap_trajectory,
        probs_to_state_distribution,
        random_initial_probabilities,
    )
except ModuleNotFoundError:
    from ising_four_models import (  # type: ignore
        IsingParams,
        initial_k_distribution,
        model_1_heatmap_trajectory,
        model_1_single_spin,
        model_2_heatmap_trajectory,
        model_2_mean_field,
        model_3_heatmap_trajectory,
        model_3_local_probabilities,
        model_4_full_state_space,
        model_4_heatmap_trajectory,
        probs_to_state_distribution,
        random_initial_probabilities,
    )


class IsingDemoTests(unittest.TestCase):
    """Covers normalization, bounds, and heatmap frame shapes."""

    def test_model_1_distribution_sums_to_one(self):
        params = IsingParams(temperature=1.0, coupling=0.5, field=0.1)
        trans = model_1_single_spin(params)
        self.assertAlmostEqual(sum(trans[(1,)].values()), 1.0)

    def test_model_2_distribution_sums_to_one(self):
        params = IsingParams(temperature=1.0, coupling=0.5, field=0.0)
        dist = model_2_mean_field(8, params, {4: 1.0})
        self.assertAlmostEqual(sum(dist.values()), 1.0)

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

    def test_random_initial_probabilities_reproducible(self):
        p1 = random_initial_probabilities(4, seed=11)
        p2 = random_initial_probabilities(4, seed=11)
        self.assertEqual(p1, p2)

    def test_initial_k_distribution_sums_to_one(self):
        kd = initial_k_distribution([0.2, 0.7, 0.5, 0.1])
        self.assertAlmostEqual(sum(kd.values()), 1.0)

    def test_model_1_heatmap_trajectory_shape(self):
        params = IsingParams()
        traj = model_1_heatmap_trajectory(initial_probs=[0.2, 0.7, 0.5, 0.1], params=params, steps=2, n_cols=2)
        self.assertEqual(len(traj), 3)
        for frame in traj:
            self.assertEqual(len(frame), 2)
            self.assertEqual(len(frame[0]), 2)

    def test_model_2_heatmap_trajectory_shape(self):
        params = IsingParams()
        traj = model_2_heatmap_trajectory(
            n_spins=4,
            params=params,
            steps=2,
            initial_probs=[0.2, 0.7, 0.5, 0.1],
            n_cols=2,
        )
        self.assertEqual(len(traj), 3)
        for frame in traj:
            self.assertEqual(len(frame), 2)
            self.assertEqual(len(frame[0]), 2)

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


if __name__ == "__main__":
    unittest.main()
