import unittest

from agentic_cloud_radar.s0 import build_demand_card


class S0DemandCardTests(unittest.TestCase):
    def test_url_input_waits_for_confirmation(self):
        result = build_demand_card(
            {
                "problem_statement": "Assess whether an AWS storage launch can simplify file workflows.",
                "desired_outcome": "Decide whether a small PoC should be proposed.",
                "success_criteria": ["Official source is parsed."],
                "source_mode": "url",
                "source_input": {"url": "https://aws.amazon.com/blogs/aws/example/"},
            }
        ).to_dict()

        self.assertEqual(result["status"], "ready_for_confirmation")
        self.assertEqual(result["constraints"]["max_small_poc_usd"], 3)
        self.assertEqual(result["constraints"]["preferred_region"], "ap-southeast-1")
        self.assertEqual(result["sensitivity_check"]["status"], "passed")

    def test_confirmed_input_can_enter_s1(self):
        result = build_demand_card(
            {
                "problem_statement": "Assess whether an AWS storage launch can simplify file workflows.",
                "desired_outcome": "Decide whether a small PoC should be proposed.",
                "success_criteria": ["Official source is parsed."],
                "source_mode": "url",
                "source_input": {"url": "https://aws.amazon.com/blogs/aws/example/"},
                "human_confirmed": True,
            }
        ).to_dict()

        self.assertEqual(result["status"], "confirmed")

    def test_missing_problem_needs_revision(self):
        result = build_demand_card(
            {
                "desired_outcome": "Decide whether a small PoC should be proposed.",
                "success_criteria": ["Official source is parsed."],
                "source_mode": "url",
                "source_input": {"url": "https://aws.amazon.com/blogs/aws/example/"},
            }
        ).to_dict()

        self.assertEqual(result["status"], "needs_revision")
        self.assertIn("missing_problem_statement", [issue["code"] for issue in result["validation_issues"]])

    def test_sensitive_input_is_blocked(self):
        result = build_demand_card(
            {
                "problem_statement": "Assess storage workflow 123456789012",
                "desired_outcome": "Decide whether a small PoC should be proposed.",
                "success_criteria": ["Official source is parsed."],
                "source_mode": "url",
                "source_input": {"url": "https://aws.amazon.com/blogs/aws/example/"},
                "human_confirmed": True,
            }
        ).to_dict()

        self.assertEqual(result["status"], "blocked_sensitive")
        self.assertEqual(result["sensitivity_check"]["status"], "blocked")

    def test_vague_input_gets_assistant_question(self):
        result = build_demand_card(
            {
                "problem_statement": "better",
                "desired_outcome": "faster",
                "success_criteria": ["Need a useful answer."],
                "source_mode": "service",
                "source_input": {"service": "S3"},
            }
        ).to_dict()

        self.assertEqual(result["status"], "needs_revision")
        self.assertTrue(result["assistant_findings"])


if __name__ == "__main__":
    unittest.main()
