"""Unit tests for ising_magnetization_compare helpers."""

import csv
import tempfile
import unittest
from pathlib import Path

from python_demos.foundation.ising_four_models import IsingParams
from python_demos.stage1_generate.ising_magnetization_compare import (
    linspace,
    mean_grid_value,
    trajectory_magnetizations,
    write_raw,
)


class MagnetizationCompareTests(unittest.TestCase):
    def test_linspace(self):
        self.assertEqual(linspace(0.0, 1.0, 3), [0.0, 0.5, 1.0])

    def test_mean_grid_value(self):
        self.assertAlmostEqual(mean_grid_value([[1.0, -1.0], [0.0, 0.0]]), 0.0)

    def test_trajectory_shapes_and_init_metadata(self):
        traj, up_count, up_frac = trajectory_magnetizations(
            params=IsingParams(), rows=2, cols=2, steps=3, seed=7, mixing=0.2
        )
        self.assertEqual(set(traj.keys()), {"model_1", "model_2", "model_3", "model_4"})
        for series in traj.values():
            self.assertEqual(len(series), 4)
        self.assertGreaterEqual(up_count, 0)
        self.assertGreaterEqual(up_frac, 0.0)
        self.assertLessEqual(up_frac, 1.0)

    def test_write_raw_includes_init_fields(self):
        rows = [
            {
                "model": "model_1",
                "coupling": 0.2,
                "field": 0.0,
                "temperature": 1.0,
                "seed": 0,
                "initial_up_count": 2,
                "initial_up_fraction": 0.5,
                "t": 0,
                "m": 0.0,
            }
        ]
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "raw.csv"
            write_raw(out, rows)
            with out.open("r", encoding="utf-8") as f:
                parsed = list(csv.DictReader(f))
            self.assertEqual(parsed[0]["initial_up_count"], "2")
            self.assertEqual(parsed[0]["initial_up_fraction"], "0.5")


if __name__ == "__main__":
    unittest.main()
