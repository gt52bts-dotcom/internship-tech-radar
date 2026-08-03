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


class S1ExplanationTests(unittest.TestCase):
    """The explanation layer must stay auditable and never invent a fact."""

    TITLE = "AWS Lambda announces self-managed code storage - AWS"
    TEXT = (
        "AWS Lambda announces self-managed code storage. "
        "Lambda now supports self-managed Amazon S3 buckets for code storage, "
        "so you can reference source code directly without an intermediate copy. "
        "Previously, Lambda always copied your deployment package into "
        "Lambda-managed storage, which counted against this quota. "
        "This eliminates the code storage limit and shortens start time."
    )

    def _build(self, **kwargs):
        from agentic_cloud_radar.s1_explanation import build_explanation

        params = {
            "title": self.TITLE,
            "description": "",
            "article_text": self.TEXT,
            "related_services": ["Lambda", "S3"],
            "demand_card": {},
        }
        params.update(kwargs)
        return build_explanation(**params)

    def test_every_key_point_span_resolves_to_its_own_text(self):
        explanation = self._build()
        evidence = explanation["evidence_text"]

        self.assertTrue(explanation["key_points"])
        for point in explanation["key_points"]:
            start, end = point["evidence_span"]
            self.assertEqual(evidence[start:end].strip(), point["point"].strip())
            self.assertEqual(point["derivation"], "source_verbatim")

    def test_significance_is_a_before_after_contrast_backed_by_key_points(self):
        explanation = self._build()
        significance = explanation["significance"]

        self.assertEqual(significance["status"], "derived")
        self.assertEqual(significance["derivation"], "derived_summary")
        self.assertIn("Previously", significance["before"])
        self.assertNotEqual(significance["before"], significance["after"])
        self.assertEqual(
            significance["supported_by"],
            [point["id"] for point in explanation["key_points"]],
        )

    def test_architecture_marks_components_the_source_never_stated(self):
        explanation = self._build()
        architecture = explanation["implementation_architecture"]

        self.assertEqual(architecture["status"], "drafted")
        self.assertEqual(architecture["derivation"], "inferred_architecture")
        stated = {item["service"] for item in architecture["core_components"] if item["stated_in_source"]}
        unstated = {item["service"] for item in architecture["core_components"] if not item["stated_in_source"]}
        self.assertEqual(stated, {"Lambda", "S3"})
        self.assertIn("IAM", unstated)
        self.assertIn("CloudWatch", unstated)
        self.assertEqual(sorted(architecture["unstated_prerequisites"]), ["CloudWatch", "IAM"])

    def test_source_derived_application_contexts_stay_hypotheses(self):
        explanation = self._build(demand_card={"business_domain": "保單批次處理"})
        contexts = explanation["possible_application_contexts"]

        stated = [item for item in contexts if item["derivation"] == "source_verbatim"]
        derived = [item for item in contexts if item["derivation"] == "hypothesis"]
        self.assertEqual(stated[0]["context"], "保單批次處理")
        self.assertTrue(derived)
        for item in derived:
            self.assertIn("assumption", item)

    def test_missing_service_evidence_blocks_the_architecture_draft(self):
        explanation = self._build(related_services=[])

        self.assertEqual(explanation["implementation_architecture"]["status"], "needs_service_evidence")
        self.assertTrue(explanation["explanation_gaps"])

    def test_explanation_is_deterministic(self):
        self.assertEqual(self._build(), self._build())
