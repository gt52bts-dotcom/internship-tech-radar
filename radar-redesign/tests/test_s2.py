import unittest

from agentic_cloud_radar.s1 import build_direct_url_scan
from agentic_cloud_radar.s2 import _target_region_matches, build_compare


REAL_AWS_S3_FILES_URL = "https://aws.amazon.com/blogs/aws/launching-s3-files-making-s3-buckets-accessible-as-file-systems/"


class S2CompareTests(unittest.TestCase):
    def test_singapore_text_for_another_feature_cannot_pass_the_region_gate(self):
        candidate = {"title": "Now Open AWS Local Zones in Athens Greece"}
        source_text = (
            "Athens Local Zone is now open.\n"
            "Parent Region: ap-southeast-1 (Asia Pacific, Singapore).\n"
            "This table describes a different Local Zone."
        )

        self.assertEqual(_target_region_matches(source_text, "ap-southeast-1", candidate), [])

    def test_all_commercial_regions_statement_can_prove_singapore_for_named_service(self):
        candidate = {"title": "AWS Lambda self-managed S3 code storage", "related_aws_services": ["Lambda", "S3"]}
        source_text = "Lambda self-managed S3 code storage is available in all commercial AWS Regions."

        self.assertEqual(
            _target_region_matches(source_text, "ap-southeast-1", candidate),
            [source_text],
        )

    def test_traditional_chinese_all_commercial_regions_statement_can_prove_singapore(self):
        candidate = {"title": "AWS Lambda 自主管理程式碼儲存空間", "related_aws_services": ["Lambda", "S3"]}
        source_text = "所有商業 AWS 區域皆提供自主管理的 Amazon S3 程式碼儲存功能。"

        self.assertEqual(
            _target_region_matches(source_text, "ap-southeast-1", candidate),
            [source_text],
        )

    def test_compares_a_real_s1_candidate_with_source_linked_evidence(self):
        scan = build_direct_url_scan(REAL_AWS_S3_FILES_URL).to_dict()
        result = build_compare(scan).to_dict()

        self.assertEqual(result["status"], "ready_for_human_shortlist")
        self.assertFalse(result["comparison_contract"]["automatic_shortlist"])
        self.assertEqual(len(result["candidates"]), 1)
        self.assertEqual(result["shortlist_policy"]["eligible_candidate_count"], 1)
        self.assertIn(
            result["candidates"][0]["comparison_dimensions"]["target_region_eligibility"]["status"],
            {"available_ap_southeast_1", "region_unknown"},
        )
        self.assertFalse(
            result["candidates"][0]["comparison_dimensions"]["target_region_eligibility"]["blocks_s3"]
        )
        card = result["candidates"][0]["proposal_card"]
        self.assertEqual(card["proposal_status"], "public_evidence_candidate")
        self.assertIn("improvement_hypothesis", card)
        self.assertIn("tradeoffs_and_risks", card)
        self.assertIn("validation_design", card)
        self.assertEqual(result["candidates"][0]["linked_evidence"]["primary_source"]["status"], "refetched")
        self.assertEqual(
            result["shortlist_policy"]["target_region"],
            "ap-southeast-1",
        )
        lookup = result["candidates"][0]["linked_evidence"]["official_region_lookup"]
        self.assertEqual(lookup["method"], "aws_official_search_then_fetch")
        self.assertNotIn("ap-southeast-1", lookup["query"])
        self.assertEqual(lookup["target_region"], "ap-southeast-1")
        self.assertIn(
            lookup["status"],
            {"search_completed", "search_completed_no_new_official_pages"},
        )
        region = result["candidates"][0]["comparison_dimensions"]["target_region_eligibility"]
        if region["status"] == "available_ap_southeast_1":
            self.assertNotIn(
                "No candidate-relevant official AWS Region or availability page was fetched in this S2 run.",
                result["candidates"][0]["evidence_limits"],
            )


if __name__ == "__main__":
    unittest.main()
