import unittest
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from agentic_cloud_radar.s3 import build_evaluate
from agentic_cloud_radar.s4 import build_validate
from agentic_cloud_radar.s4_deployer import _matches_run_identity, build_deployment_context, record_console_review


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
        "problem_to_solve": "Validate a non-production storage workflow.",
        "available_environment": "Isolated intern account non-production environment.",
        "forbidden_data_and_permissions": "No production data, no PII, no production roles.",
        "selected_by": "Cleo",
    }


class S3S4Tests(unittest.TestCase):
    def test_s3_stops_without_human_shortlist(self):
        result = build_evaluate(_sample_s2()).to_dict()

        self.assertEqual(result["status"], "needs_human_shortlist")
        self.assertEqual(result["evaluated_candidates"], [])

    def test_s3_evaluates_shortlisted_candidate_without_region_blocking_s3(self):
        request = _shortlist()

        result = build_evaluate(_sample_s2(), request).to_dict()

        self.assertEqual(result["status"], "evaluated")
        evaluated = result["evaluated_candidates"][0]
        self.assertTrue(evaluated["recommend_s4"])
        self.assertEqual(evaluated["region_status"]["status"], "region_unknown")
        self.assertFalse(evaluated["region_status"]["blocks_s3"])
        self.assertTrue(evaluated["region_status"]["blocks_paid_poc"])
        self.assertEqual(evaluated["s4_validation_path"], "low_risk_validation_only")

    def test_s4_downgrades_region_unknown_candidate_to_low_risk_validation(self):
        request = _shortlist()
        s3 = build_evaluate(_sample_s2(), request).to_dict()

        result = build_validate(s3).to_dict()

        self.assertEqual(result["status"], "validated_low_risk")
        validated = result["validated_candidates"][0]
        self.assertEqual(validated["validation_status"], "validated_low_risk")
        self.assertEqual(validated["cleanup_status"], "not_applicable_no_cloud_resources_created")
        self.assertFalse(validated["automatic_poc_start"])
        self.assertIn("region_status_available", validated["downgrade_reasons"])

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
                "validation_type": "paid_poc",
                "approved_by": "Cleo",
                "estimated_usd": 1.0,
                "automatic_poc_start": False,
                "selected_candidate_id": "CAND-1",
                "deployment_authorized": True,
                "approval_basis": "Reviewed S3 result.",
                "deployment": {"profile": "intern", "target_region": "ap-southeast-1", "create_test_instance": True},
                "success_criteria": ["CloudFormation completes."],
                "cleanup_scope": ["Delete the stack and its test data."],
                "lineage": {**{f"{key}_artifact_path": str(path) for key, path in paths.items()}},
            }
            context = build_deployment_context(evaluate, approval)

        self.assertEqual(context["status"], "ready_for_manual_deployment")
        self.assertEqual(context["deployment"]["recipe"], "s3_files_cdk")
        self.assertEqual(len(context["lineage"]["source_artifacts"]), 3)

    def test_console_review_is_required_before_cleanup(self):
        runtime = {"stage": "S4", "status": "awaiting_console_review", "console_review": {}, "cleanup": {}}
        reviewed = record_console_review(runtime, "Cleo")

        self.assertEqual(reviewed["status"], "ready_for_cleanup")
        self.assertEqual(reviewed["console_review"]["status"], "confirmed")

    def test_s4_deployment_context_allows_explicitly_acknowledged_region_warning(self):
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
                "validation_type": "paid_poc", "approved_by": "Cleo", "estimated_usd": 1.0,
                "automatic_poc_start": False, "selected_candidate_id": "CAND-1",
                "deployment_authorized": True, "region_warning_acknowledged": True,
                "deployment": {"profile": "intern", "target_region": "ap-southeast-1"},
                "success_criteria": ["CloudFormation completes."], "cleanup_scope": ["Delete the stack."],
                "lineage": {f"{key}_artifact_path": str(path) for key, path in paths.items()},
            }
            context = build_deployment_context(evaluate, approval)

        self.assertEqual(context["status"], "ready_for_manual_deployment")
        self.assertTrue(context["authorization"]["region_warning_acknowledged"])

    def test_cleanup_identity_must_be_derived_from_the_run(self):
        context = {"run_id": "unit-test-run"}
        suffix = hashlib.sha256(context["run_id"].encode("utf-8")).hexdigest()[:8]

        self.assertTrue(_matches_run_identity(context["run_id"], f"AgenticRadarS4{suffix.upper()}", f"agentic-radar-s4-{suffix}"))
        self.assertFalse(_matches_run_identity(context["run_id"], "UnrelatedStack", f"agentic-radar-s4-{suffix}"))


if __name__ == "__main__":
    unittest.main()
