"""Unit tests for one-at-a-time sweep plotting helpers."""

import math
import tempfile
import unittest
from pathlib import Path

from python_demos.stage3_analyze.plot_one_at_a_time_sweeps import (
    build_sweep_points,
    flattened_rmse_vs_reference,
    grouped_by_model_point,
    load_summary,
    steady_state_mean,
)


class PlotOneAtATimeSweepsTests(unittest.TestCase):
    def test_load_and_group_helpers(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "summary.csv"
            path.write_text(
                "model,coupling,field,temperature,t,mean_m,var_m,n\n"
                "model_1,0.2,0.0,1.0,0,0.1,0.0,1\n"
                "model_1,0.2,0.0,1.0,1,0.2,0.0,1\n"
                "model_1,0.2,0.0,1.2,0,0.2,0.0,1\n"
                "model_2,0.2,0.0,1.0,0,0.0,0.0,1\n"
                "model_2,0.2,0.0,1.2,0,0.1,0.0,1\n",
                encoding="utf-8",
            )
            data = load_summary(path)
            grouped = grouped_by_model_point(data)
            self.assertIn("model_1", grouped)
            sweep = build_sweep_points(grouped, "model_1", base=(0.2, 0.0, 1.0), sweep_axis="temperature")
            self.assertEqual([x for x, _ in sweep], [1.0, 1.2])

    def test_metric_helpers(self):
        self.assertAlmostEqual(steady_state_mean({0: 0.1, 1: 0.2, 2: 0.4, 3: 0.6}), (0.2 + 0.4 + 0.6) / 3.0)

        model_points = [
            (0.6, {0: 0.1, 1: 0.2}),
            (0.8, {0: 0.3, 1: 0.5}),
        ]
        ref_points = [
            (0.6, {0: 0.1, 1: 0.1}),
            (0.8, {0: 0.2, 1: 0.3}),
        ]
        rmse = flattened_rmse_vs_reference(model_points, ref_points)
        self.assertFalse(math.isnan(rmse))
        self.assertGreater(rmse, 0.0)


if __name__ == "__main__":
    unittest.main()

