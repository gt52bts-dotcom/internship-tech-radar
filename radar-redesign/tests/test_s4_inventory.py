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
