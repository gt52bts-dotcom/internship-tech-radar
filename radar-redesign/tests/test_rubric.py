"""評分準則：構面定義、逐級判定、否決門檻，以及不得為特定候選寫死。"""

from __future__ import annotations

import inspect
import unittest

from agentic_cloud_radar import rubric, s3
from agentic_cloud_radar.rubric import (
    RUBRIC_CRITERIA,
    VETO_THRESHOLDS,
    WEIGHTS,
    render_criteria_markdown,
    score_adoption_prerequisites,
    score_reversibility,
    score_risk_and_stop_conditions,
    score_technical_value,
    score_verifiability,
)


class CriteriaShapeTests(unittest.TestCase):
    def test_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(WEIGHTS.values()), 1.0, places=6)

    def test_every_dimension_declares_question_smi_inputs_and_levels(self):
        for name, spec in RUBRIC_CRITERIA.items():
            self.assertTrue(spec["question"], name)
            self.assertTrue(spec["smi"], name)
            self.assertTrue(spec["inputs"], name)
            self.assertTrue(spec["levels"], name)

    def test_every_input_declares_which_stage_produced_it(self):
        for name, spec in RUBRIC_CRITERIA.items():
            for item in spec["inputs"]:
                self.assertIn(item["stage"], {"S1", "S2", "S3"}, f"{name}:{item['field']}")

    def test_every_level_states_condition_evidence_and_rationale(self):
        for name, spec in RUBRIC_CRITERIA.items():
            for level in spec["levels"]:
                self.assertTrue(level["condition"], name)
                self.assertTrue(level["evidence"], name)
                self.assertTrue(level["why"], name)

    def test_levels_descend_and_stay_within_range(self):
        for name, spec in RUBRIC_CRITERIA.items():
            scores = [level["score"] for level in spec["levels"]]
            self.assertEqual(scores, sorted(scores, reverse=True), name)
            self.assertTrue(all(0 <= s <= 5 for s in scores), name)

    def test_veto_thresholds_reference_real_dimensions(self):
        self.assertTrue(set(VETO_THRESHOLDS).issubset(set(WEIGHTS)))


class NoCandidateSpecificScoringTests(unittest.TestCase):
    """分數必須由通用訊號決定，否則個案結果不能作為方法有效的證據。"""

    FORBIDDEN = ("workspaces", "lambda-self-managed", "s3 files", "bedrock")

    def test_rubric_module_names_no_specific_candidate(self):
        source = inspect.getsource(rubric).lower()

        for token in self.FORBIDDEN:
            self.assertNotIn(token, source, f"評分準則不得針對 {token} 寫死")

    def test_scoring_path_in_s3_names_no_specific_candidate(self):
        for fn in (s3._score_candidate, s3._information_provenance):
            self.assertNotIn("workspaces", inspect.getsource(fn).lower())


class TechnicalValueTests(unittest.TestCase):
    def test_quantified_improvement_with_before_state_scores_five(self):
        explanation = {"significance": {"status": "derived", "before": "以前要手動複製",
                                        "difference": "縮短 40% 啟動時間"}}

        score, _ = score_technical_value(explanation, {}, {})

        self.assertEqual(score, 5)

    def test_qualitative_improvement_with_mechanism_scores_four(self):
        explanation = {"significance": {"status": "derived", "before": "以前要手動複製",
                                        "difference": "移除複製步驟"}}

        score, _ = score_technical_value(explanation, {}, {})

        self.assertEqual(score, 4)

    def test_quota_or_region_expansion_scores_two(self):
        proposal = {"improvement_hypothesis": {"potential_vectors": ["提高配額上限"]}}

        score, reason = score_technical_value({}, proposal, {})

        self.assertEqual(score, 2)
        self.assertIn("擴充", reason)

    def test_no_claim_at_all_scores_zero(self):
        score, _ = score_technical_value({}, {}, {})

        self.assertEqual(score, 0)


class VerifiabilityTests(unittest.TestCase):
    FULL_DESIGN = {"validation_design": {"minimum_success_evidence": ["x"],
                                         "before_measurements": ["a"], "after_measurements": ["b"]}}

    def test_recipe_covering_the_claim_with_full_design_scores_five(self):
        decision = {"deployable_recipe_registered": True,
                    "recipe": {"success_criteria": ["確認函數以參照模式建立"]}}
        explanation = {"significance": {"after": "以參照模式建立", "difference": "參照"}}

        score, _ = score_verifiability(self.FULL_DESIGN, decision, explanation)

        self.assertEqual(score, 5)

    def test_registered_recipe_not_covering_the_claim_scores_three(self):
        decision = {"deployable_recipe_registered": True, "recipe": {"success_criteria": ["堆疊建立完成"]}}
        explanation = {"significance": {"after": "代理操作桌面應用程式", "difference": "代理操作"}}

        score, reason = score_verifiability(self.FULL_DESIGN, decision, explanation)

        self.assertEqual(score, 3)
        self.assertIn("未涵蓋核心主張", reason)

    def test_no_design_and_no_recipe_scores_one_and_is_vetoed(self):
        score, _ = score_verifiability({}, {}, {})

        self.assertEqual(score, 1)
        self.assertLessEqual(score, VETO_THRESHOLDS["verifiability"])


class AdoptionPrerequisiteTests(unittest.TestCase):
    def test_no_prerequisites_scores_five(self):
        score, _ = score_adoption_prerequisites({"status": "feature_confirmed"}, {}, {})

        self.assertEqual(score, 5)

    def test_each_prerequisite_lowers_the_score_and_is_named(self):
        decision = {"recipe": {"required_region_capabilities": ["a", "b"],
                               "required_aws_services": ["a", "b", "c", "d"]}}
        quote = {"exclusions": ["Windows 授權模式需確認"]}

        score, reason = score_adoption_prerequisites({"status": "feature_confirmed"}, decision, quote)

        self.assertEqual(score, 2)
        self.assertIn("兩項以上區域能力", reason)
        self.assertIn("授權", reason)


class ControllabilityTests(unittest.TestCase):
    def test_missing_stop_conditions_scores_one(self):
        score, _ = score_risk_and_stop_conditions([], [], {})

        self.assertEqual(score, 1)

    def test_unrefundable_cost_is_a_stop_condition_failure(self):
        quote = {"cost_containment_model": {"cleanup_cannot_refund": ["月費"]}}

        score, _ = score_risk_and_stop_conditions(["逾時即停"], [], quote)

        self.assertEqual(score, 2)
        self.assertLessEqual(score, VETO_THRESHOLDS["risk_and_stop_conditions"])

    def test_defined_stop_conditions_score_four(self):
        score, _ = score_risk_and_stop_conditions(["逾時即停"], [], {})

        self.assertEqual(score, 4)


class ReversibilityTests(unittest.TestCase):
    RECIPE = {"recipe": {"cleanup_strategy": "delete stack", "cleanup_verification": ["回查"]}}

    def _quote(self, unit: str, formula: str) -> dict:
        return {"scenarios": {"expected": {"line_items": [{"quantity_unit": unit, "formula": formula}]}}}

    def test_monthly_billing_scores_one(self):
        score, _ = score_reversibility(self._quote("unique users", "x USD/user-month"), {})

        self.assertEqual(score, 1)

    def test_hourly_billing_with_declared_teardown_scores_five(self):
        score, _ = score_reversibility(self._quote("hours", "x USD/instance-hour"), self.RECIPE)

        self.assertEqual(score, 5)

    def test_hourly_billing_without_teardown_scores_three(self):
        score, _ = score_reversibility(self._quote("hours", "x USD/instance-hour"), {})

        self.assertEqual(score, 3)


class GeneratedDocumentTests(unittest.TestCase):
    def test_the_table_is_generated_from_the_same_definition_the_scorers_use(self):
        markdown = render_criteria_markdown()

        for spec in RUBRIC_CRITERIA.values():
            self.assertIn(spec["label"], markdown)
            self.assertIn(spec["question"], markdown)
            for level in spec["levels"]:
                self.assertIn(level["condition"], markdown)

    def test_the_table_states_each_input_stage(self):
        markdown = render_criteria_markdown()

        self.assertIn("由誰產生", markdown)
        self.assertIn("| S1 |", markdown)
        self.assertIn("| S3 |", markdown)
