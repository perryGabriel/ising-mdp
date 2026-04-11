"""Unit tests for plot_summary_magnetization_grid helpers."""

import math
import tempfile
import unittest
from pathlib import Path

from python_demos.stage3_analyze.plot_summary_magnetization_grid import (
    compute_metrics_for_point,
    convergence_time,
    list_models,
    list_param_points,
    load_runtime_map,
    load_summary_rows,
    mean_and_ci95,
    series_for,
    write_metrics_csv,
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

    def test_metrics_helpers(self):
        rows = [
            {"model": "model_1", "coupling": 0.2, "field": 0.0, "temperature": 1.0, "t": 0, "mean_m": 0.0, "var_m": 0.02, "n": 20},
            {"model": "model_1", "coupling": 0.2, "field": 0.0, "temperature": 1.0, "t": 1, "mean_m": 0.4, "var_m": 0.02, "n": 20},
            {"model": "model_1", "coupling": 0.2, "field": 0.0, "temperature": 1.0, "t": 2, "mean_m": 0.6, "var_m": 0.02, "n": 20},
            {"model": "model_1", "coupling": 0.2, "field": 0.0, "temperature": 1.0, "t": 3, "mean_m": 0.6, "var_m": 0.02, "n": 20},
            {"model": "model_2", "coupling": 0.2, "field": 0.0, "temperature": 1.0, "t": 0, "mean_m": 0.1, "var_m": 0.03, "n": 20},
            {"model": "model_2", "coupling": 0.2, "field": 0.0, "temperature": 1.0, "t": 1, "mean_m": 0.5, "var_m": 0.01, "n": 20},
            {"model": "model_2", "coupling": 0.2, "field": 0.0, "temperature": 1.0, "t": 2, "mean_m": 0.5, "var_m": 0.03, "n": 20},
            {"model": "model_2", "coupling": 0.2, "field": 0.0, "temperature": 1.0, "t": 3, "mean_m": 0.5, "var_m": 0.01, "n": 20},
        ]
        self.assertEqual(convergence_time([0.0, 0.5, 0.49, 0.5], tol=0.02), 1)
        metrics = compute_metrics_for_point(rows, point=(0.2, 0.0, 1.0), model="model_2", runtime_map={})
        self.assertTrue(math.isnan(float(metrics["runtime_seconds"])))
        self.assertGreaterEqual(float(metrics["transient_rmse_vs_model_1"]), 0.0)
        self.assertIn("variance_mismatch_vs_model_1", metrics)

        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "metrics.csv"
            write_metrics_csv(out, [metrics])
            text = out.read_text(encoding="utf-8")
            self.assertIn("transient_rmse_vs_model_1", text)
            self.assertIn("model_2", text)

    def test_load_runtime_map_and_ratio(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "raw.csv"
            raw.write_text(
                "model,coupling,field,temperature,seed,t,m,runtime_seconds\n"
                "model_1,0.2,0.0,1.0,0,0,0.1,0.5\n"
                "model_1,0.2,0.0,1.0,0,1,0.2,0.5\n"
                "model_2,0.2,0.0,1.0,0,0,0.0,1.0\n"
                "model_2,0.2,0.0,1.0,0,1,0.1,1.0\n",
                encoding="utf-8",
            )
            runtime_map = load_runtime_map(raw)
            self.assertAlmostEqual(runtime_map[("model_1", 0.2, 0.0, 1.0)], 0.5)
            self.assertAlmostEqual(runtime_map[("model_2", 0.2, 0.0, 1.0)], 1.0)

            rows = [
                {"model": "model_1", "coupling": 0.2, "field": 0.0, "temperature": 1.0, "t": 0, "mean_m": 0.1, "var_m": 0.01, "n": 5},
                {"model": "model_1", "coupling": 0.2, "field": 0.0, "temperature": 1.0, "t": 1, "mean_m": 0.2, "var_m": 0.01, "n": 5},
                {"model": "model_2", "coupling": 0.2, "field": 0.0, "temperature": 1.0, "t": 0, "mean_m": 0.1, "var_m": 0.01, "n": 5},
                {"model": "model_2", "coupling": 0.2, "field": 0.0, "temperature": 1.0, "t": 1, "mean_m": 0.3, "var_m": 0.02, "n": 5},
            ]
            metrics = compute_metrics_for_point(rows, point=(0.2, 0.0, 1.0), model="model_2", runtime_map=runtime_map)
            self.assertAlmostEqual(float(metrics["runtime_seconds"]), 1.0)
            self.assertAlmostEqual(float(metrics["runtime_ratio_vs_model_1"]), 2.0)


if __name__ == "__main__":
    unittest.main()
