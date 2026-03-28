"""Unit tests for visualize_trajectory_matching helpers."""

import csv
import tempfile
import unittest
from pathlib import Path

from python_demos.visualize_trajectory_matching import (
    load_raw,
    mean_series,
    nearest_map_row,
    select_seed_keys,
)


class VisualizeMatchingTests(unittest.TestCase):
    def test_nearest_map_row(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "map.csv"
            path.write_text(
                "source_coupling,source_field,source_temperature,target_coupling,target_field,target_temperature,fit_error\n"
                "0.2,0.0,1.0,0.3,0.1,0.9,0.01\n"
                "0.8,0.0,1.0,0.7,0.1,0.9,0.02\n",
                encoding="utf-8",
            )
            row = nearest_map_row(path, 0.21, 0.0, 1.0)
            self.assertAlmostEqual(row["target_coupling"], 0.3)

    def test_load_raw_and_seed_selection(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "raw.csv"
            with path.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(
                    f,
                    fieldnames=[
                        "model",
                        "coupling",
                        "field",
                        "temperature",
                        "seed",
                        "initial_up_count",
                        "initial_up_fraction",
                        "t",
                        "m",
                    ],
                )
                w.writeheader()
                for seed, frac in [(0, 0.25), (1, 0.75)]:
                    for t, m in [(0, 2 * frac - 1), (1, 0.0)]:
                        w.writerow(
                            {
                                "model": "model_1",
                                "coupling": 0.2,
                                "field": 0.0,
                                "temperature": 1.0,
                                "seed": seed,
                                "initial_up_count": int(frac * 4),
                                "initial_up_fraction": frac,
                                "t": t,
                                "m": m,
                            }
                        )
            series, init_frac = load_raw(path)
            selected = select_seed_keys(series, init_frac, "model_1", 0.2, 0.0, 1.0, 0.7, 0.2, 10)
            self.assertEqual(len(selected), 1)
            ts, mu = mean_series(selected, series)
            self.assertEqual(ts, [0, 1])
            self.assertEqual(len(mu), 2)


if __name__ == "__main__":
    unittest.main()
