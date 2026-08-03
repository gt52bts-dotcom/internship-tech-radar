import unittest

from agentic_cloud_radar.s5 import build_report


class Skill5Tests(unittest.TestCase):
    def test_runtime_evidence_is_rendered_without_fabricating_cost_or_closure(self):
        s1 = {"stage": "S1", "run_id": "run-1", "candidates": [{"candidate_id": "C1"}]}
        s2 = {"stage": "S2", "run_id": "run-1", "candidates": [{"candidate_id": "C1", "title": "Lambda feature", "source_url": "https://aws.amazon.com/example"}]}
        s3 = {
            "stage": "S3", "run_id": "run-1", "evaluated_candidates": [{
                "candidate_id": "C1", "title": "Lambda feature", "source_url": "https://aws.amazon.com/example",
                "weighted_score": 4.0, "recommend_s4": True,
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
        self.assertIn("本流程不進行預估與實際帳務成本比對", " ".join(report["unknown_or_not_verified"]))
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
                "recommend_poc": True,
            }],
        }

        report = build_report(s1, s2, s3)

        rows = dict(report["evaluation"]["rows"])
        self.assertEqual(rows["建議進入實際 Skill 4 PoC"], "是")
        self.assertNotIn("達到 PoC 審查門檻", rows)
        self.assertEqual(report["conclusion"]["status"], "poc_recommended_awaiting_approval")
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
            "console_review": {"status": "confirmed", "display_channel_confirmed": "conversation", "evidence": {"screenshots": [{"view": "infrastructure_composer"}]}},
            "cleanup": {"status": "verified"},
        }

        report = build_report(s1, s2, s3, s4, runtime)

        self.assertEqual(report["status"], "final")
        self.assertIn("Infrastructure Composer 截圖人工確認", report["conclusion"]["text"])
        self.assertEqual(report["gui_model"]["console_review"]["screenshot_status"], "已截圖並經人類確認（1 張）")

    def test_final_report_accepts_resource_inventory_review(self):
        s1 = {"stage": "S1", "run_id": "run-inventory", "candidates": [{"candidate_id": "C5"}]}
        s2 = {"stage": "S2", "run_id": "run-inventory", "candidates": [{"candidate_id": "C5", "title": "Feature", "source_url": "https://aws.amazon.com/example"}]}
        s3 = {"stage": "S3", "run_id": "run-inventory", "evaluated_candidates": [{"candidate_id": "C5", "title": "Feature", "source_url": "https://aws.amazon.com/example", "recommend_poc": True}]}
        s4 = {"stage": "S4", "run_id": "run-inventory", "validated_candidates": [{"candidate_id": "C5", "validation_status": "poc_ready_for_manual_start"}]}
        runtime = {
            "schema_version": "s4.runtime-evidence.v3",
            "stage": "S4",
            "run_id": "run-inventory",
            "status": "cleanup_verified",
            "console_review": {
                "status": "confirmed",
                "display_channel_confirmed": "conversation",
                "evidence": {
                    "schema_version": "s4.resource-inventory-review.v1",
                    "inventory_sha256": "a" * 64,
                    "screenshots": [{"view": "resource_inventory"}],
                },
            },
            "cleanup": {"status": "verified"},
        }

        report = build_report(s1, s2, s3, s4, runtime)

        self.assertEqual(report["status"], "final")
        self.assertIn("資源盤點人工確認", report["conclusion"]["text"])
        self.assertNotIn("Infrastructure Composer 截圖人工確認", report["conclusion"]["text"])
        self.assertEqual(report["gui_model"]["console_review"]["review_evidence_status"], "已用資源盤點經人類確認（1 份）")

    def test_final_report_renders_pre_cleanup_usage_snapshot(self):
        s1 = {"stage": "S1", "run_id": "run-usage", "candidates": [{"candidate_id": "C8"}]}
        s2 = {"stage": "S2", "run_id": "run-usage", "candidates": [{"candidate_id": "C8", "title": "Feature", "source_url": "https://aws.amazon.com/example"}]}
        s3 = {"stage": "S3", "run_id": "run-usage", "evaluated_candidates": [{"candidate_id": "C8", "title": "Feature", "source_url": "https://aws.amazon.com/example", "recommend_poc": True}]}
        s4 = {"stage": "S4", "run_id": "run-usage", "validated_candidates": [{"candidate_id": "C8", "validation_status": "poc_ready_for_manual_start"}]}
        runtime = {
            "schema_version": "s4.runtime-evidence.v3",
            "stage": "S4",
            "run_id": "run-usage",
            "status": "cleanup_verified",
            "console_review": {"status": "confirmed", "display_channel_confirmed": "conversation", "evidence": {"screenshots": [{"view": "infrastructure_composer"}]}},
            "cleanup": {"status": "verified", "pre_cleanup_usage_snapshot_status": "captured"},
            "pre_cleanup_usage_snapshot": {
                "schema_version": "s4.pre-cleanup-usage-snapshot.v1",
                "status": "captured",
                "captured_at": "2026-07-31T10:20:00+00:00",
                "billing_evidence": False,
                "actual_cost_status": "not_billing_evidence",
                "timeline": {"deployed_at": "2026-07-31T10:00:00+00:00", "elapsed_seconds": 1200},
                "sections": {
                    "cloudformation": {"stack_status": "CREATE_COMPLETE", "resource_count": 4},
                    "s3": {"object_count_current": 1, "object_version_count": 2, "delete_marker_count": 0, "total_size_bytes": 4096},
                    "lambda": {
                        "runtime": "python3.12",
                        "code_size_bytes": 2048,
                        "cloudwatch_metrics": {"Invocations": {"sum": 1}, "Errors": {"sum": 0}},
                    },
                },
            },
        }

        report = build_report(s1, s2, s3, s4, runtime)

        self.assertEqual(report["pre_cleanup_usage_snapshot"]["status"], "captured")
        self.assertEqual(report["gui_model"]["pre_cleanup_usage_snapshot"]["status_label"], "已擷取")
        self.assertIn("cleanup 前即時用量快照", report["markdown"])
        self.assertIn("不是 AWS 帳單", report["markdown"])

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

    def test_abort_cleanup_is_never_a_console_reviewed_final(self):
        s1 = {"stage": "S1", "run_id": "run-abort", "candidates": [{"candidate_id": "C7"}]}
        s2 = {"stage": "S2", "run_id": "run-abort", "candidates": [{"candidate_id": "C7", "title": "Feature", "source_url": "https://aws.amazon.com/example"}]}
        s3 = {"stage": "S3", "run_id": "run-abort", "evaluated_candidates": [{"candidate_id": "C7", "title": "Feature", "source_url": "https://aws.amazon.com/example"}]}
        s4 = {"stage": "S4", "run_id": "run-abort", "validated_candidates": [{"candidate_id": "C7", "validation_status": "poc_ready_for_manual_start"}]}
        runtime = {
            "schema_version": "s4.runtime-evidence.v3",
            "stage": "S4",
            "run_id": "run-abort",
            "status": "cleanup_verified",
            "console_review": {"status": "skipped_for_cost_control"},
            "cleanup": {"status": "verified", "cleanup_mode": "abort_without_console_review"},
        }

        report = build_report(s1, s2, s3, s4, runtime)

        self.assertEqual(report["status"], "final_without_console_review")
        self.assertEqual(report["report_type"], "closed_without_console_review")
        self.assertEqual(report["conclusion"]["status"], "cleaned_without_console_review")

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
        self.assertIn("本流程不進行預估與實際帳務成本比對", report["markdown"])
        self.assertIn("## 新聞摘要：應用面優勢", report["markdown"])
        self.assertIn("## Future work", report["markdown"])
        self.assertIn("## Reviewer questions", report["markdown"])
        self.assertIn("## S1-S5 階段證據", report["markdown"])
        self.assertIn("Skill 3 加權分（滿分 5）", report["markdown"])
        self.assertIn("4.4 / 5", report["markdown"])
        self.assertIn("主要成本驅動", report["markdown"])
        self.assertIn("人工需確認的 PoC 資源", report["markdown"])
        self.assertNotIn("| pending |", report["markdown"])
        self.assertNotIn("## 一句結論", report["markdown"])
        self.assertNotIn("信心", report["markdown"])
        self.assertNotIn("### 報價假設與限制", report["markdown"])
        self.assertNotIn("## 後續提醒", report["markdown"])
        self.assertIn("預期總額", report["markdown"])
        self.assertEqual(report["cost_quote"]["expected_total_usd"], 0.04719)
        self.assertEqual(report["gui_model"]["cost_quote"]["recommended_approval_ceiling_usd"], 0.2)
        self.assertEqual(report["gui_model"]["cost_quote"]["status_label"], "已完成估算")
        self.assertGreaterEqual(len(report["gui_model"]["stage_evidence"]), 6)
