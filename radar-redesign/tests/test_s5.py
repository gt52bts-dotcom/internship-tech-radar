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
        s4 = {"stage": "S4", "run_id": "run-1", "validated_candidates": [{"candidate_id": "C1", "validation_status": "poc_ready_for_manual_start"}]}
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
        self.assertEqual(report["cost_reconciliation"]["actual"]["status"], "pending")
        self.assertIn("不得以 runtime 估算代替", " ".join(report["unknown_or_not_verified"]))
        self.assertIn("CloudFormation", report["markdown"])
        self.assertEqual(report["gui_model"]["score"]["weighted_score"], 4.0)

    def test_single_poc_decision_is_rendered(self):
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
                "recommend_poc": True,
            }],
        }

        report = build_report(s1, s2, s3)

        rows = dict(report["evaluation"]["rows"])
        self.assertEqual(rows["技術上具備 Skill 4 PoC 資格"], "是")
        self.assertNotIn("達到 PoC 審查門檻", rows)
        self.assertEqual(report["conclusion"]["status"], "technically_eligible_for_poc")
        self.assertIn("工作負載適配性未評估", " ".join(report["unknown_or_not_verified"]))

    def test_final_report_records_screenshot_backed_actual_poc_conclusion(self):
        s1 = {"stage": "S1", "run_id": "run-screenshot", "candidates": [{"candidate_id": "C5"}]}
        s2 = {"stage": "S2", "run_id": "run-screenshot", "candidates": [{"candidate_id": "C5", "title": "Feature", "source_url": "https://aws.amazon.com/example"}]}
        s3 = {"stage": "S3", "run_id": "run-screenshot", "evaluated_candidates": [{"candidate_id": "C5", "title": "Feature", "source_url": "https://aws.amazon.com/example", "recommend_poc": True}]}
        s4 = {"stage": "S4", "run_id": "run-screenshot", "validated_candidates": [{"candidate_id": "C5", "validation_status": "poc_ready_for_manual_start"}]}
        runtime = {
            "schema_version": "s4.runtime-evidence.v3",
            "stage": "S4",
            "run_id": "run-screenshot",
            "status": "cleanup_verified",
            "console_review": {"status": "confirmed", "evidence": {"screenshots": [{"view": "infrastructure_composer"}]}},
            "cleanup": {"status": "verified"},
        }

        report = build_report(s1, s2, s3, s4, runtime)

        self.assertEqual(report["status"], "final")
        self.assertIn("Infrastructure Composer 截圖人工確認", report["conclusion"]["text"])
        self.assertEqual(report["gui_model"]["console_review"]["screenshot_status"], "captured_and_confirmed (1)")

    def test_v3_cleanup_verified_without_screenshot_is_not_final(self):
        s1 = {"stage": "S1", "run_id": "run-cleaned", "candidates": [{"candidate_id": "C6"}]}
        s2 = {"stage": "S2", "run_id": "run-cleaned", "candidates": [{"candidate_id": "C6", "title": "Feature", "source_url": "https://aws.amazon.com/example"}]}
        s3 = {"stage": "S3", "run_id": "run-cleaned", "evaluated_candidates": [{"candidate_id": "C6", "title": "Feature", "source_url": "https://aws.amazon.com/example", "recommend_poc": True}]}
        s4 = {"stage": "S4", "run_id": "run-cleaned", "validated_candidates": [{"candidate_id": "C6", "validation_status": "poc_ready_for_manual_start"}]}
        runtime = {
            "schema_version": "s4.runtime-evidence.v3",
            "stage": "S4",
            "run_id": "run-cleaned",
            "status": "cleanup_verified",
            "console_review": {"status": "confirmed", "evidence_status": "captured_and_confirmed"},
            "cleanup": {"status": "verified"},
        }

        report = build_report(s1, s2, s3, s4, runtime)

        self.assertEqual(report["status"], "incomplete_artifacts")
        self.assertEqual(report["report_type"], "interim")
        self.assertEqual(report["conclusion"]["status"], "cleanup_verified_missing_console_screenshot")

    def test_mismatched_artifacts_are_reported_as_incomplete(self):
        report = build_report({"stage": "S1", "run_id": "run-a"}, {"stage": "S2", "run_id": "run-b"})
        self.assertEqual(report["status"], "incomplete_artifacts")
        self.assertIn("artifact_run_id_mismatch", report["input_issues"])

    def test_itemized_quote_is_rendered_in_markdown_and_gui(self):
        from agentic_cloud_radar.costing import build_cost_quote

        candidate = {
            "candidate_id": "C3",
            "title": "Launching S3 Files, making S3 buckets accessible as file systems",
            "source_url": "https://aws.amazon.com/blogs/aws/launching-s3-files-making-s3-buckets-accessible-as-file-systems/",
            "weighted_score": 4.4,
            "confidence": "medium",
            "recommend_poc": True,
            "region_status": {"status": "available_ap_southeast_1"},
            "evidence_refs": {"evidence_limits": []},
        }
        quote = build_cost_quote(candidate, "run-3", "ap-southeast-1")
        candidate["cost_estimate"] = {
            "status": quote["status"],
            "estimated_usd": quote["expected_total_usd"],
            "quote_id": quote["quote_id"],
            "quote": quote,
        }
        s1 = {"stage": "S1", "run_id": "run-3", "candidates": [{"candidate_id": "C3"}]}
        s2 = {"stage": "S2", "run_id": "run-3", "candidates": [candidate]}
        s3 = {"stage": "S3", "run_id": "run-3", "evaluated_candidates": [candidate]}

        report = build_report(s1, s2, s3)

        self.assertIn("## PoC 成本估算報價單", report["markdown"])
        self.assertIn("## 預估成本 vs 可歸因實際帳務成本", report["markdown"])
        self.assertIn("實際成本狀態：pending", report["markdown"])
        self.assertIn("預期總額", report["markdown"])
        self.assertEqual(report["cost_quote"]["expected_total_usd"], 0.04719)
        self.assertEqual(report["cost_reconciliation"]["actual"]["status"], "pending")
        self.assertEqual(report["gui_model"]["cost_quote"]["recommended_approval_ceiling_usd"], 0.2)
        self.assertEqual(report["gui_model"]["cost_reconciliation"]["status"], "pending_actual_cost")

    def test_attributable_billing_artifact_is_compared_to_estimate(self):
        from agentic_cloud_radar.costing import build_cost_quote

        candidate = {
            "candidate_id": "C4",
            "title": "Launching S3 Files, making S3 buckets accessible as file systems",
            "source_url": "https://aws.amazon.com/blogs/aws/launching-s3-files-making-s3-buckets-accessible-as-file-systems/",
            "weighted_score": 4.4,
            "confidence": "medium",
            "recommend_poc": True,
        }
        quote = build_cost_quote(candidate, "run-4", "ap-southeast-1")
        candidate["cost_estimate"] = {
            "status": quote["status"],
            "estimated_usd": quote["expected_total_usd"],
            "quote_id": quote["quote_id"],
            "quote": quote,
        }
        billing = {
            "run_id": "run-4",
            "source_type": "cost_explorer",
            "attributable": True,
            "amount_usd": 0.031,
            "currency": "USD",
            "source_artifact": "cost-explorer-run-4.json",
            "period_start": "2026-07-30",
            "period_end": "2026-07-31",
            "attribution_key": "agentic-radar-s4",
        }
        s1 = {"stage": "S1", "run_id": "run-4", "candidates": [{"candidate_id": "C4"}]}
        s2 = {"stage": "S2", "run_id": "run-4", "candidates": [candidate]}
        s3 = {"stage": "S3", "run_id": "run-4", "evaluated_candidates": [candidate]}

        report = build_report(s1, s2, s3, billing=billing)

        self.assertEqual(report["cost_reconciliation"]["status"], "compared")
        self.assertEqual(report["cost_reconciliation"]["actual"]["amount_usd"], 0.031)
        self.assertEqual(report["cost_reconciliation"]["delta_usd"], -0.01619)
        self.assertIn("可歸因實際帳務成本已由 cost_explorer 記錄", " ".join(report["verified_facts"]))


if __name__ == "__main__":
    unittest.main()
