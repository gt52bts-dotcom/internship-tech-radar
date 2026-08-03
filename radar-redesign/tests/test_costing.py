import unittest
from datetime import datetime, timezone

from agentic_cloud_radar.costing import build_cost_quote


class CostQuoteTests(unittest.TestCase):
    def test_s3_files_quote_is_itemized_and_reproducible(self):
        quote = build_cost_quote(
            {
                "candidate_id": "CAND-1",
                "title": "Launching S3 Files, making S3 buckets accessible as file systems",
            },
            "unit-test-run",
            "ap-southeast-1",
            datetime(2026, 7, 30, 8, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(quote["status"], "estimated")
        self.assertEqual(quote["expected_total_usd"], 0.04719)
        self.assertEqual(
            quote["estimated_range_usd"],
            {"low": 0.018037, "expected": 0.04719, "high": 0.150963},
        )
        self.assertEqual(quote["recommended_approval_ceiling_usd"], 0.2)
        self.assertEqual(quote["valid_until"], "2026-08-06")
        self.assertEqual(len(quote["scenarios"]["expected"]["line_items"]), 10)
        self.assertTrue(all(item["url"].startswith("https://") for item in quote["sources"]))

    def test_service_hints_use_generic_usage_model(self):
        quote = build_cost_quote(
            {
                "candidate_id": "GENERIC-1",
                "title": "Build a customer data lake automation with Lambda and Glue",
                "comparison_dimensions": {
                    "technology_scope": {"services_detected": ["Lambda", "Glue", "CloudFormation"]}
                },
            },
            "unit-test-run",
            "ap-southeast-1",
            datetime(2026, 7, 31, 8, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(quote["status"], "estimated")
        self.assertEqual(quote["pricing_level"], "Level B generic usage model")
        self.assertEqual(quote["recipe"], "generic_usage_model")
        self.assertFalse(quote["deployable_recipe_registered"])
        self.assertGreater(quote["expected_total_usd"], 0)
        self.assertGreaterEqual(quote["recommended_approval_ceiling_usd"], 0.05)
        self.assertIn("lambda", quote["detected_services"])
        self.assertIn("glue", quote["detected_services"])

    def test_unknown_scope_returns_incomplete_quote_artifact(self):
        quote = build_cost_quote(
            {"candidate_id": "OTHER-1", "title": "Unknown cloud feature"},
            "unit-test-run",
            "ap-southeast-1",
        )

        self.assertEqual(quote["status"], "incomplete")
        self.assertEqual(quote["pricing_level"], "Level C incomplete")
        self.assertIsNone(quote["expected_total_usd"])
        self.assertTrue(quote["quote_id"].startswith("POC-QUOTE-"))


if __name__ == "__main__":
    unittest.main()
