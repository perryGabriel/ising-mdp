"""Unit tests for renormalization and manifest helpers."""

import json
import tempfile
import unittest
from pathlib import Path

from python_demos.stage4_report.generate_figure_manifest import build_manifest, sha256_file
from python_demos.stage3_analyze.renormalization_operator_demo import coarse_evolution_from_m0, project_dist_to_mean_m
from python_demos.foundation.ising_four_models import IsingParams


class RenormAndManifestTests(unittest.TestCase):
    def test_project_dist_to_mean_m(self):
        dist = {(1, -1): 1.0}
        self.assertAlmostEqual(project_dist_to_mean_m(dist), 0.0)

    def test_coarse_evolution_length(self):
        series = coarse_evolution_from_m0(n_spins=4, params=IsingParams(), m0=0.0, steps=5)
        self.assertEqual(len(series), 6)
        for m in series:
            self.assertGreaterEqual(m, -1.0)
            self.assertLessEqual(m, 1.0)

    def test_manifest_generation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            art = root / "artifacts"
            art.mkdir()
            p = art / "x.csv"
            p.write_text("a,b\n1,2\n", encoding="utf-8")
            h = sha256_file(p)
            manifest = build_manifest(art)
            self.assertEqual(len(manifest["artifacts"]), 1)
            self.assertEqual(manifest["artifacts"][0]["sha256"], h)

            out = root / "manifest.json"
            out.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
