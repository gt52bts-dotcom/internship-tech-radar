import unittest

from agentic_cloud_radar.s5 import build_report


class Skill5Tests(unittest.TestCase):
    def test_runtime_evidence_is_rendered_without_fabricating_cost_or_closure(self):
        s1 = {"stage": "S1", "run_id": "run-1", "candidates": [{"candidate_id": "C1"}]}
        s2 = {"stage": "S2", "run_id": "run-1", "candidates": [{"candidate_id": "C1", "title": "Lambda feature", "source_url": "https://aws.amazon.com/example"}]}
        s3 = {
            "stage": "S3", "run_id": "run-1", "evaluated_candidates": [{
                "candidate_id": "C1", "title": "Lambda feature", "source_url": "https://aws.amazon.com/example",
                "weighted_score": 4.0, "confidence": "medium", "recommend_s4": True,
                "dimension_scores": {"technical_value": 4},
                "region_status": {"status": "available_ap_southeast_1"},
                "cost_estimate": {"status": "unknown"}, "stop_conditions": ["Keep the PoC non-production."],
                "evidence_refs": {"evidence_limits": []},
            }],
        }
        s4 = {"stage": "S4", "run_id": "run-1", "validated_candidates": [{"candidate_id": "C1", "validation_status": "paid_poc_ready_for_manual_start"}]}
        runtime = {
            "stage": "S4", "run_id": "run-1", "status": "awaiting_console_review",
            "deployment": {"stack_status": "CREATE_COMPLETE"},
            "verification": {"cloudformation_reference_mode": "verified", "lambda_invoke": "verified"},
            "console_review": {"status": "required"}, "cleanup": {"status": "pending_console_review"},
        }

        report = build_report(s1, s2, s3, s4, runtime)

        self.assertEqual(report["status"], "interim")
        self.assertIn("REFERENCE 設定", report["conclusion"]["text"])
        self.assertIn("官方定價或實際成本", " ".join(report["unknown_or_not_verified"]))
        self.assertIn("CloudFormation", report["markdown"])
        self.assertEqual(report["gui_model"]["score"]["weighted_score"], 4.0)

    def test_dual_s4_decisions_are_rendered_separately(self):
        s1 = {"stage": "S1", "run_id": "run-2", "candidates": [{"candidate_id": "C2"}]}
        s2 = {"stage": "S2", "run_id": "run-2", "candidates": [{"candidate_id": "C2", "title": "Feature", "source_url": "https://aws.amazon.com/example"}]}
        s3 = {
            "stage": "S3",
            "run_id": "run-2",
            "evaluated_candidates": [{
                "candidate_id": "C2",
                "title": "Feature",
                "source_url": "https://aws.amazon.com/example",
                "weighted_score": 3.35,
                "confidence": "medium",
                "recommend_low_risk_validation": True,
                "eligible_for_paid_poc_review": False,
                "recommend_s4": True,
            }],
        }

        report = build_report(s1, s2, s3)

        rows = dict(report["evaluation"]["rows"])
        self.assertEqual(rows["建議低風險 Skill 4 驗證"], "是")
        self.assertEqual(rows["具備付費 PoC 審查資格"], "否")
        self.assertEqual(report["conclusion"]["status"], "low_risk_validation_recommended")

    def test_mismatched_artifacts_are_reported_as_incomplete(self):
        report = build_report({"stage": "S1", "run_id": "run-a"}, {"stage": "S2", "run_id": "run-b"})
        self.assertEqual(report["status"], "incomplete_artifacts")
        self.assertIn("artifact_run_id_mismatch", report["input_issues"])


if __name__ == "__main__":
    unittest.main()
