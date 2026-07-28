import unittest

from agentic_cloud_radar.s1 import _has_explicit_ga_wording, _maturity_evidence, build_direct_url_scan, build_scan


REAL_AWS_S3_FILES_URL = "https://aws.amazon.com/blogs/aws/launching-s3-files-making-s3-buckets-accessible-as-file-systems/"


class S1ScanTests(unittest.TestCase):
    def test_invalid_scan_parameters_stop_before_any_external_request(self):
        result = build_scan({"discovery_scope": "not-a-scope"}).to_dict()

        self.assertEqual(result["status"], "needs_revision")
        self.assertFalse(result["external_fetch_performed"])

    def test_direct_url_entry_fetches_the_real_official_page_without_s0(self):
        result = build_direct_url_scan(REAL_AWS_S3_FILES_URL).to_dict()

        self.assertIn(result["status"], {"scanned", "scanned_with_gaps"})
        self.assertEqual(result["entry_point"]["type"], "direct_url_import")
        self.assertIsNone(result["demand_card_ref"])
        candidate = result["candidates"][0]
        self.assertTrue(candidate["official_source"])
        self.assertTrue(candidate["external_fetch_performed"])
        self.assertFalse(candidate["rss_discovered"])
        self.assertFalse(candidate["seed_article"])
        self.assertIn("aws.amazon.com", candidate["source_url"])

    def test_rss_entry_discovers_current_public_sources(self):
        card = {
            "problem_statement": "Find current AWS technology changes relevant to cloud operations and infrastructure workflows.",
            "desired_outcome": "Produce current official AWS candidates for later comparison.",
            "discovery_scope": "focused",
        }

        result = build_scan(card).to_dict()

        self.assertIn(result["status"], {"scanned", "scanned_with_gaps"})
        self.assertTrue(result["external_fetch_performed"])
        self.assertTrue(result["source_catalog"]["github_repository_queries"])
        self.assertIn(
            "aws_cloud_operations",
            [feed["feed_key"] for feed in result["source_catalog"]["aws_rss_feeds"]],
        )

    def test_ga_evidence_requires_explicit_source_wording(self):
        found = _maturity_evidence(
            "A release announcement",
            "This capability is now generally available in supported Regions.",
        )
        absent = _maturity_evidence(
            "A configuration guide",
            "This guide explains how to configure the capability.",
        )
        preview = _maturity_evidence(
            "Amazon RDS Database Preview Environment",
            "Test the capability before it becomes generally available.",
        )
        roundup = _maturity_evidence(
            "The most visited Front-end Web and Mobile blog posts in 2024",
            "This older post announces the general availability of a capability.",
        )

        self.assertEqual(found["status"], "official_ga_evidence_found")
        self.assertEqual(absent["status"], "not_verified_by_this_source")
        self.assertEqual(preview["status"], "preview_or_future_ga_not_eligible")
        self.assertEqual(roundup["status"], "not_a_single_technology_announcement")
        self.assertTrue(_has_explicit_ga_wording("Amazon S3 Tables are now generally available."))
        self.assertFalse(_has_explicit_ga_wording("Amazon S3 Tables are available in a new tutorial."))


if __name__ == "__main__":
    unittest.main()
