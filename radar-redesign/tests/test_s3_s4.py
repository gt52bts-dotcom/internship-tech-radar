import unittest

from agentic_cloud_radar.s3 import build_evaluate
from agentic_cloud_radar.s4 import build_validate


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


class S3S4Tests(unittest.TestCase):
    def test_s3_stops_without_human_shortlist(self):
        result = build_evaluate(_sample_s2()).to_dict()

        self.assertEqual(result["status"], "needs_human_shortlist")
        self.assertEqual(result["evaluated_candidates"], [])

    def test_s3_evaluates_shortlisted_candidate_without_region_blocking_s3(self):
        request = {
            "selected_candidate_ids": ["CAND-1"],
            "problem_to_solve": "Reduce manual evidence gathering in a non-production radar workflow.",
            "available_environment": "Local/document validation only.",
            "forbidden_data_and_permissions": "No production data, no PII, no write permissions.",
            "selected_by": "Cleo",
        }

        result = build_evaluate(_sample_s2(), request).to_dict()

        self.assertEqual(result["status"], "evaluated")
        evaluated = result["evaluated_candidates"][0]
        self.assertTrue(evaluated["recommend_s4"])
        self.assertEqual(evaluated["region_status"]["status"], "region_unknown")
        self.assertFalse(evaluated["region_status"]["blocks_s3"])
        self.assertTrue(evaluated["region_status"]["blocks_paid_poc"])
        self.assertEqual(evaluated["s4_validation_path"], "low_risk_validation_only")

    def test_s4_downgrades_region_unknown_candidate_to_low_risk_validation(self):
        request = {
            "selected_candidate_ids": ["CAND-1"],
            "problem_to_solve": "Reduce manual evidence gathering in a non-production radar workflow.",
            "available_environment": "Local/document validation only.",
            "forbidden_data_and_permissions": "No production data, no PII, no write permissions.",
            "selected_by": "Cleo",
        }
        s3 = build_evaluate(_sample_s2(), request).to_dict()

        result = build_validate(s3).to_dict()

        self.assertEqual(result["status"], "validated_low_risk")
        validated = result["validated_candidates"][0]
        self.assertEqual(validated["validation_status"], "validated_low_risk")
        self.assertEqual(validated["cleanup_status"], "not_applicable_no_cloud_resources_created")
        self.assertFalse(validated["automatic_poc_start"])
        self.assertIn("region_status_available", validated["downgrade_reasons"])


if __name__ == "__main__":
    unittest.main()
