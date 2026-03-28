"""Unit tests for report pipeline orchestration."""

import unittest
from unittest.mock import patch

from python_demos.stage4_report import run_report_pipeline as rrp


class RunReportPipelineTests(unittest.TestCase):
    def test_parse_defaults(self):
        with patch("sys.argv", ["run_report_pipeline.py"]):
            args = rrp.parse_args()
        self.assertEqual(args.artifact_prefix, "artifacts")
        self.assertFalse(args.skip_plots)

    def test_skip_plots_reduces_command_count(self):
        calls = []

        def fake_run(cmd, check):
            calls.append(cmd)

        with patch("subprocess.run", side_effect=fake_run):
            with patch(
                "sys.argv",
                [
                    "run_report_pipeline.py",
                    "--artifact-prefix",
                    "/tmp/a",
                    "--skip-plots",
                    "--steps",
                    "1",
                    "--seeds",
                    "1",
                ],
            ):
                rrp.main()

        # compare, fit, renorm, manifest
        self.assertEqual(len(calls), 4)


if __name__ == "__main__":
    unittest.main()
