"""S4 controlled PoC deployment runner.

The validator in :mod:`s4` decides whether a PoC may be reviewed. This
module owns the later, explicit actions: prove S1/S2/S3 lineage, select a
candidate-specific recipe, synthesize CDK, deploy through CloudFormation,
run the recipe verification, wait for Console review, and clean up.

No function in this module is called by normal ``s4``. Resource creation
requires both ``deployment_authorized=true`` in a human approval artifact and
an explicit CLI ``--execute`` flag.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import time
from typing import Any

from .s4 import DEFAULT_MAX_SMALL_POC_USD, build_validate


RADAR_ROOT = Path(__file__).resolve().parents[1]
# The main workspace keeps ``poc/`` beside ``radar-redesign/``.  The portable
# Claude handoff keeps it inside the handoff root.  Resolve either layout
# without changing the recorded deployment recipe contract.
PROJECT_ROOT = RADAR_ROOT if (RADAR_ROOT / "poc").is_dir() else RADAR_ROOT.parent
DEFAULT_PROFILE = "intern"
DEFAULT_REGION = "ap-southeast-1"
COMMAND_TIMEOUT_SECONDS = 900
DEFAULT_CLEANUP_SCOPE = (
    "Delete the run-derived CloudFormation stack.",
    "Remove only test data owned by that stack.",
    "Verify the stack and active test resources are gone.",
)
CONSOLE_REVIEW_EVIDENCE_SCHEMA = "s4.console-review-evidence.v1"
DEPLOYMENT_APPROVAL_SCHEMA = "s4.deployment-approval.v1"
REQUIRED_CONSOLE_VIEW = "infrastructure_composer"


from .s4_recipes import (
    canonicalize_approval,
    deployment_preflight,
    get_recipe,
    read_cost_ceiling,
    select_recipe,
)


class DeploymentError(RuntimeError):
    """Raised when an explicit S4 deployment or cleanup command cannot finish."""


@dataclass(frozen=True)
class PocRecipe:
    """A deployable implementation for one candidate family.

    Recipes are intentionally registered in code. A candidate without a
    registered recipe is reported as ``needs_poc_recipe`` rather than receiving
    an unrelated CloudFormation template.
    """

    key: str
    poc_directory: Path
    success_criteria: tuple[str, ...]


def _from_registry(recipe_id: str) -> PocRecipe:
    """Build the deployer's runtime view from the registry definition."""

    definition = get_recipe(recipe_id)
    if definition is None or definition.poc_directory is None:
        raise DeploymentError(f"Registry has no deployable definition for {recipe_id}.")
    return PocRecipe(
        key=definition.recipe_id,
        poc_directory=definition.poc_directory,
        success_criteria=tuple(definition.success_criteria),
    )


S3_FILES_RECIPE = _from_registry("s3_files_cdk")
LAMBDA_SELF_MANAGED_STORAGE_RECIPE = _from_registry("lambda_self_managed_s3_code_storage_cdk")


def build_approval_template(
    evaluate: dict[str, Any],
    selected_candidate_id: str | None = None,
    approved_by: str | None = None,
    authorize: bool = False,
) -> dict[str, Any]:
    """Create the human-editable S4 approval file from a Skill 3 artifact."""

    if evaluate.get("stage") != "S3" or evaluate.get("status") not in {"awaiting_poc_decision", "evaluated"}:
        raise DeploymentError("S4 approval template requires an evaluated Skill 3 artifact.")
    candidates = evaluate.get("evaluated_candidates") or []
    selected = _select_approval_candidate(candidates, selected_candidate_id)
    candidate_id = str(selected.get("candidate_id") or "")
    if not candidate_id:
        raise DeploymentError("Selected Skill 3 candidate has no candidate_id.")
    quote = ((selected.get("cost_estimate") or {}).get("quote") or {})
    recipe = _recipe_for(selected)
    recommended_ceiling = quote.get("recommended_approval_ceiling_usd")
    policy_ceiling = float((evaluate.get("policy") or {}).get("max_small_poc_usd", DEFAULT_MAX_SMALL_POC_USD))
    effective_ceiling = _minimum_numeric(
        recommended_ceiling,
        policy_ceiling,
    )
    decision = select_recipe(selected)
    can_enter_skill4 = bool(decision.get("deployable_recipe_registered"))
    # An approval file for a candidate with no deployable recipe must not look
    # ready. Flipping deployment_authorized by hand still fails the context gate,
    # but the template should say so rather than leave the reader to find out.
    authorized = bool(authorize) and can_enter_skill4
    return {
        "schema_version": DEPLOYMENT_APPROVAL_SCHEMA,
        "template_status": "ready_for_human_approval" if can_enter_skill4 else "not_deployable_missing_recipe",
        "approved_at": _now() if authorized and approved_by else None,
        "run_id": evaluate.get("run_id"),
        "selected_candidate_id": candidate_id,
        "approved_by": str(approved_by or "").strip() or None,
        "deployment_authorized": authorized,
        "recipe_decision": decision,
        "can_enter_skill4": can_enter_skill4,
        "missing_recipe_reason_zh": "" if can_enter_skill4 else decision.get("reason_zh", ""),
        "required_next_step_zh": (
            "確認分數、報價、區域狀態與清除範圍後，將 deployment_authorized 設為 true。"
            if can_enter_skill4
            else decision.get("next_step_zh", "下一步是建立或補齊專用 recipe，不是建立 AWS 資源。")
        ),
        "approval_basis": (
            "Review the Skill 3 score, quote, Region status, recipe, success criteria, "
            "cleanup scope, and known limits before setting deployment_authorized=true."
        ),
        "approved_cost_ceiling_usd": effective_ceiling if can_enter_skill4 else None,
        "success_criteria": list(recipe.success_criteria) if (recipe and can_enter_skill4) else [],
        "cleanup_scope": list(DEFAULT_CLEANUP_SCOPE) if can_enter_skill4 else [],
        "cost_ceiling_policy": {
            "rule": "effective_ceiling_usd = min(Skill 3 recommended approval ceiling, human approved ceiling, built-in small-cost ceiling)",
            "skill3_recommended_approval_ceiling_usd": recommended_ceiling,
            "built_in_small_cost_ceiling_usd": policy_ceiling,
            "human_may_lower_ceiling": True,
            "human_may_raise_above_built_in_ceiling": False,
        },
        "region_warning_acknowledged": False,
        "quote_snapshot": {
            "quote_id": quote.get("quote_id"),
            "status": quote.get("status") or (selected.get("cost_estimate") or {}).get("status"),
            "expected_total_usd": quote.get("expected_total_usd"),
            "recommended_approval_ceiling_usd": recommended_ceiling,
            "valid_until": quote.get("valid_until"),
            "live_pricing_api_used": quote.get("live_pricing_api_used") is True,
            "formal_procurement_quote_ready": quote.get("formal_procurement_quote_ready") is True,
        },
        "deployment": {
            "profile": DEFAULT_PROFILE,
            "target_region": DEFAULT_REGION,
            "create_test_instance": True,
        },
        "lineage": {
            "s1_artifact_path": "REPLACE_WITH_ABSOLUTE_PATH_TO_S1_JSON",
            "s2_artifact_path": "REPLACE_WITH_ABSOLUTE_PATH_TO_S2_JSON",
            "s3_artifact_path": "REPLACE_WITH_ABSOLUTE_PATH_TO_S3_JSON",
        },
    }


def build_deployment_context(evaluate: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
    """Create an auditable, non-deploying context from a human-approved S3 run."""

    approval = canonicalize_approval(approval)
    validation = build_validate(evaluate, approval).to_dict()
    selected_id = str(approval.get("selected_candidate_id") or "").strip()
    selected = next(
        (item for item in evaluate.get("evaluated_candidates") or [] if item.get("candidate_id") == selected_id),
        None,
    )
    errors = _context_errors(evaluate, approval, validation, selected)
    lineage, lineage_errors = _verify_lineage(evaluate, approval.get("lineage") or {}, selected_id)
    errors.extend(lineage_errors)
    recipe = _recipe_for(selected) if selected else None
    if not recipe and selected:
        errors.append("needs_poc_recipe")

    # The recipe gate runs inside the real context builder, not beside it: a
    # deployment that never reads the preflight would be protected only in tests.
    preflight = run_deployment_preflight(selected, approval, _region_state(selected, approval))
    errors.extend(f"preflight:{name}" for name in preflight.get("failed_checks") or [])

    run_id = str(evaluate.get("run_id") or "unknown-run")
    suffix = hashlib.sha256(run_id.encode("utf-8")).hexdigest()[:8]
    deployment = approval.get("deployment") or {}
    context = {
        "schema_version": "s4.deployment-context.v3",
        "stage": "S4",
        "created_at": _now(),
        "run_id": run_id,
        "status": "ready_for_manual_deployment" if not errors else "not_deployable",
        "lineage": lineage,
        "selected_candidate": _candidate_summary(selected),
        "s4_validation": _selected_validation(validation, selected_id),
        "authorization": {
            "approved_by": approval.get("approved_by"),
            "approved_at": approval.get("approved_at"),
            "deployment_authorized": approval.get("deployment_authorized") is True,
            "automatic_poc_start": False,
            "approval_basis": approval.get("approval_basis"),
        },
        "deployment": {
            "recipe": recipe.key if recipe else None,
            "stack_name": f"AgenticRadarS4{suffix.upper()}",
            "resource_prefix": f"agentic-radar-s4-{suffix}",
            "profile": deployment.get("profile") or DEFAULT_PROFILE,
            "target_region": deployment.get("target_region") or DEFAULT_REGION,
            "create_test_instance": bool(deployment.get("create_test_instance", True)),
        },
        "success_criteria": list(approval.get("success_criteria") or (recipe.success_criteria if recipe else [])),
        "cleanup_scope": list(approval.get("cleanup_scope") or DEFAULT_CLEANUP_SCOPE),
        "approved_cost_ceiling_usd": read_cost_ceiling(approval),
        "preflight": preflight,
        "errors": _dedupe(errors),
    }
    return context


def _region_state(candidate: dict[str, Any] | None, approval: dict[str, Any]) -> dict[str, Any]:
    """Combine the candidate's recorded Region evidence with the approver's acknowledgement."""

    region = ((candidate or {}).get("region_status") or {})
    return {
        "status": region.get("status"),
        "region_warning_acknowledged": approval.get("region_warning_acknowledged") is True,
    }


def execute_deployment(context: dict[str, Any]) -> dict[str, Any]:
    """Deploy and verify a recipe after all non-automatic gates are satisfied."""

    _require_deployable_context(context)
    recipe = _recipe_by_key(str((context.get("deployment") or {}).get("recipe") or ""))
    if not recipe:
        raise DeploymentError("The selected candidate does not have a registered deployable recipe.")

    deployment = context["deployment"]
    work_dir = _work_dir(context)
    work_dir.mkdir(parents=True, exist_ok=True)
    template_path = _synthesize(recipe, deployment, work_dir)
    profile = str(deployment["profile"])
    region = str(deployment["target_region"])
    stack_name = str(deployment["stack_name"])

    _aws(["cloudformation", "validate-template", "--template-body", f"file://{template_path}"], profile, region)
    stack_status = _stack_status_or_none(stack_name, profile, region)
    if stack_status is None:
        _aws(
            [
                "cloudformation",
                "create-stack",
                "--stack-name",
                stack_name,
                "--template-body",
                f"file://{template_path}",
                "--capabilities",
                "CAPABILITY_IAM",
                "--on-failure",
                "DELETE",
            ],
            profile,
            region,
        )
        _aws(["cloudformation", "wait", "stack-create-complete", "--stack-name", stack_name], profile, region)
    elif stack_status == "CREATE_IN_PROGRESS":
        _aws(["cloudformation", "wait", "stack-create-complete", "--stack-name", stack_name], profile, region)
    elif stack_status != "CREATE_COMPLETE":
        raise DeploymentError(f"Existing PoC stack cannot resume verification from status {stack_status}.")
    outputs = _stack_outputs(stack_name, profile, region)
    verification = _verify_recipe(recipe, context, outputs, work_dir)

    return {
        "schema_version": "s4.runtime-evidence.v3",
        "stage": "S4",
        "run_id": context.get("run_id"),
        "status": "awaiting_console_review",
        "deployed_at": _now(),
        "lineage": context.get("lineage"),
        "deployment": {
            "recipe": recipe.key,
            "stack_name": stack_name,
            "resource_prefix": deployment["resource_prefix"],
            "profile": profile,
            "target_region": region,
            "deployment_method": "CDK synth followed by CloudFormation create-stack",
            "stack_status": "CREATE_COMPLETE",
        },
        "verification": verification,
        "console_review": {
            "status": "required",
            "evidence_status": "awaiting_capture",
            "required_checks": [
                "CloudFormation stack Resources and Template",
                "Recipe resources and their expected relationships",
                "Test workload result",
            ],
            "required_screenshot_views": [REQUIRED_CONSOLE_VIEW],
            "recommended_screenshot_views": ["resource_inventory"],
        },
        "cleanup": {"status": "pending_console_review"},
    }


def build_console_review_packet(runtime: dict[str, Any], review_timeout_minutes: int = 60) -> dict[str, Any]:
    """Build the human-facing screenshot checklist for one deployed PoC run."""

    if runtime.get("stage") != "S4" or runtime.get("status") != "awaiting_console_review":
        raise DeploymentError("A Console review packet requires an S4 runtime artifact awaiting review.")
    if not 1 <= review_timeout_minutes <= 1_440:
        raise DeploymentError("Console review timeout must be between 1 and 1440 minutes.")
    deployment = runtime.get("deployment") or {}
    region = str(deployment.get("target_region") or DEFAULT_REGION)
    stack_name = str(deployment.get("stack_name") or "")
    run_id = str(runtime.get("run_id") or "unknown-run")
    screenshot_dir = f".\\out\\run\\s4-console-review\\{_safe_path_segment(run_id)}"
    evidence_path = f"{screenshot_dir}\\s4-console-review-evidence.json"
    issued_at = datetime.now(timezone.utc)
    review_deadline = issued_at + timedelta(minutes=review_timeout_minutes)
    return {
        "schema_version": "s4.console-review-packet.v1",
        "stage": "S4",
        "run_id": runtime.get("run_id"),
        "status": "awaiting_human_confirmation",
        "issued_at": issued_at.isoformat(),
        "review_deadline": review_deadline.isoformat(),
        "review_target": {
            "stack_name": stack_name,
            "target_region": region,
            "recipe": deployment.get("recipe"),
            "composer_url": _composer_url(region),
            "cloudformation_stack_url": _cloudformation_stack_url(region, stack_name),
        },
        "automation": {
            "mode": "playwright_headful_browser",
            "command": (
                "node .\\scripts\\s4-capture-infrastructure-composer.mjs "
                f"--runtime .\\out\\run\\s4-runtime.json --packet .\\out\\run\\s4-console-review-packet.json "
                f"--output-dir {screenshot_dir} --evidence-output {evidence_path} --shared-via conversation"
            ),
            "outputs": {
                "required_png": f"{screenshot_dir}\\infrastructure-composer.png",
                "review_evidence": evidence_path,
            },
            "human_display_required": True,
            "cleanup_must_wait_for_named_confirmation": True,
        },
        "required_screenshots": [
            {
                "view": REQUIRED_CONSOLE_VIEW,
                "console_location": "CloudFormation stack > Infrastructure Composer",
                "must_show": [
                    "The run-derived stack's resource relationship canvas",
                    "The deployed resources are visible and match the selected recipe",
                ],
            }
        ],
        "recommended_screenshots": [
            {
                "view": "resource_inventory",
                "console_location": "CloudFormation stack > Resources or candidate-service resource page",
                "must_show": ["Resource statuses", "The test workload result when the Console exposes it"],
            }
        ],
        "human_confirmation": {
            "required": True,
            "instruction": "Show the screenshots in the GUI or this conversation, then wait for a named human to approve cleanup.",
        },
        "evidence_contract": {
            "schema_version": CONSOLE_REVIEW_EVIDENCE_SCHEMA,
            "required_review_target_fields": ["stack_name", "target_region", "run_id"],
            "required_fields_per_screenshot": [
                "view",
                "screenshot_ref",
                "sha256",
                "captured_at",
                "shared_via",
                "redacted",
                "hash_scope",
            ],
            "allowed_shared_via": ["gui", "conversation"],
            "privacy_order": "capture visible canvas -> hide/redact Console chrome -> hash the redacted PNG -> show the redacted PNG to the human",
            "automated_image_understanding": False,
            "human_confirmation_record_only": True,
        },
        "privacy": [
            "Do not commit Console screenshots or unredacted Console URLs to Git.",
            "Store only redacted screenshot references, SHA-256 hashes, run-derived stack name, Region, and capture time in the review evidence JSON.",
            "The metadata contract cannot prove the pixels show the correct stack; a named human must confirm the screenshot content before cleanup.",
        ],
        "timeout_policy": {
            "review_timeout_minutes": review_timeout_minutes,
            "on_timeout": "After review_deadline, use s4-abort --packet <packet> --execute with a named cost-control approver and reason; record that Console screenshot review was skipped for cost control.",
        },
    }


def record_console_review(
    runtime: dict[str, Any],
    confirmed_by: str,
    notes: str | None = None,
    review_evidence: dict[str, Any] | None = None,
    review_packet: dict[str, Any] | None = None,
    shared_via: str | None = None,
) -> dict[str, Any]:
    """Record screenshot-backed human Console confirmation before cleanup is permitted."""

    reviewer = str(confirmed_by or "").strip()
    if runtime.get("stage") != "S4" or runtime.get("status") != "awaiting_console_review":
        raise DeploymentError("Console review requires an S4 runtime artifact awaiting review.")
    if not reviewer:
        raise DeploymentError("Console review requires a named human reviewer.")
    confirmed_channel = str(shared_via or "").strip()
    if confirmed_channel not in {"gui", "conversation"}:
        raise DeploymentError("Console review requires the GUI or conversation channel where the human saw the screenshot.")
    evidence = _validated_review_evidence(runtime, review_evidence, review_packet)
    reviewed = dict(runtime)
    reviewed["status"] = "ready_for_cleanup"
    reviewed["console_review"] = {
        **dict(runtime.get("console_review") or {}),
        "status": "confirmed",
        "confirmed_by": reviewer,
        "confirmed_at": _now(),
        "notes": str(notes or "").strip() or None,
        "evidence_status": "captured_and_confirmed",
        "display_channel_confirmed": confirmed_channel,
        "evidence": evidence,
    }
    reviewed["cleanup"] = {"status": "ready_for_manual_cleanup"}
    return reviewed


def execute_cleanup(runtime: dict[str, Any]) -> dict[str, Any]:
    """Remove only this stack's test data and resources after Console review."""

    if runtime.get("stage") != "S4" or runtime.get("status") != "ready_for_cleanup":
        raise DeploymentError("Cleanup requires a Console-reviewed S4 runtime artifact.")
    if runtime.get("schema_version") == "s4.runtime-evidence.v3" and (
        (runtime.get("console_review") or {}).get("evidence_status") != "captured_and_confirmed"
        or (runtime.get("console_review") or {}).get("display_channel_confirmed") not in {"gui", "conversation"}
    ):
        raise DeploymentError("Cleanup requires screenshot-backed Console confirmation for this runtime schema.")
    usage_snapshot = _pre_cleanup_usage_snapshot(runtime)
    try:
        checks = _cleanup_stack_resources(runtime)
    except DeploymentError as exc:
        failed = dict(runtime)
        failed["status"] = "cleanup_failed"
        failed["pre_cleanup_usage_snapshot"] = usage_snapshot
        failed["cleanup"] = {
            "status": "failed",
            "failed_at": _now(),
            "pre_cleanup_usage_snapshot_status": usage_snapshot.get("status"),
            "error": str(exc),
            "orphan_resource_risk": True,
            "next_action": "Inspect the run-derived stack and re-run scoped cleanup after the blocker is removed.",
        }
        raise DeploymentError(json.dumps(failed, ensure_ascii=False)) from exc

    cleaned = dict(runtime)
    cleaned["status"] = "cleanup_verified"
    cleaned["pre_cleanup_usage_snapshot"] = usage_snapshot
    cleaned["cleanup"] = {
        "status": "verified",
        "verified_at": _now(),
        "pre_cleanup_usage_snapshot_status": usage_snapshot.get("status"),
        "checks": checks,
    }
    return cleaned


def execute_abort_cleanup(
    runtime: dict[str, Any], confirmed_by: str, reason: str, review_packet: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Emergency cleanup for timed out or failed S4 runs without Console screenshots."""

    reviewer = str(confirmed_by or "").strip()
    abort_reason = str(reason or "").strip()
    if runtime.get("stage") != "S4" or runtime.get("status") not in {
        "awaiting_console_review",
        "ready_for_cleanup",
        "deployment_failed",
        "cleanup_failed",
    }:
        raise DeploymentError("Abort cleanup requires an S4 runtime that is deployed, failed, or already partially closing.")
    if not reviewer:
        raise DeploymentError("Abort cleanup requires a named cost-control approver.")
    if len(abort_reason) < 12:
        raise DeploymentError("Abort cleanup requires a concrete reason.")
    if runtime.get("status") in {"awaiting_console_review", "ready_for_cleanup"}:
        _validate_abort_review_deadline(runtime, review_packet)
    usage_snapshot = _pre_cleanup_usage_snapshot(runtime)
    try:
        checks = _cleanup_stack_resources(runtime)
    except DeploymentError as exc:
        failed = dict(runtime)
        failed["status"] = "cleanup_failed"
        failed["pre_cleanup_usage_snapshot"] = usage_snapshot
        failed["console_review"] = {
            **dict(runtime.get("console_review") or {}),
            "status": "skipped_for_cost_control",
            "evidence_status": "not_captured_abort_cleanup_failed",
            "confirmed_by": reviewer,
            "reason": abort_reason,
        }
        failed["cleanup"] = {
            "status": "failed",
            "failed_at": _now(),
            "pre_cleanup_usage_snapshot_status": usage_snapshot.get("status"),
            "error": str(exc),
            "orphan_resource_risk": True,
            "next_action": "Escalate the run-derived residual resources for manual remediation.",
        }
        raise DeploymentError(json.dumps(failed, ensure_ascii=False)) from exc
    cleaned = dict(runtime)
    cleaned["status"] = "cleanup_verified"
    cleaned["console_review"] = {
        **dict(runtime.get("console_review") or {}),
        "status": "skipped_for_cost_control",
        "evidence_status": "not_captured_emergency_cleanup",
        "confirmed_by": reviewer,
        "confirmed_at": _now(),
        "reason": abort_reason,
    }
    cleaned["cleanup"] = {
        "status": "verified",
        "verified_at": _now(),
        "cleanup_mode": "abort_without_console_review",
        "pre_cleanup_usage_snapshot_status": usage_snapshot.get("status"),
        "checks": checks,
    }
    cleaned["pre_cleanup_usage_snapshot"] = usage_snapshot
    return cleaned


def _validate_abort_review_deadline(runtime: dict[str, Any], review_packet: dict[str, Any] | None) -> None:
    if not isinstance(review_packet, dict):
        raise DeploymentError("A review-timeout abort requires the Console review packet.")
    if str(review_packet.get("run_id") or "") != str(runtime.get("run_id") or ""):
        raise DeploymentError("Abort cleanup packet does not belong to this PoC run.")
    deadline = str(review_packet.get("review_deadline") or "").strip()
    try:
        deadline_at = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DeploymentError("Abort cleanup packet has no valid review_deadline.") from exc
    if deadline_at.tzinfo is None:
        raise DeploymentError("Abort cleanup packet review_deadline must include a timezone.")
    if datetime.now(timezone.utc) < deadline_at.astimezone(timezone.utc):
        raise DeploymentError("The Console review deadline has not passed; use the normal close path.")


def _pre_cleanup_usage_snapshot(runtime: dict[str, Any]) -> dict[str, Any]:
    """Collect immediate runtime facts before deletion; this is not billing evidence."""

    deployment = runtime.get("deployment") or {}
    stack_name = str(deployment.get("stack_name") or "")
    resource_prefix = str(deployment.get("resource_prefix") or "")
    region = str(deployment.get("target_region") or "")
    profile = str(deployment.get("profile") or DEFAULT_PROFILE)
    captured_at = _now()
    snapshot: dict[str, Any] = {
        "schema_version": "s4.pre-cleanup-usage-snapshot.v1",
        "status": "captured",
        "run_id": runtime.get("run_id"),
        "captured_at": captured_at,
        "source_type": "aws_runtime_facts",
        "billing_evidence": False,
        "actual_cost_status": "not_billing_evidence",
        "rule": (
            "This snapshot records immediately available runtime facts before cleanup. "
            "Current Skill 5 does not report actual AWS cost from runtime facts."
        ),
        "deployment": {
            "recipe": deployment.get("recipe"),
            "stack_name": stack_name,
            "resource_prefix": resource_prefix,
            "target_region": region,
        },
        "timeline": {
            "deployed_at": runtime.get("deployed_at"),
            "captured_at": captured_at,
            "elapsed_seconds": _elapsed_seconds(runtime.get("deployed_at"), captured_at),
        },
        "sections": {},
        "collection_errors": [],
    }
    if not _matches_run_identity(str(runtime.get("run_id") or ""), stack_name, resource_prefix) or not region:
        snapshot["status"] = "unavailable"
        snapshot["collection_errors"].append("runtime_identity_or_region_missing")
        return snapshot

    _add_snapshot_section(snapshot, "cloudformation", lambda: _cloudformation_usage_snapshot(stack_name, profile, region))
    _add_snapshot_section(snapshot, "s3", lambda: _s3_usage_snapshot(stack_name, profile, region))
    _add_snapshot_section(snapshot, "lambda", lambda: _lambda_usage_snapshot(stack_name, runtime, captured_at, profile, region))
    _add_snapshot_section(snapshot, "ec2", lambda: _ec2_usage_snapshot(stack_name, profile, region))
    if snapshot["collection_errors"]:
        snapshot["status"] = "partial" if snapshot["sections"] else "unavailable"
    return snapshot


def _add_snapshot_section(snapshot: dict[str, Any], name: str, collect: Any) -> None:
    try:
        section = collect()
    except DeploymentError as exc:
        snapshot["collection_errors"].append(f"{name}: {str(exc)[:240]}")
        return
    if section is not None:
        snapshot["sections"][name] = section


def _cloudformation_usage_snapshot(stack_name: str, profile: str, region: str) -> dict[str, Any]:
    stacks_payload = _aws_json(["cloudformation", "describe-stacks", "--stack-name", stack_name], profile, region)
    resources_payload = _aws_json(["cloudformation", "describe-stack-resources", "--stack-name", stack_name], profile, region)
    stack = (stacks_payload.get("Stacks") or [{}])[0]
    resources = []
    for item in resources_payload.get("StackResources") or []:
        resources.append(
            {
                "logical_resource_id": item.get("LogicalResourceId"),
                "resource_type": item.get("ResourceType"),
                "resource_status": item.get("ResourceStatus"),
            }
        )
    return {
        "stack_status": stack.get("StackStatus"),
        "creation_time": _json_time(stack.get("CreationTime")),
        "last_updated_time": _json_time(stack.get("LastUpdatedTime")),
        "tags": _tag_list_to_dict(stack.get("Tags") or []),
        "resource_count": len(resources),
        "resources": resources,
    }


def _s3_usage_snapshot(stack_name: str, profile: str, region: str) -> dict[str, Any] | None:
    try:
        bucket_name = _stack_resource_physical_id(stack_name, "DataBucket", profile, region)
    except DeploymentError:
        return None
    usage = _s3_bucket_usage(bucket_name, profile, region)
    return {"bucket_name": bucket_name, "tags": _s3_bucket_tags(bucket_name, profile, region), **usage}


def _s3_bucket_usage(bucket_name: str, profile: str, region: str) -> dict[str, Any]:
    key_marker: str | None = None
    version_marker: str | None = None
    versions = 0
    latest_versions = 0
    delete_markers = 0
    total_size_bytes = 0
    page_count = 0
    while True:
        command = ["s3api", "list-object-versions", "--bucket", bucket_name]
        if key_marker:
            command.extend(["--key-marker", key_marker])
        if version_marker:
            command.extend(["--version-id-marker", version_marker])
        payload = _aws_json(command, profile, region)
        page_count += 1
        for item in payload.get("Versions") or []:
            versions += 1
            total_size_bytes += int(item.get("Size") or 0)
            if item.get("IsLatest") is True:
                latest_versions += 1
        delete_markers += len(payload.get("DeleteMarkers") or [])
        if not payload.get("IsTruncated"):
            break
        key_marker = str(payload.get("NextKeyMarker") or "")
        version_marker = str(payload.get("NextVersionIdMarker") or "")
        if not key_marker:
            raise DeploymentError("S3 version listing was truncated without a continuation marker.")
    return {
        "object_count_current": latest_versions,
        "object_version_count": versions,
        "delete_marker_count": delete_markers,
        "total_size_bytes": total_size_bytes,
        "list_pages": page_count,
    }


def _lambda_usage_snapshot(
    stack_name: str,
    runtime: dict[str, Any],
    captured_at: str,
    profile: str,
    region: str,
) -> dict[str, Any] | None:
    outputs = _stack_outputs(stack_name, profile, region)
    function_name = outputs.get("FunctionName")
    if not function_name:
        return None
    config = _aws_json(["lambda", "get-function-configuration", "--function-name", function_name], profile, region)
    tags = _lambda_tags(config.get("FunctionArn"), profile, region)
    start_time = _metric_start(runtime.get("deployed_at"), captured_at)
    end_time = _parse_time(captured_at) or datetime.now(timezone.utc)
    dimensions = f"Name=FunctionName,Value={function_name}"
    metrics = {
        "Invocations": _metric_sum("AWS/Lambda", "Invocations", dimensions, start_time, end_time, profile, region),
        "Errors": _metric_sum("AWS/Lambda", "Errors", dimensions, start_time, end_time, profile, region),
        "Duration": _metric_average("AWS/Lambda", "Duration", dimensions, start_time, end_time, profile, region),
    }
    return {
        "function_name": function_name,
        "runtime": config.get("Runtime"),
        "code_size_bytes": config.get("CodeSize"),
        "memory_mb": config.get("MemorySize"),
        "timeout_seconds": config.get("Timeout"),
        "last_modified": config.get("LastModified"),
        "tags": tags,
        "cloudwatch_metrics": metrics,
    }


def _ec2_usage_snapshot(stack_name: str, profile: str, region: str) -> dict[str, Any] | None:
    outputs = _stack_outputs(stack_name, profile, region)
    instance_id = outputs.get("TestInstanceId")
    if not instance_id:
        return None
    payload = _aws_json(["ec2", "describe-instances", "--instance-ids", instance_id], profile, region)
    instances = [
        instance
        for reservation in payload.get("Reservations") or []
        for instance in reservation.get("Instances") or []
    ]
    if not instances:
        return {"instance_id": instance_id, "status": "not_found"}
    instance = instances[0]
    return {
        "instance_id": instance_id,
        "state": (instance.get("State") or {}).get("Name"),
        "instance_type": instance.get("InstanceType"),
        "launch_time": _json_time(instance.get("LaunchTime")),
        "tags": _tag_list_to_dict(instance.get("Tags") or []),
    }


def _s3_bucket_tags(bucket_name: str, profile: str, region: str) -> dict[str, Any]:
    try:
        payload = _aws_json(["s3api", "get-bucket-tagging", "--bucket", bucket_name], profile, region)
    except DeploymentError as exc:
        reason = "empty_or_unavailable"
        if "NoSuchTagSet" not in str(exc):
            reason = str(exc)[:160]
        return {"status": "unavailable", "reason": reason, "values": {}}
    return {"status": "captured", "values": _tag_list_to_dict(payload.get("TagSet") or [])}


def _lambda_tags(function_arn: Any, profile: str, region: str) -> dict[str, Any]:
    if not function_arn:
        return {"status": "unavailable", "reason": "function_arn_not_returned", "values": {}}
    try:
        payload = _aws_json(["lambda", "list-tags", "--resource", str(function_arn)], profile, region)
    except DeploymentError as exc:
        return {"status": "unavailable", "reason": str(exc)[:160], "values": {}}
    tags = payload.get("Tags")
    return {"status": "captured", "values": tags if isinstance(tags, dict) else {}}


def _tag_list_to_dict(tags: list[dict[str, Any]]) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in tags:
        key = item.get("Key")
        value = item.get("Value")
        if key is not None and value is not None:
            values[str(key)] = str(value)
    return values


def _metric_sum(
    namespace: str,
    metric_name: str,
    dimensions: str,
    start_time: datetime,
    end_time: datetime,
    profile: str,
    region: str,
) -> dict[str, Any]:
    payload = _metric_statistics(namespace, metric_name, dimensions, start_time, end_time, "Sum", profile, region)
    values = [float(point.get("Sum") or 0) for point in payload.get("Datapoints") or []]
    return {"status": "captured" if values else "no_datapoints_yet", "sum": round(sum(values), 6), "datapoints": len(values)}


def _metric_average(
    namespace: str,
    metric_name: str,
    dimensions: str,
    start_time: datetime,
    end_time: datetime,
    profile: str,
    region: str,
) -> dict[str, Any]:
    payload = _metric_statistics(namespace, metric_name, dimensions, start_time, end_time, "Average", profile, region)
    values = [float(point.get("Average") or 0) for point in payload.get("Datapoints") or []]
    average = round(sum(values) / len(values), 6) if values else None
    return {"status": "captured" if values else "no_datapoints_yet", "average": average, "datapoints": len(values)}


def _metric_statistics(
    namespace: str,
    metric_name: str,
    dimensions: str,
    start_time: datetime,
    end_time: datetime,
    statistic: str,
    profile: str,
    region: str,
) -> dict[str, Any]:
    return _aws_json(
        [
            "cloudwatch",
            "get-metric-statistics",
            "--namespace",
            namespace,
            "--metric-name",
            metric_name,
            "--start-time",
            start_time.isoformat(),
            "--end-time",
            end_time.isoformat(),
            "--period",
            "60",
            "--statistics",
            statistic,
            "--dimensions",
            dimensions,
        ],
        profile,
        region,
    )


def _metric_start(deployed_at: Any, captured_at: str) -> datetime:
    captured = _parse_time(captured_at) or datetime.now(timezone.utc)
    deployed = _parse_time(deployed_at)
    if not deployed:
        return captured - timedelta(hours=1)
    return min(deployed.astimezone(timezone.utc), captured - timedelta(minutes=1))


def _elapsed_seconds(start: Any, end: Any) -> int | None:
    started = _parse_time(start)
    ended = _parse_time(end)
    if not started or not ended:
        return None
    return max(0, int((ended.astimezone(timezone.utc) - started.astimezone(timezone.utc)).total_seconds()))


def _parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _json_time(value: Any) -> str | None:
    parsed = _parse_time(value)
    return parsed.isoformat() if parsed else str(value) if value else None


def _cleanup_stack_resources(runtime: dict[str, Any]) -> dict[str, str]:
    deployment = runtime.get("deployment") or {}
    stack_name = str(deployment.get("stack_name") or "")
    resource_prefix = str(deployment.get("resource_prefix") or "")
    region = str(deployment.get("target_region") or "")
    if not _matches_run_identity(str(runtime.get("run_id") or ""), stack_name, resource_prefix) or not region:
        raise DeploymentError("Cleanup artifact does not match the expected run-derived stack identity.")
    profile = str(deployment.get("profile") or DEFAULT_PROFILE)
    bucket_name = _stack_resource_physical_id(stack_name, "DataBucket", profile, region)
    if not bucket_name.startswith(f"{resource_prefix}-"):
        raise DeploymentError("Refusing cleanup because the stack bucket does not match this run's resource prefix.")
    _empty_versioned_bucket(bucket_name, profile, region)
    _aws(["cloudformation", "delete-stack", "--stack-name", stack_name], profile, region)
    _aws(["cloudformation", "wait", "stack-delete-complete", "--stack-name", stack_name], profile, region)
    return {
        "cloudformation_stack": "deleted",
        "versioned_test_bucket": "emptied_before_stack_delete",
        "run_derived_resource_prefix": "matched",
    }


def _validated_review_evidence(
    runtime: dict[str, Any],
    evidence: dict[str, Any] | None,
    review_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate review metadata and packet binding, not screenshot pixels."""

    if not isinstance(evidence, dict):
        raise DeploymentError("Console review requires screenshot evidence JSON from the review packet.")
    if evidence.get("schema_version") == "s4.resource-inventory.v1":
        return _validated_resource_inventory_evidence(runtime, evidence, review_packet)
    if evidence.get("schema_version") != CONSOLE_REVIEW_EVIDENCE_SCHEMA:
        raise DeploymentError("Console review evidence has an unsupported schema version.")
    if str(evidence.get("run_id") or "") != str(runtime.get("run_id") or ""):
        raise DeploymentError("Console review evidence does not belong to this PoC run.")
    _validate_review_packet_binding(runtime, evidence, review_packet)
    screenshots = evidence.get("screenshots")
    if not isinstance(screenshots, list):
        raise DeploymentError("Console review evidence must include a screenshot list.")
    accepted: list[dict[str, Any]] = []
    seen_views: set[str] = set()
    for item in screenshots:
        if not isinstance(item, dict):
            continue
        view = str(item.get("view") or "").strip()
        screenshot_ref = str(item.get("screenshot_ref") or "").strip()
        sha256 = str(item.get("sha256") or "").strip().lower()
        captured_at = str(item.get("captured_at") or "").strip()
        shared_via = str(item.get("shared_via") or "").strip()
        redacted = item.get("redacted") is True
        hash_scope = str(item.get("hash_scope") or "").strip()
        if not view or not screenshot_ref or not captured_at or shared_via not in {"gui", "conversation"}:
            raise DeploymentError("Each Console screenshot needs view, reference, capture time, and GUI or conversation sharing.")
        if not redacted or hash_scope != "redacted_png":
            raise DeploymentError("Each Console screenshot must be redacted before hashing and sharing.")
        if not re.fullmatch(r"[0-9a-f]{64}", sha256):
            raise DeploymentError("Each Console screenshot needs a SHA-256 hash.")
        accepted.append(
            {
                "view": view,
                "screenshot_ref": screenshot_ref,
                "sha256": sha256,
                "captured_at": captured_at,
                "shared_via": shared_via,
                "redacted": True,
                "hash_scope": "redacted_png",
            }
        )
        seen_views.add(view)
    if REQUIRED_CONSOLE_VIEW not in seen_views:
        raise DeploymentError("Console review evidence must include an Infrastructure Composer screenshot.")
    return {
        "schema_version": CONSOLE_REVIEW_EVIDENCE_SCHEMA,
        "review_target": evidence.get("review_target"),
        "capture_contract": evidence.get("capture_contract"),
        "screenshots": accepted,
        "automated_image_understanding": False,
        "human_confirmation_record_only": True,
    }


def _validate_review_packet_binding(
    runtime: dict[str, Any],
    evidence: dict[str, Any],
    review_packet: dict[str, Any] | None,
) -> None:
    deployment = runtime.get("deployment") or {}
    expected_target = {
        "stack_name": str(deployment.get("stack_name") or ""),
        "target_region": str(deployment.get("target_region") or ""),
        "run_id": str(runtime.get("run_id") or ""),
    }
    evidence_target = evidence.get("review_target") or {}
    for field, expected in expected_target.items():
        if not expected:
            continue
        if str(evidence_target.get(field) or "") != expected:
            raise DeploymentError(f"Console review evidence {field} does not match the runtime.")
    contract = evidence.get("capture_contract") or {}
    if contract.get("hash_scope") != "redacted_png" or contract.get("redacted_before_hash") is not True:
        raise DeploymentError("Console review evidence must record the redact-before-hash capture contract.")
    if contract.get("automated_image_understanding") is not False:
        raise DeploymentError("Console review evidence must not claim automated screenshot-content verification.")
    if not review_packet:
        raise DeploymentError("Console review requires the packet that defined the screenshot checklist.")
    if review_packet.get("schema_version") != "s4.console-review-packet.v1":
        raise DeploymentError("Console review packet has an unsupported schema version.")
    if str(review_packet.get("run_id") or "") != expected_target["run_id"]:
        raise DeploymentError("Console review packet does not belong to this PoC run.")
    packet_target = review_packet.get("review_target") or {}
    for field in ("stack_name", "target_region"):
        if str(packet_target.get(field) or "") != expected_target[field]:
            raise DeploymentError(f"Console review packet {field} does not match the runtime.")
    required_views = {
        str(item.get("view") or "")
        for item in review_packet.get("required_screenshots") or []
        if isinstance(item, dict)
    }
    evidence_views = {
        str(item.get("view") or "")
        for item in evidence.get("screenshots") or []
        if isinstance(item, dict)
    }
    missing_views = sorted(view for view in required_views if view and view not in evidence_views)
    if missing_views:
        detail = ", ".join(missing_views)
        if REQUIRED_CONSOLE_VIEW in missing_views:
            detail += " (Infrastructure Composer)"
        raise DeploymentError(f"Console review evidence is missing required packet views: {detail}.")


def _validated_resource_inventory_evidence(
    runtime: dict[str, Any],
    inventory: dict[str, Any],
    review_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate the structured inventory that replaced image-only review."""

    deployment = runtime.get("deployment") or {}
    expected = {
        "run_id": str(runtime.get("run_id") or ""),
        "stack_name": str(deployment.get("stack_name") or ""),
        "region": str(deployment.get("target_region") or deployment.get("region") or ""),
    }
    for field, expected_value in expected.items():
        if expected_value and str(inventory.get(field) or "") != expected_value:
            raise DeploymentError(f"Resource inventory {field} does not match the runtime.")
    sha256 = str(inventory.get("inventory_sha256") or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", sha256):
        raise DeploymentError("Resource inventory needs a SHA-256 hash.")
    if not isinstance(inventory.get("resources"), list) or not inventory["resources"]:
        raise DeploymentError("Resource inventory must include deployed resources.")
    reconciliation = inventory.get("quote_reconciliation") or {}
    if reconciliation.get("status") == "quote_incomplete" or reconciliation.get("deployed_not_quoted"):
        raise DeploymentError("Resource inventory shows deployed resources missing from the Skill 3 quote.")
    if review_packet and str(review_packet.get("run_id") or "") != expected["run_id"]:
        raise DeploymentError("Review packet does not belong to this PoC run.")
    return {
        "schema_version": "s4.resource-inventory-review.v1",
        "review_target": {
            "run_id": expected["run_id"],
            "stack_name": expected["stack_name"],
            "target_region": expected["region"],
        },
        "inventory_sha256": sha256,
        "resource_count": inventory.get("resource_count"),
        "quote_reconciliation": reconciliation,
        "permission_surface": inventory.get("permission_surface"),
        "screenshots": [
            {
                "view": "resource_inventory",
                "screenshot_ref": "structured_inventory_json",
                "sha256": sha256,
                "captured_at": inventory.get("captured_at"),
                "shared_via": "conversation",
                "redacted": True,
                "hash_scope": "inventory_json",
            }
        ],
        "automated_image_understanding": False,
        "human_confirmation_record_only": True,
    }


def _context_errors(
    evaluate: dict[str, Any], approval: dict[str, Any], validation: dict[str, Any], selected: dict[str, Any] | None
) -> list[str]:
    errors: list[str] = []
    if evaluate.get("stage") != "S3" or evaluate.get("status") not in {"awaiting_poc_decision", "evaluated"}:
        errors.append("s3_not_usable")
    if approval.get("schema_version") not in {None, "", DEPLOYMENT_APPROVAL_SCHEMA}:
        errors.append("approval_schema_unsupported")
    if approval.get("run_id") and str(approval.get("run_id")) != str(evaluate.get("run_id") or ""):
        errors.append("approval_run_id_mismatch")
    if not selected:
        errors.append("selected_candidate_id_not_in_s3")
        return errors
    validation_candidate = _selected_validation(validation, str(selected.get("candidate_id")))
    if not _poc_gate_passes(validation_candidate):
        errors.append("poc_gate_not_passed")
    if approval.get("deployment_authorized") is not True:
        errors.append("deployment_authorized_not_true")
    deployment = approval.get("deployment") or {}
    if deployment.get("target_region") not in {None, "", DEFAULT_REGION}:
        errors.append("deployment_target_region_invalid")
    region = deployment.get("target_region") or DEFAULT_REGION
    region_status = (selected.get("region_status") or {}).get("status")
    if region_status != f"available_{str(region).replace('-', '_')}" and not (
        region_status == "region_unknown" and approval.get("region_warning_acknowledged") is True
    ):
        errors.append("target_region_not_verified_or_acknowledged")
    quote_recipe = (((selected.get("cost_estimate") or {}).get("quote") or {}).get("recipe"))
    recipe = _recipe_for(selected)
    if quote_recipe and recipe and quote_recipe != recipe.key:
        errors.append("cost_model_and_deployment_recipe_mismatch")
    return errors


def _poc_gate_passes(validation_candidate: dict[str, Any]) -> bool:
    """Require the simplified manual PoC gate without custom environment forms."""

    return validation_candidate.get("validation_status") in {
        "poc_ready_for_manual_start",
        "paid_poc_ready_for_manual_start",
    }


def _verify_lineage(
    evaluate: dict[str, Any], request: dict[str, Any], selected_id: str
) -> tuple[dict[str, Any], list[str]]:
    paths = {stage: Path(str(request.get(f"{stage.lower()}_artifact_path") or "")) for stage in ("S1", "S2", "S3")}
    errors: list[str] = []
    records: list[dict[str, str]] = []
    payloads: dict[str, dict[str, Any]] = {}
    for stage, path in paths.items():
        if not str(path):
            errors.append(f"{stage.lower()}_artifact_path_missing")
            continue
        if not path.is_file():
            errors.append(f"{stage.lower()}_artifact_path_not_found")
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            errors.append(f"{stage.lower()}_artifact_invalid_json")
            continue
        if payload.get("stage") != stage:
            errors.append(f"{stage.lower()}_artifact_stage_mismatch")
        payloads[stage] = payload
        records.append({"stage": stage, "path": str(path.resolve()), "sha256": _sha256(path)})
    run_ids = {str(payload.get("run_id") or "") for payload in payloads.values()}
    if len(run_ids) != 1 or str(evaluate.get("run_id") or "") not in run_ids:
        errors.append("lineage_run_id_mismatch")
    if payloads.get("S3") and payloads["S3"] != evaluate:
        errors.append("s3_input_does_not_match_lineage_artifact")
    if selected_id:
        if not any(item.get("candidate_id") == selected_id for item in payloads.get("S1", {}).get("candidates") or []):
            errors.append("selected_candidate_missing_from_s1")
        if not any(item.get("candidate_id") == selected_id for item in payloads.get("S2", {}).get("candidates") or []):
            errors.append("selected_candidate_missing_from_s2")
        if not any(item.get("candidate_id") == selected_id for item in payloads.get("S3", {}).get("evaluated_candidates") or []):
            errors.append("selected_candidate_missing_from_s3")
    return {"source_artifacts": records}, errors


def _candidate_summary(candidate: dict[str, Any] | None) -> dict[str, Any] | None:
    if not candidate:
        return None
    return {
        "candidate_id": candidate.get("candidate_id"),
        "title": candidate.get("title"),
        "source_url": candidate.get("source_url"),
        "weighted_score": candidate.get("weighted_score"),
        "region_status": (candidate.get("region_status") or {}).get("status"),
    }


def _select_approval_candidate(
    candidates: list[dict[str, Any]], selected_candidate_id: str | None
) -> dict[str, Any]:
    if selected_candidate_id:
        selected = next(
            (item for item in candidates if str(item.get("candidate_id") or "") == str(selected_candidate_id)),
            None,
        )
        if not selected:
            raise DeploymentError("Selected candidate ID is not present in the Skill 3 artifact.")
        return selected
    recommended = [item for item in candidates if _candidate_recommends_poc(item)]
    if len(recommended) == 1:
        return recommended[0]
    if len(candidates) == 1:
        return candidates[0]
    raise DeploymentError("Approval template needs exactly one selected candidate ID.")


def _candidate_recommends_poc(candidate: dict[str, Any]) -> bool:
    if "recommend_poc" in candidate:
        return bool(candidate.get("recommend_poc"))
    if "eligible_for_poc_review" in candidate:
        return bool(candidate.get("eligible_for_poc_review"))
    if "eligible_for_paid_poc_review" in candidate:
        return bool(candidate.get("eligible_for_paid_poc_review"))
    return bool(candidate.get("recommend_s4"))


def _minimum_numeric(*values: Any) -> float | None:
    numeric = [float(value) for value in values if isinstance(value, (int, float))]
    return min(numeric) if numeric else None


def _selected_validation(validation: dict[str, Any], selected_id: str) -> dict[str, Any]:
    return next(
        (item for item in validation.get("validated_candidates") or [] if item.get("candidate_id") == selected_id),
        {},
    )


def _recipe_for(candidate: dict[str, Any] | None) -> PocRecipe | None:
    """Resolve through the registry so S3 and S4 never disagree.

    A draft or unmatched candidate returns ``None``, which the caller reports as
    ``needs_poc_recipe``. Nothing here falls back to a nearby recipe.
    """

    decision = select_recipe(candidate)
    if not decision.get("deployable_recipe_registered"):
        return None
    return _recipe_by_key(str(decision.get("recipe_id") or ""))


def _recipe_by_key(key: str) -> PocRecipe | None:
    definition = get_recipe(key)
    if definition is None or not definition.is_deployable() or definition.poc_directory is None:
        return None
    return PocRecipe(
        key=definition.recipe_id,
        poc_directory=definition.poc_directory,
        success_criteria=tuple(definition.success_criteria),
    )


def run_deployment_preflight(
    candidate: dict[str, Any] | None,
    approval: dict[str, Any] | None,
    region_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Public entry point for the eight pre-deployment checks.

    Skill 4 must call this and refuse to continue unless the status is
    ``ready_for_deployment``. Keeping it here rather than inline means the same
    checks run whether the caller is the CLI, a test, or another surface.
    """

    decision = select_recipe(candidate)
    result = deployment_preflight(decision, approval, region_state)
    result["recipe_decision"] = decision
    return result


def _require_deployable_context(context: dict[str, Any]) -> None:
    if context.get("status") != "ready_for_manual_deployment":
        raise DeploymentError("S4 deployment context is not ready for manual deployment.")
    authorization = context.get("authorization") or {}
    if authorization.get("deployment_authorized") is not True or authorization.get("automatic_poc_start") is not False:
        raise DeploymentError("Deployment requires explicit human authorization and automatic_poc_start=false.")


def _synthesize(recipe: PocRecipe, deployment: dict[str, Any], work_dir: Path) -> Path:
    output_dir = work_dir / "cdk.out"
    command = [
        _npx_command(),
        "cdk",
        "synth",
        str(deployment["stack_name"]),
        "--context",
        f"stackName={deployment['stack_name']}",
        "--context",
        f"namePrefix={deployment['resource_prefix']}",
        "--context",
        f"createTestInstance={str(deployment['create_test_instance']).lower()}",
        "--output",
        str(output_dir),
    ]
    _run(command, recipe.poc_directory)
    template = output_dir / f"{deployment['stack_name']}.template.json"
    if not template.is_file():
        raise DeploymentError("CDK synth completed without the expected CloudFormation template.")
    return template


def _verify_recipe(recipe: PocRecipe, context: dict[str, Any], outputs: dict[str, str], work_dir: Path) -> dict[str, Any]:
    if recipe.key == LAMBDA_SELF_MANAGED_STORAGE_RECIPE.key:
        return _verify_lambda_self_managed_storage(context, outputs, work_dir)
    if recipe.key != S3_FILES_RECIPE.key:
        raise DeploymentError("No verification handler is registered for this recipe.")
    required = ("BucketName", "TestInstanceId")
    if any(name not in outputs for name in required):
        raise DeploymentError("S3 Files stack outputs are incomplete; verification cannot proceed.")
    deployment = context["deployment"]
    profile = str(deployment["profile"])
    region = str(deployment["target_region"])
    marker = f"S4 source-to-mount verification for run {context['run_id']}"
    source_file = work_dir / "from-s3.txt"
    source_file.write_text(marker + "\n", encoding="utf-8")
    _aws(["s3api", "put-object", "--bucket", outputs["BucketName"], "--key", "poc/from-s3.txt", "--body", str(source_file)], profile, region)
    _wait_for_ssm(outputs["TestInstanceId"], profile, region)
    command_id = _send_s3_files_verification(outputs["TestInstanceId"], context["run_id"], work_dir, profile, region)
    invocation = _wait_for_command(command_id, outputs["TestInstanceId"], profile, region)
    if invocation.get("Status") != "Success":
        raise DeploymentError("SSM validation command did not succeed.")
    round_trip_file = work_dir / "from-mount.txt"
    _get_s3_object_with_retry(
        outputs["BucketName"], "poc/from-mount.txt", round_trip_file, profile, region
    )
    expected = f"S4 mount-to-S3 verification for run {context['run_id']}"
    if expected not in round_trip_file.read_text(encoding="utf-8"):
        raise DeploymentError("S3 read-back did not contain the mount-to-S3 verification marker.")
    return {
        "recipe": recipe.key,
        "source_to_mount": "verified",
        "mount_to_s3": "verified",
        "ssm_status": "Success",
        "success_criteria": list(context.get("success_criteria") or []),
    }


def _verify_lambda_self_managed_storage(
    context: dict[str, Any], outputs: dict[str, str], work_dir: Path
) -> dict[str, Any]:
    required = ("FunctionName", "CodeObjectVersion", "CodeStorageMode")
    if any(name not in outputs for name in required):
        raise DeploymentError("Lambda self-managed storage stack outputs are incomplete; verification cannot proceed.")
    if outputs["CodeStorageMode"] != "REFERENCE" or not outputs["CodeObjectVersion"]:
        raise DeploymentError("CloudFormation did not preserve the expected Lambda REFERENCE storage configuration.")
    deployment = context["deployment"]
    payload = json.dumps({"run_id": context["run_id"]})
    response_file = work_dir / "lambda-invoke-response.json"
    response = _aws_json(
        [
            "lambda",
            "invoke",
            "--function-name",
            outputs["FunctionName"],
            "--cli-binary-format",
            "raw-in-base64-out",
            "--payload",
            payload,
            str(response_file),
        ],
        str(deployment["profile"]),
        str(deployment["target_region"]),
    )
    if response.get("FunctionError") or int(response.get("StatusCode") or 0) != 200:
        raise DeploymentError("Lambda invocation did not succeed.")
    try:
        invoked = json.loads(response_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DeploymentError("Lambda invocation did not return valid JSON.") from exc
    if invoked.get("storage_mode") != "REFERENCE" or invoked.get("run_id") != context["run_id"]:
        raise DeploymentError("Lambda invocation response did not match the self-managed storage test contract.")
    return {
        "recipe": LAMBDA_SELF_MANAGED_STORAGE_RECIPE.key,
        "cloudformation_reference_mode": "verified",
        "lambda_invoke": "verified",
        "success_criteria": list(context.get("success_criteria") or []),
    }


def _wait_for_ssm(instance_id: str, profile: str, region: str) -> None:
    for _ in range(30):
        info = _aws_json(["ssm", "describe-instance-information", "--filters", f"Key=InstanceIds,Values={instance_id}"], profile, region)
        instances = info.get("InstanceInformationList") or []
        if instances and instances[0].get("PingStatus") == "Online":
            return
        time.sleep(20)
    raise DeploymentError("EC2 test client did not become SSM Online before the validation timeout.")


def _send_s3_files_verification(instance_id: str, run_id: str, work_dir: Path, profile: str, region: str) -> str:
    script = "\n".join(
        [
            "set -euo pipefail",
            "for i in $(seq 1 30); do findmnt -T /mnt/s3files && break; sleep 20; done",
            "findmnt -T /mnt/s3files",
            "test -f /mnt/s3files/from-s3.txt",
            "cat /mnt/s3files/from-s3.txt",
            f"printf '%s\\n' 'S4 mount-to-S3 verification for run {run_id}' > /mnt/s3files/from-mount.txt",
            "sync",
        ]
    )
    request_file = work_dir / "ssm-command.json"
    request_file.write_text(
        json.dumps(
            {"DocumentName": "AWS-RunShellScript", "InstanceIds": [instance_id], "Parameters": {"commands": [script]}},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    response = _aws_json(["ssm", "send-command", "--cli-input-json", f"file://{request_file}"], profile, region)
    command_id = str(((response.get("Command") or {}).get("CommandId")) or "")
    if not command_id:
        raise DeploymentError("SSM did not return a command ID.")
    return command_id


def _wait_for_command(command_id: str, instance_id: str, profile: str, region: str) -> dict[str, Any]:
    pending = {"Pending", "InProgress", "Delayed"}
    for _ in range(45):
        try:
            invocation = _aws_json(
                ["ssm", "get-command-invocation", "--command-id", command_id, "--instance-id", instance_id], profile, region
            )
        except DeploymentError:
            time.sleep(10)
            continue
        if invocation.get("Status") not in pending:
            return invocation
        time.sleep(10)
    raise DeploymentError("SSM validation command timed out.")


def _stack_outputs(stack_name: str, profile: str, region: str) -> dict[str, str]:
    payload = _aws_json(["cloudformation", "describe-stacks", "--stack-name", stack_name], profile, region)
    stacks = payload.get("Stacks") or []
    if not stacks:
        raise DeploymentError("CloudFormation did not return stack outputs.")
    return {str(item.get("OutputKey")): str(item.get("OutputValue")) for item in stacks[0].get("Outputs") or []}


def _stack_status_or_none(stack_name: str, profile: str, region: str) -> str | None:
    try:
        payload = _aws_json(["cloudformation", "describe-stacks", "--stack-name", stack_name], profile, region)
    except DeploymentError as exc:
        if "does not exist" in str(exc):
            return None
        raise
    stacks = payload.get("Stacks") or []
    return str(stacks[0].get("StackStatus") or "") if stacks else None


def _get_s3_object_with_retry(
    bucket_name: str,
    key: str,
    output_path: Path,
    profile: str,
    region: str,
    attempts: int = 30,
    interval_seconds: int = 20,
) -> None:
    for attempt in range(attempts):
        try:
            _aws(["s3api", "get-object", "--bucket", bucket_name, "--key", key, str(output_path)], profile, region)
            return
        except DeploymentError as exc:
            if "NoSuchKey" not in str(exc) or attempt == attempts - 1:
                raise
            time.sleep(interval_seconds)
    raise DeploymentError("S3 Files did not export the mount-written object before the validation timeout.")


def _stack_resource_physical_id(stack_name: str, logical_id: str, profile: str, region: str) -> str:
    payload = _aws_json(
        ["cloudformation", "describe-stack-resource", "--stack-name", stack_name, "--logical-resource-id", logical_id], profile, region
    )
    physical_id = str(((payload.get("StackResourceDetail") or {}).get("PhysicalResourceId")) or "")
    if not physical_id:
        raise DeploymentError(f"CloudFormation did not return physical ID for {logical_id}.")
    return physical_id


def _empty_versioned_bucket(bucket_name: str, profile: str, region: str) -> None:
    key_marker: str | None = None
    version_marker: str | None = None
    page = 0
    while True:
        command = ["s3api", "list-object-versions", "--bucket", bucket_name]
        if key_marker:
            command.extend(["--key-marker", key_marker])
        if version_marker:
            command.extend(["--version-id-marker", version_marker])
        payload = _aws_json(command, profile, region)
        objects = [
            {"Key": item["Key"], "VersionId": item["VersionId"]}
            for group in ("Versions", "DeleteMarkers")
            for item in payload.get(group) or []
        ]
        for start in range(0, len(objects), 1000):
            request_path = RADAR_ROOT / "out" / ".s4-runtime" / (
                f"delete-{hashlib.sha256(bucket_name.encode()).hexdigest()[:12]}-{page}-{start}.json"
            )
            request_path.parent.mkdir(parents=True, exist_ok=True)
            request_path.write_text(json.dumps({"Objects": objects[start : start + 1000], "Quiet": True}), encoding="utf-8")
            _aws(["s3api", "delete-objects", "--bucket", bucket_name, "--delete", f"file://{request_path}"], profile, region)
        if not payload.get("IsTruncated"):
            return
        key_marker = str(payload.get("NextKeyMarker") or "")
        version_marker = str(payload.get("NextVersionIdMarker") or "")
        if not key_marker:
            raise DeploymentError("S3 version listing was truncated without a continuation marker.")
        page += 1


def _aws(arguments: list[str], profile: str, region: str) -> str:
    return _run(["aws", *arguments, "--profile", profile, "--region", region], PROJECT_ROOT)


def _aws_json(arguments: list[str], profile: str, region: str) -> dict[str, Any]:
    output = _aws([*arguments, "--output", "json"], profile, region)
    try:
        return json.loads(output or "{}")
    except json.JSONDecodeError as exc:
        raise DeploymentError("AWS CLI did not return valid JSON.") from exc


def _run(command: list[str], cwd: Path) -> str:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DeploymentError(f"Command could not be completed: {command[0]}") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "command failed").strip().splitlines()[-1][:500]
        raise DeploymentError(f"Command failed ({command[0]}): {detail}")
    return completed.stdout


def _npx_command() -> str:
    return "npx.cmd" if platform.system() == "Windows" else "npx"


def _work_dir(context: dict[str, Any]) -> Path:
    run_id = str(context.get("run_id") or "unknown").replace("/", "-").replace("\\", "-")
    return RADAR_ROOT / "out" / "s4-runtime" / run_id


def _matches_run_identity(run_id: str, stack_name: str, resource_prefix: str) -> bool:
    suffix = hashlib.sha256(run_id.encode("utf-8")).hexdigest()[:8]
    return stack_name == f"AgenticRadarS4{suffix.upper()}" and resource_prefix == f"agentic-radar-s4-{suffix}"


def _composer_url(region: str) -> str:
    region = region or DEFAULT_REGION
    return f"https://{region}.console.aws.amazon.com/composer/home?region={region}"


def _cloudformation_stack_url(region: str, stack_name: str) -> str:
    region = region or DEFAULT_REGION
    safe_stack = stack_name.replace("/", "%2F").replace(":", "%3A")
    return (
        f"https://{region}.console.aws.amazon.com/cloudformation/home?region={region}"
        f"#/stacks/stackinfo?stackId={safe_stack}"
    )


def _safe_path_segment(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value or "unknown-run").strip("-") or "unknown-run"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
