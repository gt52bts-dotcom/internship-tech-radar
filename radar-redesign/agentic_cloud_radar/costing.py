"""Auditable PoC cost quotations for registered radar recipes.

The quotation is an estimate built from public AWS list prices and explicit
usage assumptions.  It is never presented as an AWS invoice or a promise that
the account will be charged exactly this amount.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_CEILING
import hashlib
from typing import Any


HOURS_PER_MONTH = Decimal("730")
AWS_S3_PRICING_URL = "https://aws.amazon.com/s3/pricing/"
AWS_EC2_PRICING_URL = "https://aws.amazon.com/ec2/pricing/on-demand/"
AWS_EBS_PRICING_URL = "https://aws.amazon.com/ebs/pricing/"
AWS_PRICE_LIST_DOC_URL = (
    "https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/"
    "finding-prices-in-service-price-list-files.html"
)
AWS_EC2_SINGAPORE_PRICE_URL = (
    "https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/"
    "ec2-ondemand-without-sec-sel/Asia%20Pacific%20(Singapore)/Linux/index.json"
)
AWS_LAMBDA_PRICING_URL = "https://aws.amazon.com/lambda/pricing/"


RATE_CARD = {
    "ec2_t3_micro": {
        "label": "EC2 t3.micro Linux 隨需執行個體",
        "rate": Decimal("0.0132"),
        "unit": "USD/instance-hour",
        "source_url": AWS_EC2_SINGAPORE_PRICE_URL,
        "source_basis": "AWS public EC2 price file, Asia Pacific (Singapore)",
        "effective_date": "2026-07-01",
    },
    "ebs_gp3": {
        "label": "EBS gp3 根磁碟",
        "rate": Decimal("0.096"),
        "unit": "USD/GB-month",
        "source_url": AWS_EBS_PRICING_URL,
        "source_basis": "AWS Price List API snapshot, Asia Pacific (Singapore)",
        "effective_date": "2026-07-01",
    },
    "s3_files_storage": {
        "label": "S3 Files 高效能儲存",
        "rate": Decimal("0.36"),
        "unit": "USD/GB-month",
        "source_url": AWS_S3_PRICING_URL,
        "source_basis": "AWS Price List API snapshot, Asia Pacific (Singapore)",
        "effective_date": "2026-07-01",
    },
    "s3_files_write": {
        "label": "S3 Files write access",
        "rate": Decimal("0.06"),
        "unit": "USD/GB",
        "source_url": AWS_S3_PRICING_URL,
        "source_basis": "AWS S3 Files public pricing example rate",
        "effective_date": "2026-07-30",
    },
    "s3_files_export_read": {
        "label": "S3 Files sync export/read",
        "rate": Decimal("0.03"),
        "unit": "USD/GB",
        "source_url": AWS_S3_PRICING_URL,
        "source_basis": "AWS S3 Files public pricing example rate",
        "effective_date": "2026-07-30",
    },
    "s3_files_small_read": {
        "label": "S3 Files small read",
        "rate": Decimal("0.03"),
        "unit": "USD/GB",
        "source_url": AWS_S3_PRICING_URL,
        "source_basis": "AWS S3 Files public pricing example rate",
        "effective_date": "2026-07-30",
    },
    "s3_files_import_write": {
        "label": "S3 Files sync import/write",
        "rate": Decimal("0.06"),
        "unit": "USD/GB",
        "source_url": AWS_S3_PRICING_URL,
        "source_basis": "AWS S3 Files public pricing example rate",
        "effective_date": "2026-07-30",
    },
    "s3_standard_storage": {
        "label": "S3 Standard 儲存",
        "rate": Decimal("0.025"),
        "unit": "USD/GB-month",
        "source_url": AWS_S3_PRICING_URL,
        "source_basis": "AWS Price List API snapshot, Asia Pacific (Singapore), first 50 TB",
        "effective_date": "2026-07-01",
    },
    "s3_tier1_request": {
        "label": "S3 Tier 1 PUT/COPY/POST/LIST",
        "rate": Decimal("0.000005"),
        "unit": "USD/request",
        "source_url": AWS_S3_PRICING_URL,
        "source_basis": "AWS Price List API snapshot, Asia Pacific (Singapore)",
        "effective_date": "2026-07-01",
    },
    "s3_tier2_request": {
        "label": "S3 Tier 2 GET 與其他請求",
        "rate": Decimal("0.0000004"),
        "unit": "USD/request",
        "source_url": AWS_S3_PRICING_URL,
        "source_basis": "AWS Price List API snapshot, Asia Pacific (Singapore)",
        "effective_date": "2026-07-01",
    },
    "lambda_request": {
        "label": "AWS Lambda requests",
        "rate": Decimal("0.0000002"),
        "unit": "USD/request",
        "source_url": AWS_LAMBDA_PRICING_URL,
        "source_basis": "AWS Lambda public request price",
        "effective_date": "2026-07-31",
    },
    "lambda_x86_duration": {
        "label": "AWS Lambda x86 duration",
        "rate": Decimal("0.0000166667"),
        "unit": "USD/GB-second",
        "source_url": AWS_LAMBDA_PRICING_URL,
        "source_basis": "AWS Lambda public on-demand duration price",
        "effective_date": "2026-07-31",
    },
}


S3_FILES_SCENARIOS = {
    "low": {
        "label": "低用量",
        "hours": Decimal("1"),
        "active_gb": Decimal("0.02"),
        "write_gb": Decimal("0.02"),
        "export_read_gb": Decimal("0.02"),
        "small_read_gb": Decimal("0.02"),
        "import_write_gb": Decimal("0.02"),
        "tier1_requests": Decimal("30"),
        "tier2_requests": Decimal("60"),
    },
    "expected": {
        "label": "預期用量",
        "hours": Decimal("2"),
        "active_gb": Decimal("0.10"),
        "write_gb": Decimal("0.10"),
        "export_read_gb": Decimal("0.10"),
        "small_read_gb": Decimal("0.10"),
        "import_write_gb": Decimal("0.10"),
        "tier1_requests": Decimal("100"),
        "tier2_requests": Decimal("200"),
    },
    "high": {
        "label": "高用量",
        "hours": Decimal("4"),
        "active_gb": Decimal("0.50"),
        "write_gb": Decimal("0.50"),
        "export_read_gb": Decimal("0.50"),
        "small_read_gb": Decimal("0.50"),
        "import_write_gb": Decimal("0.50"),
        "tier1_requests": Decimal("500"),
        "tier2_requests": Decimal("1000"),
    },
}


LAMBDA_SELF_MANAGED_SCENARIOS = {
    "low": {"label": "Low", "hours": Decimal("0.5"), "artifact_gb": Decimal("0.01"), "lambda_requests": Decimal("5"), "lambda_gb_seconds": Decimal("1"), "s3_put_requests": Decimal("10"), "s3_get_requests": Decimal("10")},
    "expected": {"label": "Expected", "hours": Decimal("1"), "artifact_gb": Decimal("0.02"), "lambda_requests": Decimal("15"), "lambda_gb_seconds": Decimal("5"), "s3_put_requests": Decimal("30"), "s3_get_requests": Decimal("30")},
    "high": {"label": "High", "hours": Decimal("2"), "artifact_gb": Decimal("0.05"), "lambda_requests": Decimal("50"), "lambda_gb_seconds": Decimal("20"), "s3_put_requests": Decimal("100"), "s3_get_requests": Decimal("100")},
}


def build_cost_quote(
    candidate: dict[str, Any],
    run_id: str,
    target_region: str | None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Return a quote artifact for a known recipe, or a traceable pending quote."""

    now = generated_at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    candidate_id = str(candidate.get("candidate_id") or "unknown-candidate")
    quote_id = _quote_id(run_id, candidate_id)
    base = {
        "schema_version": "poc.cost-quote.v1",
        "quote_id": quote_id,
        "run_id": run_id,
        "candidate_id": candidate_id,
        "candidate_title": candidate.get("title") or "unknown",
        "generated_at": now.isoformat(),
        "valid_until": (now + timedelta(days=7)).date().isoformat(),
        "currency": "USD",
        "target_region": target_region or "ap-southeast-1",
        "quote_kind": "non_binding_public_price_estimate",
        "rate_card_source": "static_public_rate_card",
        "live_pricing_api_used": False,
        "formal_procurement_quote_ready": False,
        "disclaimer": (
            "這是依 AWS 公開牌價與明列用量假設產生的非約束性 PoC 成本估算，"
            "不是 AWS 帳單、發票、即時 AWS Pricing API 查詢或正式銷售報價。"
            "實際費用以部署後的 AWS 帳務資料為準；正式採購前需重新查價。"
        ),
    }
    if _is_s3_files(candidate):
        return _build_s3_files_quote(base)
    if _is_lambda_self_managed_storage(candidate):
        return _build_lambda_self_managed_quote(base)
    return {
        **base,
        "status": "needs_registered_cost_model",
        "pricing_basis": "No registered cost model matches this candidate.",
        "scenarios": {},
        "expected_total_usd": None,
        "recommended_approval_ceiling_usd": None,
        "missing_inputs": ["registered_recipe_and_rate_card"],
    }


def _build_s3_files_quote(base: dict[str, Any]) -> dict[str, Any]:
    scenarios = {
        name: _price_s3_files_scenario(name, assumptions)
        for name, assumptions in S3_FILES_SCENARIOS.items()
    }
    high_total = Decimal(str(scenarios["high"]["total_usd"]))
    ceiling = _round_up(high_total, Decimal("0.05"))
    return {
        **base,
        "status": "estimated",
        "confidence": "medium",
        "recipe": "s3_files_cdk",
        "pricing_basis": (
            "AWS public list-price snapshots for Asia Pacific (Singapore); "
            "S3 Files data-access rates use the current public S3 pricing example."
        ),
        "price_snapshot_date": "2026-07-30",
        "scenarios": scenarios,
        "expected_total_usd": scenarios["expected"]["total_usd"],
        "estimated_range_usd": {
            "low": scenarios["low"]["total_usd"],
            "expected": scenarios["expected"]["total_usd"],
            "high": scenarios["high"]["total_usd"],
        },
        "recommended_approval_ceiling_usd": _money(ceiling),
        "approval_ceiling_basis": "High-use scenario rounded up to the next USD 0.05.",
        "verified_recipe_facts": [
            "Amazon Linux 2023 public AMI root volume is 8 GiB gp3 in ap-southeast-1.",
            "The registered recipe creates one t3.micro test instance when createTestInstance=true.",
        ],
        "zero_direct_charge_resources": [
            "VPC, subnet, route table, internet gateway, security groups, IAM role and CloudFormation have no separate hourly line item in this recipe.",
        ],
        "exclusions": [
            "Tax, private pricing, Savings Plans, credits and Free Tier are excluded.",
            "Unexpected data transfer, retries, log ingestion and resources outside the registered recipe are excluded.",
            "S3 Files access rates are public example rates; recheck the AWS pricing page before deployment if the quote has expired.",
        ],
        "sources": _quote_sources(
            "ec2_t3_micro", "ebs_gp3", "s3_files_storage", "s3_files_write", "s3_files_export_read",
            "s3_files_small_read", "s3_files_import_write", "s3_standard_storage", "s3_tier1_request", "s3_tier2_request",
        ),
    }


def _build_lambda_self_managed_quote(base: dict[str, Any]) -> dict[str, Any]:
    scenarios = {
        name: _price_lambda_self_managed_scenario(name, assumptions)
        for name, assumptions in LAMBDA_SELF_MANAGED_SCENARIOS.items()
    }
    high_total = Decimal(str(scenarios["high"]["total_usd"]))
    ceiling = _round_up(high_total, Decimal("0.05"))
    return {
        **base,
        "status": "estimated",
        "confidence": "medium",
        "recipe": "lambda_self_managed_s3_code_storage_cdk",
        "pricing_basis": "AWS public Lambda and S3 list prices for the registered single-function, versioned-S3-object PoC.",
        "price_snapshot_date": "2026-07-31",
        "scenarios": scenarios,
        "expected_total_usd": scenarios["expected"]["total_usd"],
        "estimated_range_usd": {name: scenarios[name]["total_usd"] for name in ("low", "expected", "high")},
        "recommended_approval_ceiling_usd": _money(ceiling),
        "approval_ceiling_basis": "High-use scenario rounded up to the next USD 0.05.",
        "verified_recipe_facts": [
            "The registered recipe creates one versioned S3 bucket and one Lambda function using S3ObjectStorageMode=REFERENCE.",
            "CloudFormation, IAM roles, bucket policies, and deletion requests have no separate direct line item in this recipe.",
        ],
        "zero_direct_charge_resources": [
            "CloudFormation, IAM role, S3 bucket policy, and Lambda function configuration have no separate direct charge.",
        ],
        "exclusions": [
            "Tax, private pricing, Savings Plans, credits and Free Tier are excluded.",
            "Unexpected data transfer, retries, CloudWatch log ingestion, and resources outside the registered recipe are excluded.",
            "Recheck the Lambda and S3 pricing pages before deployment if the quote has expired.",
        ],
        "sources": _quote_sources(
            "lambda_request", "lambda_x86_duration", "s3_standard_storage", "s3_tier1_request", "s3_tier2_request",
        ),
    }


def _price_lambda_self_managed_scenario(name: str, assumptions: dict[str, Decimal]) -> dict[str, Any]:
    items = [
        _line("lambda_request", assumptions["lambda_requests"], "requests", "invocations x USD/request"),
        _line("lambda_x86_duration", assumptions["lambda_gb_seconds"], "GB-seconds", "allocated GB-seconds x USD/GB-second"),
        _line("s3_standard_storage", assumptions["artifact_gb"] * assumptions["hours"] / HOURS_PER_MONTH, "GB-month", "artifact GB x hours / 730 x USD/GB-month"),
        _line("s3_tier1_request", assumptions["s3_put_requests"], "requests", "PUT/COPY/POST/LIST count x USD/request"),
        _line("s3_tier2_request", assumptions["s3_get_requests"], "requests", "GET count x USD/request"),
    ]
    total = sum((Decimal(str(item["subtotal_usd"])) for item in items), Decimal("0"))
    return {
        "scenario": name,
        "label": assumptions["label"],
        "assumptions": {key: _number(value) for key, value in assumptions.items() if key != "label"},
        "line_items": items,
        "total_usd": _money(total),
        "display_total_usd": f"{total.quantize(Decimal('0.01'), rounding=ROUND_CEILING):.2f}",
    }


def _price_s3_files_scenario(name: str, assumptions: dict[str, Decimal]) -> dict[str, Any]:
    hours = assumptions["hours"]
    active_gb = assumptions["active_gb"]
    items = [
        _line("ec2_t3_micro", hours, "hours", "hours × USD/instance-hour"),
        _line("ebs_gp3", Decimal("8") * hours / HOURS_PER_MONTH, "GB-month", "8 GiB × hours ÷ 730 × USD/GB-month"),
        _line("s3_files_storage", active_gb * hours / HOURS_PER_MONTH, "GB-month", "active GB × hours ÷ 730 × USD/GB-month"),
        _line("s3_files_write", assumptions["write_gb"], "GB", "write GB × USD/GB"),
        _line("s3_files_export_read", assumptions["export_read_gb"], "GB", "export/read GB × USD/GB"),
        _line("s3_files_small_read", assumptions["small_read_gb"], "GB", "small-read GB × USD/GB"),
        _line("s3_files_import_write", assumptions["import_write_gb"], "GB", "import/write GB × USD/GB"),
        _line("s3_standard_storage", active_gb * hours / HOURS_PER_MONTH, "GB-month", "stored GB × hours ÷ 730 × USD/GB-month"),
        _line("s3_tier1_request", assumptions["tier1_requests"], "requests", "request count × USD/request"),
        _line("s3_tier2_request", assumptions["tier2_requests"], "requests", "request count × USD/request"),
    ]
    total = sum((Decimal(str(item["subtotal_usd"])) for item in items), Decimal("0"))
    return {
        "scenario": name,
        "label": assumptions["label"],
        "assumptions": {key: _number(value) for key, value in assumptions.items() if key != "label"},
        "line_items": items,
        "total_usd": _money(total),
        "display_total_usd": f"{total.quantize(Decimal('0.01'), rounding=ROUND_CEILING):.2f}",
    }


def _line(rate_key: str, quantity: Decimal, quantity_unit: str, formula: str) -> dict[str, Any]:
    rate = RATE_CARD[rate_key]
    subtotal = quantity * rate["rate"]
    return {
        "item": rate["label"],
        "rate_usd": _number(rate["rate"]),
        "rate_unit": rate["unit"],
        "quantity": _number(quantity),
        "quantity_unit": quantity_unit,
        "formula": formula,
        "subtotal_usd": _money(subtotal),
        "source_url": rate["source_url"],
        "source_basis": rate["source_basis"],
        "effective_date": rate["effective_date"],
    }


def _quote_sources(*rate_keys: str) -> list[dict[str, str]]:
    seen: set[str] = set()
    sources = []
    for rate_key in rate_keys or tuple(RATE_CARD):
        rate = RATE_CARD[rate_key]
        url = str(rate["source_url"])
        if url in seen:
            continue
        seen.add(url)
        sources.append({"url": url, "purpose": str(rate["source_basis"])})
    sources.append({"url": AWS_PRICE_LIST_DOC_URL, "purpose": "AWS Price List API interpretation"})
    sources.append({"url": AWS_EC2_PRICING_URL, "purpose": "EC2 On-Demand pricing terms"})
    return sources


def _is_s3_files(candidate: dict[str, Any]) -> bool:
    haystack = " ".join(
        str(candidate.get(key) or "").lower()
        for key in ("title", "source_url")
    )
    return "s3 files" in haystack or "launching-s3-files" in haystack


def _is_lambda_self_managed_storage(candidate: dict[str, Any]) -> bool:
    haystack = " ".join(
        str(candidate.get(key) or "").lower()
        for key in ("title", "source_url")
    )
    return "self-managed" in haystack and ("lambda" in haystack or "function-code" in haystack)


def _quote_id(run_id: str, candidate_id: str) -> str:
    digest = hashlib.sha256(f"{run_id}:{candidate_id}".encode("utf-8")).hexdigest()[:12].upper()
    return f"POC-QUOTE-{digest}"


def _round_up(value: Decimal, increment: Decimal) -> Decimal:
    return (value / increment).to_integral_value(rounding=ROUND_CEILING) * increment


def _money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.000001")))


def _number(value: Decimal) -> int | float:
    integral = value.to_integral_value()
    if value == integral:
        return int(integral)
    return float(value.normalize())
