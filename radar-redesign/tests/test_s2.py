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

    def test_compares_a_real_s1_candidate_with_source_linked_evidence(self):
        scan = build_direct_url_scan(REAL_AWS_S3_FILES_URL).to_dict()
        result = build_compare(scan).to_dict()

        self.assertIn(
            result["status"],
            {"ready_for_human_shortlist", "no_target_region_eligible_candidates"},
        )
        self.assertFalse(result["comparison_contract"]["automatic_shortlist"])
        self.assertEqual(len(result["candidates"]), 1)
        card = result["candidates"][0]["proposal_card"]
        self.assertEqual(card["proposal_status"], "candidate_hypothesis_requires_human_problem_selection")
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


if __name__ == "__main__":
    unittest.main()
