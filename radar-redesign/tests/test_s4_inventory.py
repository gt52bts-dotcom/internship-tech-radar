"""Skill 4 review evidence: inventory, quote reconciliation, permissions, timing."""

from __future__ import annotations

import unittest

from agentic_cloud_radar.pipeline_timing import build_stage_timings
from agentic_cloud_radar.s4_inventory import build_resource_inventory, reconcile_quote_against_resources


RUNTIME = {"run_id": "run-1", "stack_name": "radar-run-1", "region": "ap-southeast-1"}
RESOURCES = [
    {
        "LogicalResourceId": "CodeBucket",
        "ResourceType": "AWS::S3::Bucket",
        "ResourceStatus": "CREATE_COMPLETE",
        "PhysicalResourceId": "radar-run-1-codebucket-abcdef123456",
    },
    {
        "LogicalResourceId": "Handler",
        "ResourceType": "AWS::Lambda::Function",
        "ResourceStatus": "CREATE_COMPLETE",
        "PhysicalResourceId": "radar-run-1-handler",
    },
    {
        "LogicalResourceId": "HandlerRole",
        "ResourceType": "AWS::IAM::Role",
        "ResourceStatus": "CREATE_COMPLETE",
        "PhysicalResourceId": "radar-run-1-handler-role",
    },
]


class ResourceInventoryTests(unittest.TestCase):
    def test_inventory_redacts_physical_identifiers(self):
        inventory = build_resource_inventory(RUNTIME, RESOURCES)

        bucket = inventory["resources"][0]
        self.assertEqual(bucket["logical_id"], "CodeBucket")
        self.assertNotIn("codebucket", bucket["physical_id_redacted"])
        self.assertTrue(bucket["physical_id_redacted"].startswith("rada"))

    def test_inventory_reads_region_from_deployment_target_region(self):
        inventory = build_resource_inventory(
            {
                "run_id": "run-1",
                "deployment": {"stack_name": "radar-run-1", "target_region": "ap-southeast-1"},
            },
            RESOURCES,
        )

        self.assertEqual(inventory["stack_name"], "radar-run-1")
        self.assertEqual(inventory["region"], "ap-southeast-1")

    def test_deployed_resource_missing_from_the_quote_is_flagged(self):
        quote = {"priced_resource_types": ["AWS::S3::Bucket", "AWS::Lambda::Function"]}

        reconciliation = reconcile_quote_against_resources(quote, build_resource_inventory(RUNTIME, RESOURCES)["resources"])

        self.assertEqual(reconciliation["status"], "quote_incomplete")
        self.assertEqual(reconciliation["deployed_not_quoted"], ["AWS::IAM::Role"])

    def test_consistent_quote_reports_no_gap(self):
        quote = {
            "priced_resource_types": [
                "AWS::S3::Bucket",
                "AWS::Lambda::Function",
                "AWS::IAM::Role",
            ]
        }

        reconciliation = reconcile_quote_against_resources(quote, build_resource_inventory(RUNTIME, RESOURCES)["resources"])

        self.assertEqual(reconciliation["status"], "consistent")
        self.assertEqual(reconciliation["deployed_not_quoted"], [])

    def test_priced_log_group_is_not_treated_as_a_missing_deployment(self):
        quote = {
            "priced_resource_types": [
                "AWS::S3::Bucket",
                "AWS::Lambda::Function",
                "AWS::IAM::Role",
                "AWS::Logs::LogGroup",
            ]
        }

        reconciliation = reconcile_quote_against_resources(quote, build_resource_inventory(RUNTIME, RESOURCES)["resources"])

        log_row = next(row for row in reconciliation["rows"] if row["resource_type"] == "AWS::Logs::LogGroup")
        self.assertEqual(log_row["verdict"], "quoted_implicit_resource")
        self.assertEqual(reconciliation["status"], "consistent")

    def test_hash_covers_what_the_human_confirms(self):
        first = build_resource_inventory(RUNTIME, RESOURCES, captured_at=None)
        changed = build_resource_inventory(RUNTIME, RESOURCES[:2], captured_at=None)

        self.assertNotEqual(first["inventory_sha256"], changed["inventory_sha256"])

    def test_permission_surface_records_actions_and_services(self):
        inventory = build_resource_inventory(
            RUNTIME, RESOURCES, permission_actions=["s3:PutObject", "lambda:InvokeFunction", "s3:PutObject"]
        )

        surface = inventory["permission_surface"]
        self.assertEqual(surface["status"], "recorded")
        self.assertEqual(surface["action_count"], 2)
        self.assertEqual(surface["services"], ["lambda", "s3"])

    def test_missing_permission_record_stays_unknown(self):
        surface = build_resource_inventory(RUNTIME, RESOURCES)["permission_surface"]

        self.assertEqual(surface["status"], "not_recorded")
        self.assertEqual(surface["actions"], [])


class StageTimingTests(unittest.TestCase):
    STAGES = {
        "S1": {"started_at": "2026-08-01T00:00:00+00:00", "ended_at": "2026-08-01T00:00:20+00:00"},
        "S3": {
            "started_at": "2026-08-01T00:01:00+00:00",
            "ended_at": "2026-08-01T00:01:10+00:00",
            "human_wait_seconds": 3600,
            "human_gate": "poc_decision_gate",
        },
    }

    def test_machine_and_human_time_are_reported_separately(self):
        timings = build_stage_timings(self.STAGES)

        self.assertEqual(timings["machine_seconds_total"], 30.0)
        self.assertEqual(timings["human_wait_seconds_total"], 3600.0)
        self.assertGreater(timings["human_share"], 0.99)

    def test_unrecorded_stages_stay_visible(self):
        rows = {row["stage"]: row["status"] for row in build_stage_timings(self.STAGES)["rows"]}

        self.assertEqual(rows["S2"], "not_recorded")
        self.assertEqual(rows["S5"], "not_recorded")

    def test_time_to_first_success_spans_from_the_first_stage(self):
        timings = build_stage_timings(self.STAGES, first_success_at="2026-08-01T02:00:00+00:00")

        self.assertEqual(timings["time_to_first_success_seconds"], 7200.0)


class StageRecordingTests(unittest.TestCase):
    """The accumulated per-stage record, as written by the CLI wrapper."""

    def test_first_run_opens_a_stage_with_one_attempt(self):
        from agentic_cloud_radar.pipeline_timing import merge_stage_record

        timings = merge_stage_record({}, "S3", "2026-08-01T00:00:00+00:00", "2026-08-01T00:00:05+00:00", "s3")

        self.assertEqual(timings["S3"]["attempt_count"], 1)
        self.assertEqual(timings["S3"]["commands"], ["s3"])
        self.assertEqual(len(timings["S3"]["recorded_on"]), 1)

    def test_rerun_keeps_the_first_start_and_takes_the_last_end(self):
        from agentic_cloud_radar.pipeline_timing import merge_stage_record

        first = merge_stage_record({}, "S3", "2026-08-01T00:00:00+00:00", "2026-08-01T00:00:05+00:00", "s3")
        second = merge_stage_record(first, "S3", "2026-08-01T01:00:00+00:00", "2026-08-01T01:00:09+00:00", "s3")

        self.assertEqual(second["S3"]["attempt_count"], 2)
        self.assertEqual(second["S3"]["started_at"], "2026-08-01T00:00:00+00:00")
        self.assertEqual(second["S3"]["ended_at"], "2026-08-01T01:00:09+00:00")

    def test_upstream_stages_are_carried_forward_untouched(self):
        from agentic_cloud_radar.pipeline_timing import merge_stage_record

        upstream = merge_stage_record({}, "S1", "2026-08-01T00:00:00+00:00", "2026-08-01T00:00:22+00:00", "s1")
        merged = merge_stage_record(upstream, "S2", "2026-08-01T00:01:00+00:00", "2026-08-01T00:01:17+00:00", "s2")

        self.assertEqual(merged["S1"]["ended_at"], "2026-08-01T00:00:22+00:00")
        self.assertEqual(sorted(merged), ["S1", "S2"])

    def test_human_wait_is_derived_from_when_the_gate_was_decided(self):
        from agentic_cloud_radar.pipeline_timing import merge_stage_record, set_human_wait

        timings = merge_stage_record({}, "S3", "2026-08-01T00:00:00+00:00", "2026-08-01T00:00:10+00:00", "s3")
        timings = set_human_wait(timings, "S3", "poc_decision_gate", "2026-08-01T01:30:10+00:00")

        self.assertEqual(timings["S3"]["human_wait_seconds"], 5400.0)
        self.assertEqual(timings["S3"]["human_gate"], "poc_decision_gate")

    def test_missing_gate_decision_leaves_human_wait_unrecorded(self):
        from agentic_cloud_radar.pipeline_timing import merge_stage_record, set_human_wait

        timings = merge_stage_record({}, "S3", "2026-08-01T00:00:00+00:00", "2026-08-01T00:00:10+00:00", "s3")
        timings = set_human_wait(timings, "S3", "poc_decision_gate", None)

        self.assertNotIn("human_wait_seconds", timings["S3"])

    def test_cross_host_spans_are_flagged_rather_than_presented_as_precise(self):
        timings = {
            "S4": {
                "started_at": "2026-08-01T00:00:00+00:00",
                "ended_at": "2026-08-01T00:10:00+00:00",
                "recorded_on": ["aaaa1111", "bbbb2222"],
                "attempt_count": 2,
            }
        }

        report = build_stage_timings(timings)

        self.assertEqual(report["cross_host_stages"], ["S4"])
        self.assertIn("時鐘差異", report["measurement_note"])

    def test_single_host_run_carries_no_measurement_caveat(self):
        timings = {
            "S1": {
                "started_at": "2026-08-01T00:00:00+00:00",
                "ended_at": "2026-08-01T00:00:20+00:00",
                "recorded_on": ["aaaa1111"],
                "attempt_count": 1,
            }
        }

        report = build_stage_timings(timings)

        self.assertEqual(report["cross_host_stages"], [])
        self.assertEqual(report["measurement_note"], "")
