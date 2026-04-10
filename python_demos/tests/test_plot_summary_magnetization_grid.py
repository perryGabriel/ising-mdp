"""Unit tests for plot_summary_magnetization_grid helpers."""

import tempfile
import unittest
from pathlib import Path

from python_demos.stage3_analyze.plot_summary_magnetization_grid import (
    list_models,
    list_param_points,
    load_summary_rows,
    mean_and_ci95,
    series_for,
)


class PlotSummaryMagnetizationGridTests(unittest.TestCase):
    def test_load_and_select_helpers(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "summary.csv"
            path.write_text(
                "model,coupling,field,temperature,t,mean_m,var_m,n\n"
                "model_1,0.2,0.0,1.0,0,0.1,0.04,25\n"
                "model_1,0.2,0.0,1.0,1,0.2,0.04,25\n"
                "model_2,0.2,0.0,1.0,0,0.0,0.01,16\n",
                encoding="utf-8",
            )
            rows = load_summary_rows(path)
            self.assertEqual(len(rows), 3)
            self.assertEqual(list_models(rows, None), ["model_1", "model_2"])
            self.assertEqual(list_models(rows, "model_2,model_9"), ["model_2"])

            points = list_param_points(rows)
            self.assertEqual(points, [(0.2, 0.0, 1.0)])

            s = series_for(rows, model="model_1", point=(0.2, 0.0, 1.0))
            self.assertEqual(len(s), 2)
            self.assertEqual([r["t"] for r in s], [0, 1])

    def test_mean_and_ci95(self):
        mu, lo, hi = mean_and_ci95(
            {"mean_m": 0.2, "var_m": 0.04, "n": 25, "model": "m", "coupling": 0.0, "field": 0.0, "temperature": 1.0, "t": 0}
        )
        self.assertAlmostEqual(mu, 0.2)
        self.assertLess(lo, mu)
        self.assertGreater(hi, mu)


if __name__ == "__main__":
    unittest.main()
