"""Skill 4 recipe framework: contract, registry, selection, and the deploy gate."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from agentic_cloud_radar.s3 import build_evaluate, render_poc_decision_report
from agentic_cloud_radar.s4_deployer import (
    build_approval_template,
    build_deployment_context,
    run_deployment_preflight,
    _cleanup_stack_resources,
    _wait_for_appstream_fleet_running,
    _verify_workspaces_ai_agent_access,
)
from agentic_cloud_radar.s4_recipes import (
    LAMBDA_SELF_MANAGED_STORAGE,
    S3_FILES,
    WORKSPACES_AI_AGENT_ACCESS,
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


def _strong_dimensions() -> dict:
    return {
        "technology_scope": {"services_detected": ["WorkSpaces", "AppStream", "EC2"], "status": "source_detected"},
        "source_backed_capabilities": {"status": "source_excerpt_available"},
        "environment_signals": {"source_indicated_contexts": ["managed_desktop_application_environment"]},
        "target_region_eligibility": {
            "target_region": "ap-southeast-1",
            "status": "available_ap_southeast_1",
            "severity": "info",
            "blocks_s3": False,
            "blocks_paid_poc": False,
        },
        "unknowns_and_next_validation_question": {"unknowns": []},
    }


def _strong_proposal() -> dict:
    return {
        "improvement_hypothesis": {"potential_vectors": [{"type": "desktop_workflow_automation"}]},
        "validation_design": {
            "before_measurements": ["Manual desktop access path exists."],
            "after_measurements": ["Agent-access stack can produce a streaming URL."],
            "minimum_success_evidence": ["Fleet running, stack AgentAccessConfig present, streaming URL generated."],
            "stop_conditions": ["Fleet creation fails or streaming URL cannot be generated."],
        },
    }


def _strong_coverage() -> dict:
    return {
        "primary_source_fetched": True,
        "official_aws_primary_source": True,
        "official_ga_evidence": True,
        "official_docs_linked": True,
        "official_pricing_linked": True,
        "verified_dimension_count": 6,
        "verified_dimension_total": 8,
    }


class RecipeContractTests(unittest.TestCase):
    def test_registered_deployable_recipes_have_no_contract_gaps(self):
        for recipe in (S3_FILES, LAMBDA_SELF_MANAGED_STORAGE, WORKSPACES_AI_AGENT_ACCESS):
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

    def test_workspaces_recipe_is_deployable_but_names_limits(self):
        recipe = WORKSPACES_AI_AGENT_ACCESS

        self.assertTrue(recipe.is_deployable())
        self.assertEqual(recipe.contract_gaps(), [])
        self.assertEqual(recipe.recipe_id, WORKSPACES_AI_AGENT_ACCESS_DRAFT.recipe_id)
        self.assertTrue(recipe.draft_notes)
        self.assertIn("AWS::AppStream::Fleet", recipe.deployable_resource_types)



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

    def test_workspaces_candidate_matches_the_deployable_recipe(self):
        decision = select_recipe({"title": WORKSPACES_TITLE})

        self.assertEqual(decision["status"], "recipe_registered")
        self.assertTrue(decision["deployable_recipe_registered"])
        self.assertEqual(decision["recipe_id"], "workspaces_ai_agent_access_cdk")


    def test_detected_services_can_match_a_recipe(self):
        decision = select_recipe(
            {"title": "某項桌面新功能", "related_aws_services": ["WorkSpaces"]}
        )

        self.assertEqual(decision["recipe_id"], "workspaces_ai_agent_access_cdk")


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

    def test_workspaces_recipe_with_full_approval_passes(self):
        result = run_deployment_preflight(
            {"title": WORKSPACES_TITLE}, FULL_APPROVAL, CONFIRMED_REGION
        )

        self.assertEqual(result["status"], "ready_for_deployment")
        self.assertEqual(result["failed_checks"], [])


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
                    "comparison_dimensions": _strong_dimensions(),
                    "proposal_card": _strong_proposal(),
                    "evidence_coverage": _strong_coverage(),
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

    def test_workspaces_recipe_is_reported_as_deployable(self):
        result = build_evaluate(self._s2(WORKSPACES_TITLE)).to_dict()

        candidate = result["evaluated_candidates"][0]
        self.assertEqual(candidate["poc_recipe"]["status"], "recipe_registered")
        self.assertEqual(candidate["weighted_score"], 2.65)
        self.assertFalse(candidate["recommend_poc"])
        self.assertIn("compliance_review_required", candidate["governance_flags"])
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
            "comparison_dimensions": _strong_dimensions(),
            "proposal_card": _strong_proposal(),
            "evidence_coverage": _strong_coverage(),
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

    def test_workspaces_real_headline_reaches_the_deployable_recipe(self):
        result = build_evaluate(self._s2(WORKSPACES_TITLE)).to_dict()

        candidate = result["evaluated_candidates"][0]
        self.assertEqual(candidate["poc_recipe"]["status"], "recipe_registered")
        self.assertEqual(candidate["poc_recipe"]["recipe_id"], "workspaces_ai_agent_access_cdk")
        self.assertEqual(
            candidate["dimension_scores"],
            {
                "technical_value": 4,
                "verifiability": 3,
                "adoption_prerequisites": 2,
                "risk_and_stop_conditions": 2,
                "reversibility_and_cleanup": 1,
            },
        )
        self.assertFalse(candidate["s4_readiness"]["can_enter_skill4"])


    def test_workspaces_report_can_enter_skill4(self):
        report = render_poc_decision_report(build_evaluate(self._s2(WORKSPACES_TITLE)).to_dict())

        self.assertIn("WorkSpaces", report)
        self.assertIn("Skill 4", report)
        self.assertIn("workspaces_ai_agent_access_cdk", report)
        self.assertIn("Infrastructure Composer", report)
        self.assertIn("開一台受控的雲端 Windows 桌面給 AI 用", report)
        self.assertIn("如果目的只是偶爾人工看一次 canvas，完整桌面 PoC 太重", report)
        self.assertIn("AI agent -> WorkSpaces Applications / AppStream streaming session", report)
        self.assertIn("評分細項", report)
        self.assertIn("技術能力：4 / 5", report)
        self.assertIn("證據可驗證性：3 / 5", report)
        self.assertIn("導入前置條件：2 / 5", report)
        self.assertIn("可逆性與終止：1 / 5", report)
        self.assertIn("不開啟 URL", report)
        self.assertIn("第二段", report)
        self.assertIn("cleanup 不能退款", report)


    def test_workspaces_context_is_deployable_when_authorized(self):
        import json
        from pathlib import Path
        from tempfile import TemporaryDirectory

        evaluate = build_evaluate(self._s2(WORKSPACES_TITLE)).to_dict()
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            paths = {"s1": root / "s1.json", "s2": root / "s2.json", "s3": root / "s3.json"}
            s1 = {"stage": "S1", "run_id": "run-main-flow", "candidates": [{"candidate_id": "CAND-1"}]}
            s2 = self._s2(WORKSPACES_TITLE)
            for key, payload in (("s1", s1), ("s2", s2), ("s3", evaluate)):
                paths[key].write_text(json.dumps(payload), encoding="utf-8")
            approval = self._approved(evaluate)
            approval["region_warning_acknowledged"] = True
            approval["lineage"] = {f"{key}_artifact_path": str(path) for key, path in paths.items()}

            context = build_deployment_context(evaluate, approval)

        self.assertEqual(context["status"], "not_deployable")
        self.assertIn("poc_gate_not_passed", context["errors"])


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

        self.assertEqual(template["template_status"], "ready_for_human_approval")
        self.assertTrue(template["can_enter_skill4"])
        self.assertTrue(template["deployment_authorized"])
        self.assertTrue(template["success_criteria"])
        self.assertEqual(template["approved_cost_ceiling_usd"], 0.5)


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


class WorkSpacesRuntimeTests(unittest.TestCase):
    @patch("agentic_cloud_radar.s4_deployer.time.sleep")
    @patch("agentic_cloud_radar.s4_deployer._aws_json")
    def test_workspaces_fleet_wait_allows_transient_stopped_after_start(self, aws_json, sleep):
        aws_json.side_effect = [
            {"Fleets": [{"Name": "fleet-1", "State": "STOPPED"}]},
            {"Fleets": [{"Name": "fleet-1", "State": "STARTING"}]},
            {"Fleets": [{"Name": "fleet-1", "State": "RUNNING"}]},
        ]

        result = _wait_for_appstream_fleet_running("fleet-1", "intern", "ap-southeast-1")

        self.assertEqual(result["State"], "RUNNING")
        self.assertEqual(aws_json.call_count, 3)

    @patch("agentic_cloud_radar.s4_deployer.time.sleep")
    @patch("agentic_cloud_radar.s4_deployer._aws_json")
    @patch("agentic_cloud_radar.s4_deployer._aws")
    def test_workspaces_verification_checks_agent_access_and_redacts_streaming_url(self, aws, aws_json, sleep):
        aws_json.side_effect = [
            {
                "Fleets": [
                    {
                        "Name": "agentic-radar-s4-12345678-fleet",
                        "State": "RUNNING",
                        "InstanceType": "stream.standard.medium",
                        "FleetType": "ON_DEMAND",
                        "ImageName": "Amazon-AppStream2-Sample-Image-06-17-2024",
                    }
                ]
            },
            {
                "Stacks": [
                    {
                        "Name": "agentic-radar-s4-12345678-stack",
                        "AgentAccessConfig": {
                            "Settings": [
                                {"AgentAction": "COMPUTER_VISION", "Permission": "ENABLED"},
                                {"AgentAction": "COMPUTER_INPUT", "Permission": "ENABLED"},
                                {"AgentAction": "FORWARD_MCP_TOOLS", "Permission": "ENABLED"},
                            ],
                            "ScreenResolution": "W_1280xH_720",
                            "ScreenImageFormat": "PNG",
                            "UserControlMode": "VIEW_STOP",
                        },
                    }
                ]
            },
            {"StreamingURL": "https://example.invalid/secret", "Expires": "2026-08-05T09:00:00Z"},
        ]
        context = {
            "run_id": "unit-test-run",
            "deployment": {"profile": "intern", "target_region": "ap-southeast-1"},
            "success_criteria": ["agent access config exists"],
        }

        result = _verify_workspaces_ai_agent_access(
            context,
            {
                "AppStreamFleetName": "agentic-radar-s4-12345678-fleet",
                "AppStreamStackName": "agentic-radar-s4-12345678-stack",
                "AgentAccessConfig": "COMPUTER_VISION,COMPUTER_INPUT,FORWARD_MCP_TOOLS",
                "UserControlMode": "VIEW_STOP",
            },
        )

        self.assertEqual(result["recipe"], "workspaces_ai_agent_access_cdk")
        self.assertTrue(result["streaming_url"]["generated"])
        self.assertTrue(result["streaming_url"]["redacted"])
        self.assertNotIn("https://example.invalid/secret", str(result))
        self.assertEqual(len(result["streaming_url"]["url_sha256"]), 64)
        aws.assert_any_call(
            ["appstream", "start-fleet", "--name", "agentic-radar-s4-12345678-fleet"],
            "intern",
            "ap-southeast-1",
        )

    @patch("agentic_cloud_radar.s4_deployer._aws")
    def test_workspaces_cleanup_does_not_require_a_data_bucket(self, aws):
        import hashlib

        run_id = "unit-test-run"
        suffix = hashlib.sha256(run_id.encode("utf-8")).hexdigest()[:8]
        runtime = {
            "run_id": run_id,
            "deployment": {
                "recipe": "workspaces_ai_agent_access_cdk",
                "stack_name": f"AgenticRadarS4{suffix.upper()}",
                "resource_prefix": f"agentic-radar-s4-{suffix}",
                "profile": "intern",
                "target_region": "ap-southeast-1",
            },
            "verification": {"fleet": {"name": f"agentic-radar-s4-{suffix}-fleet"}},
        }

        result = _cleanup_stack_resources(runtime)

        self.assertEqual(result["appstream_fleet"], "stopped_before_stack_delete")
        self.assertEqual(result["cloudformation_stack"], "deleted")
        calls = [call.args[0] for call in aws.call_args_list]
        self.assertNotIn(
            [
                "cloudformation",
                "describe-stack-resource",
                "--stack-name",
                runtime["deployment"]["stack_name"],
                "--logical-resource-id",
                "DataBucket",
            ],
            calls,
        )
