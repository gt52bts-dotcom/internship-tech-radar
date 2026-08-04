"""Skill 4 recipe registry.

The registry is the single place that answers "may this candidate create AWS
resources?". Skill 3 asks it to explain why a candidate cannot proceed; Skill 4
asks it for the definition it is allowed to deploy. Both read the same table, so
a candidate can never be deployable in one stage and unknown in the other.

Selection is deliberately conservative. When nothing matches, the answer is
``needs_new_recipe`` and the next step is to write a recipe — not to fall back on
the generic cost model, and not to assemble something that looks close enough.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import RecipeDefinition

PROJECT_ROOT = Path(__file__).resolve().parents[3]


S3_FILES = RecipeDefinition(
    recipe_id="s3_files_cdk",
    display_name="S3 Files with EC2 mount",
    display_name_zh="S3 Files 掛載於 EC2 的雙向讀寫驗證",
    supported_candidate_patterns=("s3 files", "mountpoint for amazon s3"),
    required_aws_services=("S3", "EC2", "CloudFormation", "IAM"),
    required_region_capabilities=("s3_files_available", "ec2_t3_micro_available"),
    estimated_cost_model_id="s3_files",
    deployable_resource_types=(
        "AWS::S3::Bucket",
        "AWS::EC2::Instance",
        "AWS::EC2::SecurityGroup",
        "AWS::IAM::Role",
        "AWS::IAM::InstanceProfile",
    ),
    required_iam_actions=(
        "cloudformation:CreateStack",
        "cloudformation:DescribeStackResources",
        "cloudformation:DeleteStack",
        "s3:CreateBucket",
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteBucket",
        "ec2:RunInstances",
        "ec2:TerminateInstances",
        "iam:PassRole",
    ),
    approval_required_fields=("selected_candidate_id", "approved_by", "approved_cost_ceiling_usd"),
    deployment_inputs_schema={
        "region": {"type": "string", "required": True},
        "stack_name": {"type": "string", "required": True, "note": "必須由 run_id 推導"},
        "instance_type": {"type": "string", "default": "t3.micro"},
        "ebs_gb": {"type": "number", "default": 8},
    },
    success_criteria=(
        "CloudFormation 堆疊達到 CREATE_COMPLETE。",
        "EC2 測試主機成功掛載 S3 Files。",
        "放入 S3 的物件可從掛載點讀取。",
        "透過掛載點寫入的檔案可從 S3 讀取。",
    ),
    evidence_to_collect=(
        "CloudFormation 資源盤點（describe-stack-resources）",
        "雙向讀寫的驗證輸出（不含帳號識別資訊）",
        "實際觸發的 IAM action 清單",
        "各階段耗時",
    ),
    cleanup_strategy="以 run 推導的堆疊為範圍執行 CloudFormation delete-stack，先清空測試 bucket 物件。",
    cleanup_verification=(
        "堆疊狀態為 DELETE_COMPLETE 或查無此堆疊。",
        "測試 bucket 已不存在。",
        "EC2 執行個體已終止。",
    ),
    risk_level="medium",
    stop_conditions=(
        "堆疊建立失敗且無法自動回復。",
        "掛載驗證在逾時內未通過。",
        "報價高用量估算超過核准上限。",
        "目標區域無 S3 Files 能力且無可接受的替代區域。",
    ),
    unsupported_conditions=(
        "需要正式環境資料。",
        "需要跨帳號或跨組織權限。",
        "需要 VPC 對外連線以外的私有網路設定。",
    ),
    poc_directory=PROJECT_ROOT / "poc" / "s3-files-cdk-poc",
)


LAMBDA_SELF_MANAGED_STORAGE = RecipeDefinition(
    recipe_id="lambda_self_managed_s3_code_storage_cdk",
    display_name="Lambda self-managed S3 code storage",
    display_name_zh="Lambda 自主管理 S3 程式碼儲存的參照模式驗證",
    supported_candidate_patterns=(
        "lambda-self-managed-code-storage",
        "self-managed code storage",
        "自主管理程式碼儲存",
    ),
    required_aws_services=("Lambda", "S3", "CloudFormation", "IAM", "CloudWatch"),
    required_region_capabilities=("lambda_reference_mode_available",),
    estimated_cost_model_id="lambda_self_managed",
    deployable_resource_types=(
        "AWS::S3::Bucket",
        "AWS::Lambda::Function",
        "AWS::IAM::Role",
        "AWS::Logs::LogGroup",
    ),
    required_iam_actions=(
        "cloudformation:CreateStack",
        "cloudformation:DescribeStackResources",
        "cloudformation:DeleteStack",
        "s3:CreateBucket",
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteBucket",
        "lambda:CreateFunction",
        "lambda:InvokeFunction",
        "lambda:DeleteFunction",
        "logs:CreateLogGroup",
        "iam:PassRole",
    ),
    approval_required_fields=("selected_candidate_id", "approved_by", "approved_cost_ceiling_usd"),
    deployment_inputs_schema={
        "region": {"type": "string", "required": True},
        "stack_name": {"type": "string", "required": True, "note": "必須由 run_id 推導"},
        "artifact_key": {"type": "string", "required": True},
        "memory_mb": {"type": "number", "default": 512},
    },
    success_criteria=(
        "CloudFormation 堆疊達到 CREATE_COMPLETE。",
        "Lambda 函數以 S3ObjectStorageMode=REFERENCE 建立。",
        "可從沙箱測試帳號成功叫用該函數。",
    ),
    evidence_to_collect=(
        "CloudFormation 資源盤點（describe-stack-resources）",
        "叫用結果與回傳狀態（不含帳號識別資訊）",
        "實際觸發的 IAM action 清單",
        "各階段耗時",
    ),
    cleanup_strategy="以 run 推導的堆疊為範圍執行 CloudFormation delete-stack，先移除版本化的 artifact 物件。",
    cleanup_verification=(
        "堆疊狀態為 DELETE_COMPLETE 或查無此堆疊。",
        "Lambda 函數已不存在。",
        "artifact bucket 已不存在。",
    ),
    risk_level="low",
    stop_conditions=(
        "堆疊建立失敗且無法自動回復。",
        "REFERENCE 模式在該區域不被接受。",
        "報價高用量估算超過核准上限。",
        "叫用驗證在逾時內未通過。",
    ),
    unsupported_conditions=(
        "需要正式環境的程式碼或資料。",
        "需要跨帳號 bucket 參照。",
    ),
    poc_directory=PROJECT_ROOT / "poc" / "lambda-self-managed-storage-cdk-poc",
)


WORKSPACES_AI_AGENT_ACCESS_DRAFT = RecipeDefinition(
    recipe_id="workspaces_ai_agent_access_draft",
    display_name="WorkSpaces AI agent access (draft, not deployable)",
    display_name_zh="WorkSpaces AI 代理存取（草案，尚不可部署）",
    supported_candidate_patterns=(
        "workspaces",
        "workspaces applications",
        "managed workspaces",
        "ai agents",
        "ai agent",
        "operate desktop applications",
        "desktop applications",
        "desktop and application streaming",
        "agent access",
        "mcp endpoint",
        "service:WorkSpaces",
    ),
    required_aws_services=("WorkSpaces", "IAM", "CloudWatch", "CloudTrail", "S3"),
    required_region_capabilities=(
        "workspaces_applications_available",
        "workspaces_agent_access_available",
    ),
    estimated_cost_model_id=None,
    deployable_resource_types=(),
    required_iam_actions=(),
    approval_required_fields=("selected_candidate_id", "approved_by", "approved_cost_ceiling_usd"),
    deployment_inputs_schema={},
    success_criteria=(),
    evidence_to_collect=(),
    cleanup_strategy=None,
    cleanup_verification=(),
    risk_level="high",
    stop_conditions=(
        "未確認目標區域是否支援。",
        "尚無成本模型，無法估算 PoC 花費。",
        "代理可操作桌面環境，未設人工中止機制前不得啟動。",
    ),
    unsupported_conditions=(
        "任何真實使用者桌面或正式環境。",
        "任何含個資或客戶資料的畫面。",
    ),
    deployable=False,
    needs_region_confirmation=True,
    needs_environment_preparation=True,
    needs_cost_model=True,
    draft_notes=(
        "若要實作，至少需要：WorkSpaces Applications 堆疊。",
        "agent access 或 MCP endpoint 設定。",
        "一個用於測試的桌面應用程式。",
        "最小權限 IAM policy。",
        "CloudWatch 指標與日誌。",
        "CloudTrail data events。",
        "如涉及畫面或工作階段紀錄，需 S3 存放證據並先行遮蔽。",
        "人工觀察與隨時中止（human observe / stop mode）。",
        "完整 cleanup 計畫與清除後回查。",
    ),
)


REGISTRY: tuple[RecipeDefinition, ...] = (
    S3_FILES,
    LAMBDA_SELF_MANAGED_STORAGE,
    WORKSPACES_AI_AGENT_ACCESS_DRAFT,
)


def candidate_search_text(candidate: dict[str, Any] | None) -> tuple[str, set[str]]:
    """Collect everything a candidate says about itself, plus its services.

    Matching on the title alone misses real articles: a headline may name the
    product without naming the capability, while the explanation layer and the
    detected services carry the terms a recipe is registered against.
    """

    candidate = candidate or {}
    explanation = candidate.get("source_explanation") or candidate.get("explanation") or {}
    architecture = explanation.get("implementation_architecture") or {}

    parts: list[str] = [
        str(candidate.get(key) or "")
        for key in ("title", "source_url", "candidate_id", "summary")
    ]
    parts.append(str(explanation.get("evidence_text") or ""))
    parts.extend(str(item.get("point") or "") for item in explanation.get("key_points") or [])
    parts.extend(
        str(item.get("context") or "")
        for item in explanation.get("possible_application_contexts") or []
    )
    parts.extend(str(claim) for claim in candidate.get("initial_claims") or [])

    services = {
        str(item.get("service") or "")
        for item in architecture.get("core_components") or []
        if item.get("service")
    }
    services |= {str(name) for name in candidate.get("related_aws_services") or []}
    services |= {str(name) for name in candidate.get("detected_services") or []}
    parts.extend(sorted(services))

    return " ".join(parts), services


def all_recipes() -> tuple[RecipeDefinition, ...]:
    return REGISTRY


def get_recipe(recipe_id: str) -> RecipeDefinition | None:
    return next((r for r in REGISTRY if r.recipe_id == recipe_id), None)


def deployable_recipe_ids() -> list[str]:
    return [r.recipe_id for r in REGISTRY if r.is_deployable()]


def select_recipe(candidate: dict[str, Any] | None) -> dict[str, Any]:
    """Resolve a Skill 3 candidate to a recipe, or explain why it cannot deploy.

    Returns a decision dict rather than a bare recipe so both Skill 3 and Skill 4
    can render the same reason to a human. ``deployable_recipe_registered`` is the
    only field the deployer is allowed to act on.
    """

    candidate = candidate or {}
    haystack, services = candidate_search_text(candidate)

    matches = [r for r in REGISTRY if r.matches(haystack, services)]
    if not matches:
        return {
            "status": "needs_new_recipe",
            "deployable_recipe_registered": False,
            "recipe_id": None,
            "reason_zh": "此候選沒有對應的已登錄 recipe，Skill 4 不得建立任何 AWS 資源。",
            "next_step_zh": "下一步是撰寫一份 recipe，不是建立 AWS 資源。",
            "authoring_template": "docs/s4-recipe-authoring-template.md",
            "detected_services": sorted(services),
        }

    deployable = [r for r in matches if r.is_deployable()]
    if deployable:
        recipe = deployable[0]
        return {
            "status": "recipe_registered",
            "deployable_recipe_registered": True,
            "recipe_id": recipe.recipe_id,
            "recipe": recipe.to_dict(),
            "reason_zh": f"已比對到可部署 recipe：{recipe.display_name_zh}。",
            "next_step_zh": "可進入 Skill 4 的人工核准與部署前檢查。",
        }

    recipe = matches[0]
    blocking = recipe.blocking_flags() + recipe.contract_gaps()
    return {
        "status": "recipe_draft_only",
        "deployable_recipe_registered": False,
        "recipe_id": recipe.recipe_id,
        "recipe": recipe.to_dict(),
        "reason_zh": (
            f"已比對到 recipe 草案：{recipe.display_name_zh}，"
            "但尚未具備部署條件，Skill 4 不得建立任何 AWS 資源。"
        ),
        "next_step_zh": "下一步是補齊此 recipe 草案缺少的項目並改為可部署，不是建立 AWS 資源。",
        "blocking": blocking,
        "authoring_template": "docs/s4-recipe-authoring-template.md",
    }


CEILING_FIELD = "approved_cost_ceiling_usd"
CEILING_ALIASES = ("approved_ceiling_usd", "approvedCeilingUsd")


def read_cost_ceiling(approval: dict[str, Any] | None) -> float | None:
    """Read the approved ceiling, accepting older aliases on input only.

    Artifacts are always written back with the canonical name, so a stale alias
    can be consumed once but never propagates into a new artifact.
    """

    approval = approval or {}
    for key in (CEILING_FIELD, *CEILING_ALIASES):
        value = approval.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return None


def _positive_ceiling(approval: dict[str, Any] | None) -> float | None:
    value = read_cost_ceiling(approval)
    return value if value is not None and value > 0 else None


def canonicalize_approval(approval: dict[str, Any] | None) -> dict[str, Any]:
    """Return the approval with the ceiling normalised to the canonical field."""

    canonical = dict(approval or {})
    value = read_cost_ceiling(canonical)
    for alias in CEILING_ALIASES:
        canonical.pop(alias, None)
    if value is not None:
        canonical[CEILING_FIELD] = value
    return canonical


def deployment_preflight(
    decision: dict[str, Any],
    approval: dict[str, Any] | None,
    region_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the checks that must all pass before any AWS resource is created."""

    approval = approval or {}
    region_state = region_state or {}
    recipe = get_recipe(str(decision.get("recipe_id") or "")) if decision.get("recipe_id") else None
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "passed": bool(ok), "說明": detail})

    add(
        "selected_candidate_id",
        bool(approval.get("selected_candidate_id")),
        "核准文件必須指名一個候選。",
    )
    add(
        "named_human_approval",
        bool(approval.get("approved_by")) and approval.get("deployment_authorized") is True,
        "必須有具名核准者，且 deployment_authorized 為 true。",
    )
    add(
        "approved_cost_ceiling",
        _positive_ceiling(approval) is not None,
        "必須有大於零的核准花費上限（approved_cost_ceiling_usd）。",
    )
    add(
        "deployable_recipe_exists",
        bool(decision.get("deployable_recipe_registered")) and recipe is not None and recipe.is_deployable(),
        "必須有已登錄且可部署的 recipe；草案與通用成本模型都不算。",
    )
    add(
        "region_acknowledged_or_confirmed",
        region_state.get("status") == "feature_confirmed"
        or region_state.get("region_warning_acknowledged") is True,
        "目標區域須經官方確認，或由核准者明確承認風險。",
    )
    add(
        "cleanup_strategy_exists",
        bool(recipe and recipe.cleanup_strategy and recipe.cleanup_verification),
        "必須有清除策略與清除後的回查方式。",
    )
    add(
        "success_criteria_exists",
        bool(recipe and recipe.success_criteria),
        "必須事先定義成功條件。",
    )
    add(
        "evidence_plan_exists",
        bool(recipe and recipe.evidence_to_collect),
        "必須事先定義要蒐集哪些證據。",
    )

    failed = [c["check"] for c in checks if not c["passed"]]
    return {
        "status": "ready_for_deployment" if not failed else "blocked",
        "checks": checks,
        "failed_checks": failed,
        "rule_zh": "八項檢查全部通過才允許建立 AWS 資源；任何一項未過即停止。",
    }
