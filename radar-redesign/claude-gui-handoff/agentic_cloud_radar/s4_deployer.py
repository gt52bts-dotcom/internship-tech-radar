"""S4 controlled PoC deployment runner.

The validator in :mod:`s4` decides whether a paid PoC may be reviewed. This
module owns the later, explicit actions: prove S1/S2/S3 lineage, select a
candidate-specific recipe, synthesize CDK, deploy through CloudFormation,
run the recipe verification, wait for Console review, and clean up.

No function in this module is called by normal ``s4``. Resource creation
requires both ``deployment_authorized=true`` in a human approval artifact and
an explicit CLI ``--execute`` flag.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time
from typing import Any

from .s4 import build_validate


RADAR_ROOT = Path(__file__).resolve().parents[1]
# The main workspace keeps ``poc/`` beside ``radar-redesign/``.  The portable
# Claude handoff keeps it inside the handoff root.  Resolve either layout
# without changing the recorded deployment recipe contract.
PROJECT_ROOT = RADAR_ROOT if (RADAR_ROOT / "poc").is_dir() else RADAR_ROOT.parent
DEFAULT_PROFILE = "intern"
DEFAULT_REGION = "ap-southeast-1"
COMMAND_TIMEOUT_SECONDS = 900


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


S3_FILES_RECIPE = PocRecipe(
    key="s3_files_cdk",
    poc_directory=PROJECT_ROOT / "poc" / "s3-files-cdk-poc",
    success_criteria=(
        "CloudFormation stack reaches CREATE_COMPLETE.",
        "EC2 test client mounts S3 Files.",
        "An object placed in S3 is readable from the mount.",
        "A file written through the mount is readable from S3.",
    ),
)

LAMBDA_SELF_MANAGED_STORAGE_RECIPE = PocRecipe(
    key="lambda_self_managed_s3_code_storage_cdk",
    poc_directory=PROJECT_ROOT / "poc" / "lambda-self-managed-storage-cdk-poc",
    success_criteria=(
        "CloudFormation stack reaches CREATE_COMPLETE.",
        "The Lambda function is created with S3ObjectStorageMode=REFERENCE.",
        "The function can be invoked from the non-production test account.",
    ),
)


def build_deployment_context(evaluate: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
    """Create an auditable, non-deploying context from a human-approved S3 run."""

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

    run_id = str(evaluate.get("run_id") or "unknown-run")
    suffix = hashlib.sha256(run_id.encode("utf-8")).hexdigest()[:8]
    deployment = approval.get("deployment") or {}
    context = {
        "schema_version": "s4.deployment-context.v2",
        "stage": "S4",
        "created_at": _now(),
        "run_id": run_id,
        "status": "ready_for_manual_deployment" if not errors else "not_deployable",
        "lineage": lineage,
        "selected_candidate": _candidate_summary(selected),
        "s4_validation": _selected_validation(validation, selected_id),
        "authorization": {
            "approved_by": approval.get("approved_by"),
            "deployment_authorized": approval.get("deployment_authorized") is True,
            "region_warning_acknowledged": approval.get("region_warning_acknowledged") is True,
            "automatic_poc_start": False,
            "approval_basis": approval.get("approval_basis"),
        },
        "deployment": {
            "recipe": recipe.key if recipe else None,
            "stack_name": f"AgenticRadarS4{suffix.upper()}",
            "resource_prefix": f"agentic-radar-s4-{suffix}",
            "profile": deployment.get("profile"),
            "target_region": deployment.get("target_region"),
            "create_test_instance": bool(deployment.get("create_test_instance", True)),
        },
        "success_criteria": list(approval.get("success_criteria") or (recipe.success_criteria if recipe else [])),
        "cleanup_scope": list(approval.get("cleanup_scope") or []),
        "errors": _dedupe(errors),
    }
    return context


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
    outputs = _stack_outputs(stack_name, profile, region)
    verification = _verify_recipe(recipe, context, outputs, work_dir)

    return {
        "schema_version": "s4.runtime-evidence.v2",
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
            "required_checks": [
                "CloudFormation stack Resources and Template",
                "Recipe resources and their expected relationships",
                "Test workload result",
            ],
        },
        "cleanup": {"status": "pending_console_review"},
    }


def record_console_review(runtime: dict[str, Any], confirmed_by: str, notes: str | None = None) -> dict[str, Any]:
    """Record the human Console check before cleanup is permitted."""

    reviewer = str(confirmed_by or "").strip()
    if runtime.get("stage") != "S4" or runtime.get("status") != "awaiting_console_review":
        raise DeploymentError("Console review requires an S4 runtime artifact awaiting review.")
    if not reviewer:
        raise DeploymentError("Console review requires a named human reviewer.")
    reviewed = dict(runtime)
    reviewed["status"] = "ready_for_cleanup"
    reviewed["console_review"] = {
        **dict(runtime.get("console_review") or {}),
        "status": "confirmed",
        "confirmed_by": reviewer,
        "confirmed_at": _now(),
        "notes": str(notes or "").strip() or None,
    }
    reviewed["cleanup"] = {"status": "ready_for_manual_cleanup"}
    return reviewed


def execute_cleanup(runtime: dict[str, Any]) -> dict[str, Any]:
    """Remove only this stack's test data and resources after Console review."""

    if runtime.get("stage") != "S4" or runtime.get("status") != "ready_for_cleanup":
        raise DeploymentError("Cleanup requires a Console-reviewed S4 runtime artifact.")
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

    cleaned = dict(runtime)
    cleaned["status"] = "cleanup_verified"
    cleaned["cleanup"] = {
        "status": "verified",
        "verified_at": _now(),
        "checks": {
            "cloudformation_stack": "deleted",
            "versioned_test_bucket": "emptied_before_stack_delete",
            "run_derived_resource_prefix": "matched",
        },
    }
    return cleaned


def _context_errors(
    evaluate: dict[str, Any], approval: dict[str, Any], validation: dict[str, Any], selected: dict[str, Any] | None
) -> list[str]:
    errors: list[str] = []
    if evaluate.get("stage") != "S3" or evaluate.get("status") != "evaluated":
        errors.append("s3_not_usable")
    if not selected:
        errors.append("selected_candidate_id_not_in_s3")
        return errors
    if approval.get("validation_type") != "paid_poc":
        errors.append("paid_poc_validation_type_required")
    if approval.get("automatic_poc_start") is not False:
        errors.append("automatic_poc_start_must_be_explicitly_false")
    validation_candidate = _selected_validation(validation, str(selected.get("candidate_id")))
    if not _paid_poc_gate_passes(validation_candidate, selected, approval):
        errors.append("paid_poc_gate_not_passed")
    if approval.get("deployment_authorized") is not True:
        errors.append("deployment_authorized_not_true")
    deployment = approval.get("deployment") or {}
    if not str(deployment.get("profile") or "").strip():
        errors.append("deployment_profile_missing")
    if deployment.get("target_region") != DEFAULT_REGION:
        errors.append("deployment_target_region_invalid")
    if not approval.get("success_criteria"):
        errors.append("success_criteria_missing")
    if not approval.get("cleanup_scope"):
        errors.append("cleanup_scope_missing")
    return errors


def _paid_poc_gate_passes(validation_candidate: dict[str, Any], selected: dict[str, Any], approval: dict[str, Any]) -> bool:
    """Allow an explicitly acknowledged Region warning without weakening other gates.

    The radar treats missing Region evidence as a warning in S2/S3. For a real
    S4 PoC, Cleo may consciously accept that warning after seeing the S3 result.
    This is recorded in approval and evidence; every other paid-PoC check still
    has to pass.
    """

    if approval.get("validation_type") != "paid_poc" or approval.get("automatic_poc_start") is not False:
        return False
    if validation_candidate.get("validation_status") == "paid_poc_ready_for_manual_start":
        return True
    region = selected.get("region_status") or {}
    if region.get("status") != "region_unknown" or approval.get("region_warning_acknowledged") is not True:
        return False
    checks = validation_candidate.get("paid_poc_checks") or []
    return all(check.get("passed") or check.get("name") == "region_status_available" for check in checks)


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
        "confidence": candidate.get("confidence"),
        "region_status": (candidate.get("region_status") or {}).get("status"),
    }


def _selected_validation(validation: dict[str, Any], selected_id: str) -> dict[str, Any]:
    return next(
        (item for item in validation.get("validated_candidates") or [] if item.get("candidate_id") == selected_id),
        {},
    )


def _recipe_for(candidate: dict[str, Any] | None) -> PocRecipe | None:
    title = str((candidate or {}).get("title") or "").lower()
    source_url = str((candidate or {}).get("source_url") or "").lower()
    if "s3 files" in title:
        return S3_FILES_RECIPE
    if "lambda-self-managed-code-storage" in source_url or ("lambda" in title and "storage" in source_url):
        return LAMBDA_SELF_MANAGED_STORAGE_RECIPE
    return None


def _recipe_by_key(key: str) -> PocRecipe | None:
    recipes = (S3_FILES_RECIPE, LAMBDA_SELF_MANAGED_STORAGE_RECIPE)
    return next((recipe for recipe in recipes if recipe.key == key), None)


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
    _aws(["s3api", "get-object", "--bucket", outputs["BucketName"], "--key", "poc/from-mount.txt", str(round_trip_file)], profile, region)
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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
