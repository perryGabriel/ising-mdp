import unittest

try:
    from python_demos.ising_four_models import (
        IsingParams,
        model_1_single_spin,
        model_2_mean_field,
        model_3_local_probabilities,
        model_4_full_state_space,
        probs_to_state_distribution,
    )
except ModuleNotFoundError:
    # Allows running directly from inside python_demos/:
    #   python test_ising_four_models.py
    from ising_four_models import (  # type: ignore
        IsingParams,
        model_1_single_spin,
        model_2_mean_field,
        model_3_local_probabilities,
        model_4_full_state_space,
        probs_to_state_distribution,
    )


class IsingDemoTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
