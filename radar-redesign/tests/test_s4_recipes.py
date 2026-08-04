"""Skill 4 recipe framework: contract, registry, selection, and the deploy gate."""

from __future__ import annotations

import unittest

from agentic_cloud_radar.s3 import build_evaluate, render_poc_decision_report
from agentic_cloud_radar.s4_deployer import (
    build_approval_template,
    build_deployment_context,
    run_deployment_preflight,
)
from agentic_cloud_radar.s4_recipes import (
    LAMBDA_SELF_MANAGED_STORAGE,
    S3_FILES,
    WORKSPACES_AI_AGENT_ACCESS_DRAFT,
    deployable_recipe_ids,
    get_recipe,
    select_recipe,
)

FULL_APPROVAL = {
    "selected_candidate_id": "CAND-1",
    "approved_by": "Cleo",
    "approved_cost_ceiling_usd": 0.05,
    "deployment_authorized": True,
}

WORKSPACES_TITLE = (
    "Amazon WorkSpaces Now Lets AI Agents Operate Desktop Applications "
    "| Desktop and Application Streaming"
)
CONFIRMED_REGION = {"status": "feature_confirmed"}


class RecipeContractTests(unittest.TestCase):
    def test_registered_deployable_recipes_have_no_contract_gaps(self):
        for recipe in (S3_FILES, LAMBDA_SELF_MANAGED_STORAGE):
            self.assertEqual(recipe.contract_gaps(), [], recipe.recipe_id)
            self.assertTrue(recipe.is_deployable(), recipe.recipe_id)

    def test_every_deployable_recipe_declares_cleanup_and_evidence(self):
        for recipe_id in deployable_recipe_ids():
            recipe = get_recipe(recipe_id)
            self.assertTrue(recipe.cleanup_strategy, recipe_id)
            self.assertTrue(recipe.cleanup_verification, recipe_id)
            self.assertTrue(recipe.evidence_to_collect, recipe_id)
            self.assertTrue(recipe.success_criteria, recipe_id)

    def test_deployable_recipe_prices_every_resource_type_it_creates(self):
        for recipe_id in deployable_recipe_ids():
            recipe = get_recipe(recipe_id)
            self.assertTrue(recipe.estimated_cost_model_id, recipe_id)
            self.assertTrue(recipe.deployable_resource_types, recipe_id)

    def test_draft_recipe_is_not_deployable_and_names_what_is_missing(self):
        draft = WORKSPACES_AI_AGENT_ACCESS_DRAFT

        self.assertFalse(draft.is_deployable())
        self.assertEqual(
            sorted(draft.blocking_flags()),
            ["needs_cost_model", "needs_environment_preparation", "needs_region_confirmation"],
        )
        self.assertTrue(draft.draft_notes)


class RecipeSelectionTests(unittest.TestCase):
    def test_known_candidate_resolves_to_a_deployable_recipe(self):
        decision = select_recipe({"title": "Amazon S3 Files 正式推出"})

        self.assertEqual(decision["status"], "recipe_registered")
        self.assertTrue(decision["deployable_recipe_registered"])
        self.assertEqual(decision["recipe_id"], "s3_files_cdk")

    def test_unknown_candidate_returns_needs_new_recipe(self):
        decision = select_recipe({"title": "AWS Glue 新增某某功能"})

        self.assertEqual(decision["status"], "needs_new_recipe")
        self.assertFalse(decision["deployable_recipe_registered"])
        self.assertIsNone(decision["recipe_id"])
        self.assertIn("recipe", decision["next_step_zh"])

    def test_workspaces_candidate_matches_the_draft_but_cannot_deploy(self):
        decision = select_recipe({"title": WORKSPACES_TITLE})

        self.assertEqual(decision["status"], "recipe_draft_only")
        self.assertFalse(decision["deployable_recipe_registered"])
        self.assertEqual(decision["recipe_id"], "workspaces_ai_agent_access_draft")
        self.assertIn("needs_region_confirmation", decision["blocking"])

    def test_detected_services_can_match_a_recipe(self):
        decision = select_recipe(
            {"title": "某項桌面新功能", "related_aws_services": ["WorkSpaces"]}
        )

        self.assertEqual(decision["recipe_id"], "workspaces_ai_agent_access_draft")


class DeploymentGateTests(unittest.TestCase):
    def test_registered_recipe_with_full_approval_passes(self):
        result = run_deployment_preflight(
            {"title": "Amazon S3 Files"}, FULL_APPROVAL, CONFIRMED_REGION
        )

        self.assertEqual(result["status"], "ready_for_deployment")
        self.assertEqual(result["failed_checks"], [])
        self.assertEqual(len(result["checks"]), 8)

    def test_missing_recipe_blocks_deployment(self):
        result = run_deployment_preflight(
            {"title": "AWS Glue 新增某某功能"}, FULL_APPROVAL, CONFIRMED_REGION
        )

        self.assertEqual(result["status"], "blocked")
        self.assertIn("deployable_recipe_exists", result["failed_checks"])

    def test_draft_recipe_blocks_deployment(self):
        result = run_deployment_preflight(
            {"title": WORKSPACES_TITLE}, FULL_APPROVAL, CONFIRMED_REGION
        )

        self.assertEqual(result["status"], "blocked")
        self.assertIn("deployable_recipe_exists", result["failed_checks"])

    def test_generic_cost_model_cannot_substitute_for_a_recipe(self):
        candidate = {
            "title": "某個只有通用估價的候選",
            "cost_estimate": {"status": "estimated", "pricing_level": "Level B generic usage model"},
        }

        result = run_deployment_preflight(candidate, FULL_APPROVAL, CONFIRMED_REGION)

        self.assertEqual(result["status"], "blocked")
        self.assertIn("deployable_recipe_exists", result["failed_checks"])

    def test_missing_cost_ceiling_blocks_deployment(self):
        approval = {k: v for k, v in FULL_APPROVAL.items() if k != "approved_cost_ceiling_usd"}

        result = run_deployment_preflight({"title": "Amazon S3 Files"}, approval, CONFIRMED_REGION)

        self.assertIn("approved_cost_ceiling", result["failed_checks"])

    def test_missing_named_approval_blocks_deployment(self):
        approval = {**FULL_APPROVAL, "approved_by": "", "deployment_authorized": False}

        result = run_deployment_preflight({"title": "Amazon S3 Files"}, approval, CONFIRMED_REGION)

        self.assertIn("named_human_approval", result["failed_checks"])

    def test_unacknowledged_region_blocks_deployment(self):
        result = run_deployment_preflight(
            {"title": "Amazon S3 Files"}, FULL_APPROVAL, {"status": "region_unknown"}
        )

        self.assertIn("region_acknowledged_or_confirmed", result["failed_checks"])

    def test_acknowledged_unknown_region_is_allowed(self):
        result = run_deployment_preflight(
            {"title": "Amazon S3 Files"},
            FULL_APPROVAL,
            {"status": "region_unknown", "region_warning_acknowledged": True},
        )

        self.assertEqual(result["status"], "ready_for_deployment")


class Skill3HandoffTests(unittest.TestCase):
    def _s2(self, title: str) -> dict:
        return {
            "stage": "S2",
            "status": "ready_for_human_shortlist",
            "run_id": "run-recipe-test",
            "candidates": [
                {
                    "candidate_id": "CAND-1",
                    "title": title,
                    "source_url": "https://aws.amazon.com/example/",
                    "comparison_dimensions": {},
                    "proposal_card": {},
                    "evidence_coverage": {},
                }
            ],
        }

    def test_report_states_missing_recipe_and_the_next_step(self):
        result = build_evaluate(self._s2("AWS Glue 新增某某功能")).to_dict()

        readiness = result["evaluated_candidates"][0]["s4_readiness"]
        self.assertFalse(readiness["can_enter_skill4"])
        self.assertEqual(readiness["readiness_status"], "missing_deployable_recipe")
        self.assertIn("recipe", readiness["next_step_zh"])
        self.assertIn("s4-recipe-authoring-template", readiness["authoring_template"])
        self.assertNotIn("可否進入_skill4", readiness)

    def test_workspaces_draft_is_reported_as_not_deployable(self):
        result = build_evaluate(self._s2(WORKSPACES_TITLE)).to_dict()

        candidate = result["evaluated_candidates"][0]
        self.assertEqual(candidate["poc_recipe"]["status"], "recipe_draft_only")
        self.assertFalse(candidate["s4_readiness"]["can_enter_skill4"])

    def test_decision_gate_shows_recipe_verdict_per_option(self):
        result = build_evaluate(self._s2("Amazon S3 Files 正式推出")).to_dict()

        option = result["poc_decision_gate"]["options"][0]
        self.assertIn("recipe_decision", option)
        self.assertTrue(option["can_enter_skill4"])


class MainFlowGateTests(unittest.TestCase):
    """The gate has to hold inside build_deployment_context, not only beside it."""

    def _s2(self, title: str, **extra) -> dict:
        candidate = {
            "candidate_id": "CAND-1",
            "title": title,
            "source_url": "https://aws.amazon.com/blogs/example/",
            "comparison_dimensions": {},
            "proposal_card": {},
            "evidence_coverage": {},
        }
        candidate.update(extra)
        return {
            "stage": "S2",
            "status": "ready_for_human_shortlist",
            "run_id": "run-main-flow",
            "candidates": [candidate],
        }

    def _approved(self, evaluate: dict) -> dict:
        approval = build_approval_template(evaluate, "CAND-1", "Cleo", authorize=True)
        approval["deployment_authorized"] = True  # hand-edited, as a person might
        return approval

    def test_workspaces_real_headline_reaches_the_draft_recipe(self):
        result = build_evaluate(self._s2(WORKSPACES_TITLE)).to_dict()

        candidate = result["evaluated_candidates"][0]
        self.assertEqual(candidate["poc_recipe"]["status"], "recipe_draft_only")
        self.assertEqual(candidate["poc_recipe"]["recipe_id"], "workspaces_ai_agent_access_draft")
        self.assertFalse(candidate["s4_readiness"]["can_enter_skill4"])

    def test_workspaces_report_says_it_cannot_enter_skill4(self):
        report = render_poc_decision_report(build_evaluate(self._s2(WORKSPACES_TITLE)).to_dict())

        self.assertNotIn("請回覆同意進入 Skill 4", report)
        self.assertIn("目前不能進 Skill 4", report)
        self.assertIn("下一步是建立或補齊專用 recipe", report)

    def test_workspaces_context_is_not_deployable_even_when_authorized(self):
        evaluate = build_evaluate(self._s2(WORKSPACES_TITLE)).to_dict()

        context = build_deployment_context(evaluate, self._approved(evaluate))

        self.assertEqual(context["status"], "not_deployable")
        self.assertIn("preflight:deployable_recipe_exists", context["errors"])

    def test_generic_usage_model_context_is_not_deployable(self):
        evaluate = build_evaluate(self._s2("AWS Glue 新增某某功能")).to_dict()
        evaluate["evaluated_candidates"][0]["recommend_poc"] = True
        evaluate["evaluated_candidates"][0]["cost_estimate"] = {
            "status": "estimated",
            "pricing_level": "Level B generic usage model",
        }

        context = build_deployment_context(evaluate, self._approved(evaluate))

        self.assertEqual(context["status"], "not_deployable")
        self.assertIn("preflight:deployable_recipe_exists", context["errors"])

    def test_context_carries_the_full_preflight_result(self):
        evaluate = build_evaluate(self._s2("Amazon S3 Files 正式推出")).to_dict()

        context = build_deployment_context(evaluate, self._approved(evaluate))

        self.assertIn("preflight", context)
        self.assertEqual(len(context["preflight"]["checks"]), 8)
        self.assertIn("status", context["preflight"])

    def test_approval_template_exposes_the_recipe_verdict(self):
        evaluate = build_evaluate(self._s2(WORKSPACES_TITLE)).to_dict()

        template = build_approval_template(evaluate, "CAND-1", "Cleo", authorize=True)

        self.assertEqual(template["template_status"], "not_deployable_missing_recipe")
        self.assertFalse(template["can_enter_skill4"])
        self.assertFalse(template["deployment_authorized"])
        self.assertTrue(template["missing_recipe_reason_zh"])
        self.assertIn("recipe", template["required_next_step_zh"])
        self.assertEqual(template["success_criteria"], [])
        self.assertIsNone(template["approved_cost_ceiling_usd"])

    def test_deployable_candidate_still_produces_a_usable_approval_template(self):
        evaluate = build_evaluate(self._s2("Amazon S3 Files 正式推出")).to_dict()

        template = build_approval_template(evaluate, "CAND-1", "Cleo", authorize=True)

        self.assertEqual(template["template_status"], "ready_for_human_approval")
        self.assertTrue(template["can_enter_skill4"])
        self.assertTrue(template["success_criteria"])
        self.assertIsNotNone(template["approved_cost_ceiling_usd"])
        self.assertTrue(template["cleanup_scope"])

    def test_lambda_recipe_still_produces_an_approval_template(self):
        evaluate = build_evaluate(
            self._s2(
                "AWS Lambda 宣布自主管理程式碼儲存空間",
                source_url="https://aws.amazon.com/x/lambda-self-managed-code-storage/",
            )
        ).to_dict()

        template = build_approval_template(evaluate, "CAND-1", "Cleo", authorize=True)

        self.assertTrue(template["can_enter_skill4"])
        self.assertEqual(
            template["recipe_decision"]["recipe_id"],
            "lambda_self_managed_s3_code_storage_cdk",
        )

    def test_approval_uses_the_canonical_ceiling_field_only(self):
        evaluate = build_evaluate(self._s2("Amazon S3 Files 正式推出")).to_dict()

        template = build_approval_template(evaluate, "CAND-1", "Cleo", authorize=True)

        self.assertIn("approved_cost_ceiling_usd", template)
        self.assertNotIn("approved_ceiling_usd", template)

    def test_legacy_ceiling_alias_is_read_but_never_written_back(self):
        evaluate = build_evaluate(self._s2("Amazon S3 Files 正式推出")).to_dict()
        approval = self._approved(evaluate)
        approval.pop("approved_cost_ceiling_usd", None)
        approval["approved_ceiling_usd"] = 0.05  # older artifact

        context = build_deployment_context(evaluate, approval)

        self.assertEqual(context["approved_cost_ceiling_usd"], 0.05)
        self.assertNotIn("preflight:approved_cost_ceiling", context["errors"])
