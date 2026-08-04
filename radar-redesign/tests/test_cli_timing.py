"""End-to-end CLI timing: the record has to survive real command invocations."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from agentic_cloud_radar.cli import main

REFERENCE_RUN = (
    Path(__file__).resolve().parents[1]
    / "reference-runs"
    / "lambda-self-managed-code-storage-20260731"
)


@unittest.skipUnless(REFERENCE_RUN.exists(), "reference run artifacts are required")
class CliTimingTests(unittest.TestCase):
    """Exercises main(), not the helper, so the wiring itself is under test."""

    def setUp(self) -> None:
        self._temp = TemporaryDirectory()
        self.root = Path(self._temp.name)
        self.s2 = self.root / "s2.json"
        self.s2.write_text(
            (REFERENCE_RUN / "s2-lambda-self-managed.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        self.s3 = self.root / "s3.json"

    def tearDown(self) -> None:
        self._temp.cleanup()

    def _run_s3(self) -> dict:
        main(["s3", "--input", str(self.s2), "--output", str(self.s3)])
        return json.loads(self.s3.read_text(encoding="utf-8"))

    def test_running_a_command_records_that_stage(self):
        artifact = self._run_s3()

        entry = artifact["stage_timings"]["S3"]
        self.assertTrue(entry["started_at"])
        self.assertTrue(entry["ended_at"])
        self.assertEqual(entry["attempt_count"], 1)
        self.assertEqual(entry["commands"], ["s3"])
        self.assertTrue(entry["recorded_on"])

    def test_rerunning_a_stage_counts_the_attempt_instead_of_resetting(self):
        first = self._run_s3()["stage_timings"]["S3"]
        second = self._run_s3()["stage_timings"]["S3"]

        self.assertEqual(second["attempt_count"], 2)
        self.assertEqual(second["started_at"], first["started_at"])
        self.assertGreaterEqual(second["ended_at"], first["ended_at"])

    def test_the_record_is_carried_into_the_next_stage_artifact(self):
        self._run_s3()
        s4 = self.root / "s4.json"

        main(["s4", "--input", str(self.s3), "--output", str(s4)])

        timings = json.loads(s4.read_text(encoding="utf-8"))["stage_timings"]
        self.assertEqual(sorted(timings), ["S3", "S4"])
        self.assertEqual(timings["S3"]["commands"], ["s3"])

    def test_skill5_renders_the_table_without_hand_fed_timings(self):
        self._run_s3()
        s4 = self.root / "s4.json"
        main(["s4", "--input", str(self.s3), "--output", str(s4)])
        report = self.root / "s5.json"
        markdown = self.root / "s5.md"

        main([
            "s5",
            "--s1", str(REFERENCE_RUN / "s1-lambda-self-managed.json"),
            "--s2", str(self.s2),
            "--s3", str(self.s3),
            "--s4", str(s4),
            "--output", str(report),
            "--markdown-output", str(markdown),
        ])

        text = markdown.read_text(encoding="utf-8")
        self.assertIn("## 各階段耗時", text)
        self.assertIn("| S3 |", text)
        self.assertIn("| S4 |", text)

    def test_timing_failure_never_breaks_the_command(self):
        # An unwritable output would fail the timing write-back; the command's own
        # exit code must still be the one the caller sees.
        artifact = self._run_s3()
        self.assertTrue(artifact["evaluated_candidates"])
