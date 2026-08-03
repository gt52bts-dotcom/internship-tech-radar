"""Skill 4 review evidence: a resource inventory instead of a screenshot.

The earlier design captured an Infrastructure Composer PNG and hashed it.  That
never proved much: the program could not read the image, so it only checked that
a file existed with matching metadata, and the whole judgement rested on a human
looking at a picture the code could not verify.

This module records what CloudFormation reports instead.  ``describe_stack_resources``
returns structured data, so three things become checkable rather than assumed:

1. every resource the deployment created is listed;
2. that list can be reconciled against the resources the Skill 3 quote priced,
   which is how a missing line item is caught in minutes;
3. the exact bytes the reviewer approved are the exact bytes the program hashed,
   because both are the same JSON document.

The permission surface is recorded the same way.  A vendor page shows one sample
policy; the actions a deployment really needs are only visible after it runs, and
for a regulated environment that list is a deliverable in its own right.

Nothing here contacts AWS.  The caller supplies the API response so the pipeline
stays testable offline and identical inputs always produce identical evidence.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any


SCHEMA_VERSION = "s4.resource-inventory.v1"

# Resources CloudFormation does not own but the deployment still creates, so a
# reviewer is not told the quote priced something that never appears in a stack.
IMPLICIT_RESOURCE_TYPES = {
    "AWS::Logs::LogGroup": "Lambda 或其他服務會自動建立預設 log group，不屬於 stack 資源。",
}


def build_resource_inventory(
    runtime: dict[str, Any],
    stack_resources: list[dict[str, Any]],
    quote: dict[str, Any] | None = None,
    permission_actions: list[str] | None = None,
    captured_at: datetime | None = None,
) -> dict[str, Any]:
    """Return the review packet a named human confirms before cleanup."""

    moment = (captured_at or datetime.now(timezone.utc)).isoformat()
    resources = [_resource_row(item) for item in stack_resources or []]
    reconciliation = reconcile_quote_against_resources(quote, resources)
    inventory = {
        "schema_version": SCHEMA_VERSION,
        "run_id": (runtime or {}).get("run_id", "unknown-run"),
        "stack_name": _first(runtime, ("stack_name",), ("cloudformation", "stack_name"), ("deployment", "stack_name")),
        "region": _first(runtime, ("region",), ("cloudformation", "region"), ("deployment", "region"), ("deployment", "target_region")),
        "captured_at": moment,
        "resource_count": len(resources),
        "resources": resources,
        "quote_reconciliation": reconciliation,
        "permission_surface": _permission_surface(permission_actions),
        "review_rule": (
            "人工確認的內容就是這份盤點 JSON；inventory_sha256 涵蓋 resources、"
            "quote_reconciliation 與 permission_surface，確保人看過的與程式驗過的是同一份。"
        ),
    }
    inventory["inventory_sha256"] = _digest(inventory)
    return inventory


def reconcile_quote_against_resources(
    quote: dict[str, Any] | None,
    resources: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare priced resources against deployed ones.

    A ``deployed_not_quoted`` row means the quote missed something the run really
    creates, which makes the estimate wrong regardless of how small the amount is.
    """

    quoted_types = _quoted_resource_types(quote)
    deployed_types = {item["resource_type"] for item in resources}
    rows: list[dict[str, Any]] = []
    for resource_type in sorted(quoted_types | deployed_types):
        quoted = resource_type in quoted_types
        deployed = resource_type in deployed_types
        if quoted and deployed:
            verdict = "matched"
        elif deployed:
            verdict = "deployed_not_quoted"
        else:
            verdict = "quoted_not_deployed"
        row = {
            "resource_type": resource_type,
            "quoted": quoted,
            "deployed": deployed,
            "verdict": verdict,
        }
        if verdict == "quoted_not_deployed" and resource_type in IMPLICIT_RESOURCE_TYPES:
            row["verdict"] = "quoted_implicit_resource"
            row["note"] = IMPLICIT_RESOURCE_TYPES[resource_type]
        rows.append(row)
    missing = [row["resource_type"] for row in rows if row["verdict"] == "deployed_not_quoted"]
    unexplained = [row["resource_type"] for row in rows if row["verdict"] == "quoted_not_deployed"]
    if not quoted_types:
        status = "no_quote_resource_list"
    elif missing:
        status = "quote_incomplete"
    elif unexplained:
        status = "quote_lists_undeployed_resources"
    else:
        status = "consistent"
    return {
        "status": status,
        "rows": rows,
        "deployed_not_quoted": missing,
        "quoted_not_deployed": unexplained,
        "rule": "出現 deployed_not_quoted 即代表報價單漏列了實際會建立的資源，必須修正報價，不能只調整金額。",
    }


def _first(payload: dict[str, Any] | None, *paths: tuple[str, ...]) -> Any:
    """Read the first populated path, since runtimes nest these differently."""

    for path in paths:
        cursor: Any = payload or {}
        for key in path:
            cursor = cursor.get(key) if isinstance(cursor, dict) else None
            if cursor is None:
                break
        if cursor:
            return cursor
    return None


def _resource_row(item: dict[str, Any]) -> dict[str, Any]:
    """Keep the reviewable fields and redact the identifier."""

    return {
        "logical_id": str(item.get("LogicalResourceId") or item.get("logical_id") or "unknown"),
        "resource_type": str(item.get("ResourceType") or item.get("resource_type") or "unknown"),
        "status": str(item.get("ResourceStatus") or item.get("status") or "unknown"),
        "physical_id_redacted": _redact(str(item.get("PhysicalResourceId") or item.get("physical_id") or "")),
    }


def _quoted_resource_types(quote: dict[str, Any] | None) -> set[str]:
    if not quote:
        return set()
    declared = quote.get("priced_resource_types")
    if isinstance(declared, list):
        return {str(value) for value in declared if str(value).strip()}
    return set()


def _permission_surface(actions: list[str] | None) -> dict[str, Any]:
    """Record the IAM actions the run actually needed.

    Public documentation shows a sample policy.  What a deployment really calls is
    only observable from the run, and a regulated reviewer needs that list to check
    least privilege.
    """

    cleaned = sorted({str(action).strip() for action in actions or [] if str(action).strip()})
    if not cleaned:
        return {
            "status": "not_recorded",
            "actions": [],
            "note": "此 run 未記錄實際使用的 IAM action，最小權限無法據此驗證。",
        }
    services = sorted({action.split(":", 1)[0] for action in cleaned if ":" in action})
    return {
        "status": "recorded",
        "actions": cleaned,
        "action_count": len(cleaned),
        "services": services,
        "note": "這是本次 PoC 實際觸發的 action，僅涵蓋已測試的 recipe，不等於正式環境所需的完整權限。",
    }


def _redact(value: str) -> str:
    if not value:
        return "unknown"
    if len(value) <= 10:
        return value[:2] + "…"
    return f"{value[:4]}…{value[-4:]}"


def _digest(inventory: dict[str, Any]) -> str:
    payload = {
        "run_id": inventory["run_id"],
        "stack_name": inventory["stack_name"],
        "region": inventory["region"],
        "resources": inventory["resources"],
        "quote_reconciliation": inventory["quote_reconciliation"],
        "permission_surface": inventory["permission_surface"],
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
