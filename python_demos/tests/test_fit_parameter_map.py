"""Unit tests for fit_parameter_map helpers."""

import json
import tempfile
import unittest
from pathlib import Path

from python_demos.stage2_map.fit_parameter_map import (
    _bounded_to_real,
    _real_to_bounded,
    fit_affine_coefficients,
    fit_affine_coefficients_tanh_normalized,
    fit_nearest_neighbor_map,
    load_manifold,
    series_distance,
    write_affine_json,
)


class FitParameterMapTests(unittest.TestCase):
    def test_series_distance_zero_for_identical(self):
        s = {0: (0.1, 0.01), 1: (0.2, 0.02)}
        self.assertAlmostEqual(series_distance(s, s, mean_w=1.0, var_w=1.0), 0.0)

    def test_load_and_fit_nearest_neighbor(self):
        with tempfile.TemporaryDirectory() as td:
            csv_path = Path(td) / "summary.csv"
            csv_path.write_text(
                "model,coupling,field,temperature,t,mean_m,var_m,n\n"
                "model_1,1.0,0.0,1.0,0,0.0,0.1,5\n"
                "model_1,1.0,0.0,1.0,1,0.2,0.1,5\n"
                "model_2,0.8,0.1,1.0,0,0.0,0.1,5\n"
                "model_2,0.8,0.1,1.0,1,0.2,0.1,5\n",
                encoding="utf-8",
            )
            manifold = load_manifold(csv_path)
            rows = fit_nearest_neighbor_map(manifold, "model_1", "model_2", mean_w=1.0, var_w=1.0)
            self.assertEqual(len(rows), 1)
            self.assertAlmostEqual(rows[0]["fit_error"], 0.0)
            self.assertAlmostEqual(rows[0]["target_coupling"], 0.8)

    def test_affine_json_output(self):
        rows = [
            {
                "source_coupling": 0.0,
                "source_field": 0.0,
                "source_temperature": 1.0,
                "target_coupling": 1.0,
                "target_field": 2.0,
                "target_temperature": 3.0,
                "fit_error": 0.1,
            },
            {
                "source_coupling": 1.0,
                "source_field": 0.0,
                "source_temperature": 1.0,
                "target_coupling": 2.0,
                "target_field": 3.0,
                "target_temperature": 4.0,
                "fit_error": 0.1,
            },
            {
                "source_coupling": 0.0,
                "source_field": 1.0,
                "source_temperature": 1.0,
                "target_coupling": 1.5,
                "target_field": 2.5,
                "target_temperature": 3.5,
                "fit_error": 0.1,
            },
            {
                "source_coupling": 1.0,
                "source_field": 1.0,
                "source_temperature": 1.0,
                "target_coupling": 2.5,
                "target_field": 3.5,
                "target_temperature": 4.5,
                "fit_error": 0.1,
            },
            {
                "source_coupling": 0.5,
                "source_field": 0.2,
                "source_temperature": 2.0,
                "target_coupling": 2.1,
                "target_field": 3.1,
                "target_temperature": 4.1,
                "fit_error": 0.1,
            },
        ]
        coeffs = fit_affine_coefficients(rows)
        self.assertIn("target_coupling", coeffs)

        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "affine.json"
            write_affine_json(
                out,
                coeffs,
                "model_1",
                "model_2",
                fit_space="tanh-normalized",
                bounds={"coupling": (-1.0, 1.0), "field": (-1.0, 1.0), "temperature": (0.0, 1.0)},
            )
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["source_model"], "model_1")
            self.assertEqual(payload["target_model"], "model_2")
            self.assertEqual(payload["fit_space"], "tanh-normalized")
            self.assertIn("bounds", payload)

    def test_tanh_normalized_round_trip(self):
        x = 0.3
        z = _bounded_to_real(x, -1.0, 1.0)
        x_back = _real_to_bounded(z, -1.0, 1.0)
        self.assertAlmostEqual(x, x_back, places=6)

    def test_tanh_normalized_affine_fit_smoke(self):
        rows = [
            {
                "source_coupling": -0.6,
                "source_field": -0.3,
                "source_temperature": 0.2,
                "target_coupling": -0.5,
                "target_field": -0.1,
                "target_temperature": 0.25,
                "fit_error": 0.1,
            },
            {
                "source_coupling": 0.6,
                "source_field": 0.3,
                "source_temperature": 0.8,
                "target_coupling": 0.5,
                "target_field": 0.1,
                "target_temperature": 0.75,
                "fit_error": 0.1,
            },
            {
                "source_coupling": 0.0,
                "source_field": -0.2,
                "source_temperature": 0.5,
                "target_coupling": 0.1,
                "target_field": -0.1,
                "target_temperature": 0.55,
                "fit_error": 0.1,
            },
            {
                "source_coupling": -0.2,
                "source_field": 0.1,
                "source_temperature": 0.7,
                "target_coupling": -0.1,
                "target_field": 0.2,
                "target_temperature": 0.65,
                "fit_error": 0.1,
            },
        ]
        coeffs = fit_affine_coefficients_tanh_normalized(
            rows,
            bounds={"coupling": (-1.0, 1.0), "field": (-1.0, 1.0), "temperature": (0.0, 1.0)},
        )
        self.assertIn("target_coupling", coeffs)
        self.assertEqual(len(coeffs["target_field"]), 4)


if __name__ == "__main__":
    unittest.main()
