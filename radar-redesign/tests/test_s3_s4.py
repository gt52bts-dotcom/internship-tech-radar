import unittest
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from agentic_cloud_radar.s3 import build_evaluate
from agentic_cloud_radar.s4 import build_validate
from agentic_cloud_radar.s4_deployer import (
    DeploymentError,
    _get_s3_object_with_retry,
    _matches_run_identity,
    _stack_status_or_none,
    build_approval_template,
    build_console_review_packet,
    build_deployment_context,
    record_console_review,
)


def _sample_s2():
    return {
        "schema_version": "s2.comparison.v2",
        "run_id": "unit-test-run",
        "stage": "S2",
        "status": "ready_for_human_shortlist",
        "compared_at": "2026-07-29T00:00:00+00:00",
        "candidates": [
            {
                "candidate_id": "CAND-1",
                "title": "Example GA AWS Feature",
                "source_url": "https://aws.amazon.com/blogs/example/example-ga-feature/",
                "source_provenance": {
                    "official_aws_source": True,
                    "public_open_source": False,
                    "external_fetch_performed": True,
                },
                "comparison_dimensions": {
                    "technology_scope": {"services_detected": ["S3"], "status": "source_detected"},
                    "source_backed_capabilities": {"status": "source_excerpt_available"},
                    "environment_signals": {
                        "source_indicated_contexts": ["existing_compute_workload"],
                    },
                    "target_region_eligibility": {
                        "target_region": "ap-southeast-1",
                        "status": "region_unknown",
                        "severity": "warning",
                        "blocks_s3": False,
                        "blocks_paid_poc": True,
                    },
                    "unknowns_and_next_validation_question": {
                        "unknowns": [
                            "Official pricing evidence has not been established for this candidate.",
                            "Feature-level availability in ap-southeast-1 has not been officially verified.",
                        ],
                    },
                },
                "proposal_card": {
                    "improvement_hypothesis": {
                        "potential_vectors": [{"type": "workflow_automation"}],
                    },
                    "validation_design": {
                        "before_measurements": ["Baseline workflow time."],
                        "after_measurements": ["Workflow time after validation."],
                        "minimum_success_evidence": ["Same workload before/after comparison."],
                        "stop_conditions": ["No safe non-production environment is available."],
                    },
                },
                "evidence_coverage": {
                    "primary_source_fetched": True,
                    "official_aws_primary_source": True,
                    "official_ga_evidence": True,
                    "official_docs_linked": True,
                    "official_pricing_linked": False,
                    "verified_dimension_count": 5,
                    "verified_dimension_total": 8,
                },
                "linked_evidence": {"linked_sources": []},
                "evidence_limits": [],
            }
        ],
    }


def _deployable_s2():
    sample = deepcopy(_sample_s2())
    candidate = sample["candidates"][0]
    candidate["title"] = "Launching S3 Files, making S3 buckets accessible as file systems"
    candidate["comparison_dimensions"]["target_region_eligibility"] = {
        "target_region": "ap-southeast-1",
        "status": "available_ap_southeast_1",
        "severity": "info",
        "blocks_s3": False,
        "blocks_paid_poc": False,
    }
    return sample


def _shortlist():
    return {
        "selected_candidate_ids": ["CAND-1"],
        "selected_by": "Cleo",
    }


def _console_evidence_for(runtime):
    deployment = runtime.get("deployment") or {}
    return {
        "schema_version": "s4.console-review-evidence.v1",
        "run_id": runtime["run_id"],
        "review_target": {
            "run_id": runtime["run_id"],
            "stack_name": deployment.get("stack_name"),
            "target_region": deployment.get("target_region"),
            "recipe": deployment.get("recipe"),
        },
        "capture_contract": {
            "redaction_order": "hide_console_chrome_before_capture_then_hash_redacted_png",
            "redacted_before_hash": True,
            "hash_scope": "redacted_png",
            "automated_image_understanding": False,
            "human_confirmation_record_only": True,
        },
        "screenshots": [
            {
                "view": "infrastructure_composer",
                "screenshot_ref": "protected://review/infrastructure-composer.png",
                "sha256": "a" * 64,
                "captured_at": "2026-07-31T09:00:00+08:00",
                "shared_via": "conversation",
                "redacted": True,
                "hash_scope": "redacted_png",
                "stack_name": deployment.get("stack_name"),
                "target_region": deployment.get("target_region"),
            }
        ],
    }


class S3S4Tests(unittest.TestCase):
    def test_s3_stops_without_human_shortlist(self):
        result = build_evaluate(_sample_s2()).to_dict()

        self.assertEqual(result["status"], "needs_human_shortlist")
        self.assertEqual(result["evaluated_candidates"], [])

    def test_s3_records_a_blocked_poc_when_region_and_quote_are_not_ready(self):
        request = _shortlist()

        result = build_evaluate(_sample_s2(), request).to_dict()

        self.assertEqual(result["status"], "evaluated")
        evaluated = result["evaluated_candidates"][0]
        self.assertFalse(evaluated["recommend_poc"])
        self.assertEqual(evaluated["region_status"]["status"], "region_unknown")
        self.assertFalse(evaluated["region_status"]["blocks_s3"])
        self.assertTrue(evaluated["region_status"]["requires_region_confirmation"])
        self.assertEqual(evaluated["s4_path"], "not_recommended")
        self.assertIn("target_region_support_not_verified", evaluated["poc_review_notes"])
        self.assertEqual(evaluated["cost_estimate"]["status"], "needs_registered_cost_model")

    def test_s3_public_evidence_mode_requires_only_a_candidate_selection(self):
        request = {"selected_candidate_ids": ["CAND-1"], "selected_by": "Cleo"}

        result = build_evaluate(_sample_s2(), request).to_dict()

        self.assertEqual(result["status"], "evaluated")
        gate = result["human_shortlist_gate"]
        self.assertEqual(gate["evaluation_mode"], "public_evidence")
        evaluated = result["evaluated_candidates"][0]
        self.assertFalse(evaluated["recommend_poc"])
        self.assertEqual(evaluated["assessment_scope"]["company_fit"], "not_assessed")
        self.assertNotIn("paid_poc_context_gaps", evaluated)

    def test_s3_rejects_multiple_selected_candidates(self):
        request = {"selected_candidate_ids": ["CAND-1", "CAND-2"], "selected_by": "Cleo"}

        result = build_evaluate(_sample_s2(), request).to_dict()

        self.assertEqual(result["status"], "needs_human_shortlist")
        self.assertEqual(result["human_shortlist_gate"]["status"], "invalid")
        self.assertIn("exactly one candidate", result["human_shortlist_gate"]["message"])

    def test_s4_does_not_create_a_second_low_risk_track(self):
        request = {"selected_candidate_ids": ["CAND-1"], "selected_by": "Cleo"}
        s3 = build_evaluate(_sample_s2(), request).to_dict()

        result = build_validate(s3).to_dict()

        self.assertEqual(result["status"], "no_poc_candidates")
        validated = result["validated_candidates"][0]
        self.assertFalse(validated["recommend_poc"])
        self.assertEqual(validated["validation_status"], "not_recommended_for_poc")

    def test_s4_waits_for_approval_after_skill3_recommends_poc(self):
        s3 = build_evaluate(_deployable_s2(), _shortlist()).to_dict()

        result = build_validate(s3).to_dict()

        self.assertEqual(result["status"], "awaiting_poc_approval")
        validated = result["validated_candidates"][0]
        self.assertEqual(validated["validation_status"], "awaiting_poc_approval")
        self.assertEqual(validated["cleanup_status"], "not_applicable_no_cloud_resources_created")
        self.assertFalse(validated["automatic_poc_start"])
        self.assertIn("approved_by_present", validated["pending_checks"])

    def test_s4_requires_explicit_deployment_authorization(self):
        s3 = build_evaluate(_deployable_s2(), _shortlist()).to_dict()
        approval = {
            "approved_by": "Cleo",
            "selected_candidate_id": "CAND-1",
            "approved_cost_ceiling_usd": 0.2,
        }

        result = build_validate(s3, approval).to_dict()

        self.assertEqual(result["status"], "awaiting_poc_approval")
        self.assertIn("deployment_authorized", result["validated_candidates"][0]["pending_checks"])

    def test_skill3_produces_one_complete_quote_before_recommending_poc(self):
        result = build_evaluate(_deployable_s2(), _shortlist()).to_dict()

        evaluated = result["evaluated_candidates"][0]
        self.assertTrue(evaluated["recommend_poc"])
        self.assertEqual(evaluated["s4_path"], "poc")
        self.assertEqual(evaluated["cost_estimate"]["status"], "estimated")
        self.assertEqual(evaluated["cost_estimate"]["estimated_usd"], 0.04719)
        self.assertEqual(evaluated["cost_estimate"]["recommended_approval_ceiling_usd"], 0.2)

    def test_skill3_produces_a_lambda_recipe_quote(self):
        s2 = _deployable_s2()
        s2["candidates"][0]["title"] = "AWS Lambda self-managed S3 code storage"
        s2["candidates"][0]["source_url"] = "https://aws.amazon.com/about-aws/whats-new/2026/07/lambda-self-managed-code-storage/"

        evaluated = build_evaluate(s2, _shortlist()).to_dict()["evaluated_candidates"][0]

        self.assertEqual(evaluated["cost_estimate"]["status"], "estimated")
        self.assertEqual(evaluated["cost_estimate"]["quote"]["recipe"], "lambda_self_managed_s3_code_storage_cdk")
        self.assertTrue(evaluated["recommend_poc"])

    def test_s4_deployment_context_requires_matching_lineage_and_registered_recipe(self):
        evaluate = build_evaluate(_deployable_s2(), _shortlist()).to_dict()
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            s1 = {"stage": "S1", "run_id": "unit-test-run", "candidates": [{"candidate_id": "CAND-1"}]}
            s2 = _deployable_s2()
            s3_path = root / "s3.json"
            paths = {"s1": root / "s1.json", "s2": root / "s2.json", "s3": s3_path}
            for key, payload in (("s1", s1), ("s2", s2), ("s3", evaluate)):
                paths[key].write_text(json.dumps(payload), encoding="utf-8")
            approval = {
                "approved_by": "Cleo",
                "selected_candidate_id": "CAND-1",
                "deployment_authorized": True,
                "lineage": {**{f"{key}_artifact_path": str(path) for key, path in paths.items()}},
            }
            context = build_deployment_context(evaluate, approval)

        self.assertEqual(context["status"], "ready_for_manual_deployment")
        self.assertEqual(context["deployment"]["recipe"], "s3_files_cdk")
        self.assertEqual(len(context["lineage"]["source_artifacts"]), 3)
        self.assertEqual(context["s4_validation"]["cost_estimate"]["status"], "estimated")

    def test_s4_approval_template_is_generated_from_skill3(self):
        evaluate = build_evaluate(_deployable_s2(), _shortlist()).to_dict()

        approval = build_approval_template(evaluate, selected_candidate_id="CAND-1", approved_by="Cleo", authorize=True)

        self.assertEqual(approval["schema_version"], "s4.deployment-approval.v1")
        self.assertEqual(approval["run_id"], evaluate["run_id"])
        self.assertTrue(approval["deployment_authorized"])
        self.assertEqual(approval["approved_cost_ceiling_usd"], 0.2)
        self.assertFalse(approval["quote_snapshot"]["live_pricing_api_used"])

    def test_console_review_requires_infrastructure_composer_screenshot(self):
        runtime = {
            "schema_version": "s4.runtime-evidence.v3",
            "stage": "S4",
            "run_id": "unit-test-run",
            "status": "awaiting_console_review",
            "deployment": {"stack_name": "AgenticRadarS4ABC12345", "target_region": "ap-southeast-1", "recipe": "s3_files_cdk"},
            "console_review": {},
            "cleanup": {},
        }
        packet = build_console_review_packet(runtime)
        evidence = _console_evidence_for(runtime)

        reviewed = record_console_review(runtime, "Cleo", review_evidence=evidence, review_packet=packet)

        self.assertEqual(packet["required_screenshots"][0]["view"], "infrastructure_composer")
        self.assertIn("composer/home?region=ap-southeast-1", packet["review_target"]["composer_url"])
        self.assertIn("s4-capture-infrastructure-composer.mjs", packet["automation"]["command"])
        self.assertTrue(packet["automation"]["human_display_required"])
        self.assertFalse(packet["evidence_contract"]["automated_image_understanding"])
        self.assertEqual(reviewed["status"], "ready_for_cleanup")
        self.assertEqual(reviewed["console_review"]["status"], "confirmed")
        self.assertEqual(reviewed["console_review"]["evidence_status"], "captured_and_confirmed")
        self.assertTrue(reviewed["console_review"]["evidence"]["screenshots"][0]["redacted"])

    def test_console_review_rejects_missing_infrastructure_composer_screenshot(self):
        runtime = {
            "schema_version": "s4.runtime-evidence.v3",
            "stage": "S4",
            "run_id": "unit-test-run",
            "status": "awaiting_console_review",
            "deployment": {"stack_name": "AgenticRadarS4ABC12345", "target_region": "ap-southeast-1", "recipe": "s3_files_cdk"},
            "console_review": {},
            "cleanup": {},
        }
        packet = build_console_review_packet(runtime)
        evidence = _console_evidence_for(runtime)
        evidence["screenshots"][0]["view"] = "resource_inventory"

        with self.assertRaisesRegex(DeploymentError, "Infrastructure Composer"):
            record_console_review(runtime, "Cleo", review_evidence=evidence, review_packet=packet)

    def test_console_review_requires_packet_binding(self):
        runtime = {
            "schema_version": "s4.runtime-evidence.v3",
            "stage": "S4",
            "run_id": "unit-test-run",
            "status": "awaiting_console_review",
            "deployment": {"stack_name": "AgenticRadarS4ABC12345", "target_region": "ap-southeast-1", "recipe": "s3_files_cdk"},
            "console_review": {},
            "cleanup": {},
        }
        evidence = _console_evidence_for(runtime)

        with self.assertRaisesRegex(DeploymentError, "packet"):
            record_console_review(runtime, "Cleo", review_evidence=evidence)

    def test_s4_deployment_context_uses_defaults_without_environment_configuration(self):
        s2 = _sample_s2()
        s2["candidates"][0]["title"] = "Launching S3 Files, making S3 buckets accessible as file systems"
        evaluate = build_evaluate(s2, _shortlist()).to_dict()
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            paths = {"s1": root / "s1.json", "s2": root / "s2.json", "s3": root / "s3.json"}
            s1 = {"stage": "S1", "run_id": "unit-test-run", "candidates": [{"candidate_id": "CAND-1"}]}
            for key, payload in (("s1", s1), ("s2", s2), ("s3", evaluate)):
                paths[key].write_text(json.dumps(payload), encoding="utf-8")
            approval = {
                "approved_by": "Cleo", "selected_candidate_id": "CAND-1",
                "deployment_authorized": True,
                "region_warning_acknowledged": True,
                "lineage": {f"{key}_artifact_path": str(path) for key, path in paths.items()},
            }
            context = build_deployment_context(evaluate, approval)

        self.assertEqual(context["status"], "ready_for_manual_deployment")
        self.assertEqual(context["deployment"]["target_region"], "ap-southeast-1")
        self.assertTrue(context["success_criteria"])
        self.assertTrue(context["cleanup_scope"])

    def test_s4_deployment_context_blocks_unknown_region_without_acknowledgement(self):
        s2 = _sample_s2()
        s2["candidates"][0]["title"] = "Launching S3 Files, making S3 buckets accessible as file systems"
        evaluate = build_evaluate(s2, _shortlist()).to_dict()
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            paths = {"s1": root / "s1.json", "s2": root / "s2.json", "s3": root / "s3.json"}
            s1 = {"stage": "S1", "run_id": "unit-test-run", "candidates": [{"candidate_id": "CAND-1"}]}
            for key, payload in (("s1", s1), ("s2", s2), ("s3", evaluate)):
                paths[key].write_text(json.dumps(payload), encoding="utf-8")
            approval = {
                "approved_by": "Cleo", "selected_candidate_id": "CAND-1",
                "deployment_authorized": True,
                "lineage": {f"{key}_artifact_path": str(path) for key, path in paths.items()},
            }
            context = build_deployment_context(evaluate, approval)

        self.assertEqual(context["status"], "not_deployable")
        self.assertIn("target_region_not_verified_or_acknowledged", context["errors"])

    def test_cleanup_identity_must_be_derived_from_the_run(self):
        context = {"run_id": "unit-test-run"}
        suffix = hashlib.sha256(context["run_id"].encode("utf-8")).hexdigest()[:8]

        self.assertTrue(_matches_run_identity(context["run_id"], f"AgenticRadarS4{suffix.upper()}", f"agentic-radar-s4-{suffix}"))
        self.assertFalse(_matches_run_identity(context["run_id"], "UnrelatedStack", f"agentic-radar-s4-{suffix}"))

    def test_s4_selects_lambda_self_managed_storage_recipe(self):
        s2 = _deployable_s2()
        candidate = s2["candidates"][0]
        candidate["title"] = "AWS Lambda self-managed code storage"
        candidate["source_url"] = "https://aws.amazon.com/about-aws/whats-new/2026/07/lambda-self-managed-code-storage/"
        evaluate = build_evaluate(s2, _shortlist()).to_dict()
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            paths = {"s1": root / "s1.json", "s2": root / "s2.json", "s3": root / "s3.json"}
            s1 = {"stage": "S1", "run_id": "unit-test-run", "candidates": [{"candidate_id": "CAND-1"}]}
            for key, payload in (("s1", s1), ("s2", s2), ("s3", evaluate)):
                paths[key].write_text(json.dumps(payload), encoding="utf-8")
            approval = {
                "approved_by": "Cleo", "selected_candidate_id": "CAND-1", "deployment_authorized": True,
                "lineage": {f"{key}_artifact_path": str(path) for key, path in paths.items()},
            }
            context = build_deployment_context(evaluate, approval)

        self.assertEqual(context["status"], "ready_for_manual_deployment")
        self.assertEqual(context["deployment"]["recipe"], "lambda_self_managed_s3_code_storage_cdk")

    @patch("agentic_cloud_radar.s4_deployer._aws_json")
    def test_existing_complete_stack_can_resume_verification(self, aws_json):
        aws_json.return_value = {"Stacks": [{"StackStatus": "CREATE_COMPLETE"}]}

        self.assertEqual(_stack_status_or_none("Example", "intern", "ap-southeast-1"), "CREATE_COMPLETE")

    @patch("agentic_cloud_radar.s4_deployer.time.sleep")
    @patch("agentic_cloud_radar.s4_deployer._aws")
    def test_s3_files_readback_retries_eventual_no_such_key(self, aws, sleep):
        aws.side_effect = [DeploymentError("NoSuchKey"), ""]

        _get_s3_object_with_retry(
            "example-bucket",
            "poc/from-mount.txt",
            Path("from-mount.txt"),
            "intern",
            "ap-southeast-1",
            attempts=2,
            interval_seconds=1,
        )

        self.assertEqual(aws.call_count, 2)
        sleep.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
