"""Unit tests for plot_summary_magnetization_grid helpers."""

import tempfile
import unittest
from pathlib import Path

from python_demos.stage3_analyze.plot_summary_magnetization_grid import (
    compute_metrics_against_model_1,
    convergence_time,
    list_models,
    list_param_points,
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

    def test_metrics_vs_model_1_and_csv(self):
        rows = [
            {"model": "model_1", "coupling": 0.2, "field": 0.0, "temperature": 1.0, "t": 0, "mean_m": 0.0, "var_m": 0.10, "n": 10},
            {"model": "model_1", "coupling": 0.2, "field": 0.0, "temperature": 1.0, "t": 1, "mean_m": 0.2, "var_m": 0.08, "n": 10},
            {"model": "model_1", "coupling": 0.2, "field": 0.0, "temperature": 1.0, "t": 2, "mean_m": 0.4, "var_m": 0.06, "n": 10},
            {"model": "model_2", "coupling": 0.2, "field": 0.0, "temperature": 1.0, "t": 0, "mean_m": 0.1, "var_m": 0.11, "n": 10},
            {"model": "model_2", "coupling": 0.2, "field": 0.0, "temperature": 1.0, "t": 1, "mean_m": 0.3, "var_m": 0.09, "n": 10},
            {"model": "model_2", "coupling": 0.2, "field": 0.0, "temperature": 1.0, "t": 2, "mean_m": 0.5, "var_m": 0.07, "n": 10},
        ]
        metrics = compute_metrics_against_model_1(
            rows=rows,
            points=[(0.2, 0.0, 1.0)],
            models=["model_1", "model_2"],
            transient_frac=0.5,
            steady_window=2,
            convergence_tol=0.5,
        )
        self.assertEqual(len(metrics), 2)
        m1 = next(m for m in metrics if m["model"] == "model_1")
        m2 = next(m for m in metrics if m["model"] == "model_2")
        self.assertAlmostEqual(float(m1["transient_rmse_vs_model_1"]), 0.0)
        self.assertGreater(float(m2["transient_rmse_vs_model_1"]), 0.0)
        self.assertIn("runtime_seconds", m2)

        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "metrics.csv"
            write_metrics_csv(out, metrics)
            text = out.read_text(encoding="utf-8")
            self.assertIn("variance_mismatch_vs_model_1", text)

    def test_convergence_time(self):
        self.assertEqual(convergence_time([0.0, 0.1, 0.11, 0.1], steady_mean=0.1, tol=0.02), 1)


if __name__ == "__main__":
    unittest.main()
