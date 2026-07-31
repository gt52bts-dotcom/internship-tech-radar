"""Auditable, reusable pre-deployment PoC cost quotations.

Skill 3 uses this module before Skill 4 can create resources.  The estimator is
intentionally layered:

* Level A: a registered, candidate-specific PoC recipe with explicit usage
  assumptions and a static public rate card.
* Level B: a generic usage model inferred from detected AWS services or IaC
  resource types.  This is good enough for a small PoC approval ceiling, but it
  does not imply that Skill 4 has a deployable recipe.
* Level C: not enough service or usage evidence to produce a dollar estimate.

Every quote is a non-binding public-price estimate, not an AWS invoice or formal
procurement quote.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_CEILING
import hashlib
import json
import re
from typing import Any


HOURS_PER_MONTH = Decimal("730")
AWS_S3_PRICING_URL = "https://aws.amazon.com/s3/pricing/"
AWS_EC2_PRICING_URL = "https://aws.amazon.com/ec2/pricing/on-demand/"
AWS_EBS_PRICING_URL = "https://aws.amazon.com/ebs/pricing/"
AWS_LAMBDA_PRICING_URL = "https://aws.amazon.com/lambda/pricing/"
AWS_GLUE_PRICING_URL = "https://aws.amazon.com/glue/pricing/"
AWS_CLOUDWATCH_PRICING_URL = "https://aws.amazon.com/cloudwatch/pricing/"
AWS_DYNAMODB_PRICING_URL = "https://aws.amazon.com/dynamodb/pricing/on-demand/"
AWS_SQS_PRICING_URL = "https://aws.amazon.com/sqs/pricing/"
AWS_SNS_PRICING_URL = "https://aws.amazon.com/sns/pricing/"
AWS_ATHENA_PRICING_URL = "https://aws.amazon.com/athena/pricing/"
AWS_LAKE_FORMATION_PRICING_URL = "https://aws.amazon.com/lake-formation/pricing/"
AWS_RAM_DOC_URL = "https://docs.aws.amazon.com/ram/latest/userguide/what-is.html"
AWS_PRICE_LIST_DOC_URL = (
    "https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/"
    "finding-prices-in-service-price-list-files.html"
)
AWS_PRICE_LIST_QUERY_API_URL = (
    "https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_pricing_GetProducts.html"
)
AWS_PRICING_CALCULATOR_URL = "https://docs.aws.amazon.com/pricing-calculator/"
AWS_CFN_ESTIMATE_URL = "https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_EstimateTemplateCost.html"
AWS_EC2_SINGAPORE_PRICE_URL = (
    "https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/"
    "ec2-ondemand-without-sec-sel/Asia%20Pacific%20(Singapore)/Linux/index.json"
)


RATE_CARD = {
    "ec2_t3_micro": {
        "label": "EC2 t3.micro Linux on-demand",
        "rate": Decimal("0.0132"),
        "unit": "USD/instance-hour",
        "source_url": AWS_EC2_SINGAPORE_PRICE_URL,
        "source_basis": "AWS public EC2 price file, Asia Pacific (Singapore)",
        "effective_date": "2026-07-01",
    },
    "ebs_gp3": {
        "label": "EBS gp3 storage",
        "rate": Decimal("0.096"),
        "unit": "USD/GB-month",
        "source_url": AWS_EBS_PRICING_URL,
        "source_basis": "AWS public EBS pricing, Asia Pacific (Singapore)",
        "effective_date": "2026-07-01",
    },
    "s3_files_storage": {
        "label": "S3 Files active storage",
        "rate": Decimal("0.36"),
        "unit": "USD/GB-month",
        "source_url": AWS_S3_PRICING_URL,
        "source_basis": "AWS S3 Files public pricing example rate",
        "effective_date": "2026-07-30",
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
        "label": "S3 Files export/read access",
        "rate": Decimal("0.03"),
        "unit": "USD/GB",
        "source_url": AWS_S3_PRICING_URL,
        "source_basis": "AWS S3 Files public pricing example rate",
        "effective_date": "2026-07-30",
    },
    "s3_files_small_read": {
        "label": "S3 Files small read access",
        "rate": Decimal("0.03"),
        "unit": "USD/GB",
        "source_url": AWS_S3_PRICING_URL,
        "source_basis": "AWS S3 Files public pricing example rate",
        "effective_date": "2026-07-30",
    },
    "s3_files_import_write": {
        "label": "S3 Files import/write access",
        "rate": Decimal("0.06"),
        "unit": "USD/GB",
        "source_url": AWS_S3_PRICING_URL,
        "source_basis": "AWS S3 Files public pricing example rate",
        "effective_date": "2026-07-30",
    },
    "s3_standard_storage": {
        "label": "S3 Standard storage",
        "rate": Decimal("0.025"),
        "unit": "USD/GB-month",
        "source_url": AWS_S3_PRICING_URL,
        "source_basis": "AWS public S3 Standard storage price snapshot, Asia Pacific (Singapore)",
        "effective_date": "2026-07-01",
    },
    "s3_tier1_request": {
        "label": "S3 PUT/COPY/POST/LIST requests",
        "rate": Decimal("0.000005"),
        "unit": "USD/request",
        "source_url": AWS_S3_PRICING_URL,
        "source_basis": "AWS public S3 request price snapshot, Asia Pacific (Singapore)",
        "effective_date": "2026-07-01",
    },
    "s3_tier2_request": {
        "label": "S3 GET requests",
        "rate": Decimal("0.0000004"),
        "unit": "USD/request",
        "source_url": AWS_S3_PRICING_URL,
        "source_basis": "AWS public S3 request price snapshot, Asia Pacific (Singapore)",
        "effective_date": "2026-07-01",
    },
    "lambda_request": {
        "label": "Lambda requests",
        "rate": Decimal("0.0000002"),
        "unit": "USD/request",
        "source_url": AWS_LAMBDA_PRICING_URL,
        "source_basis": "AWS Lambda public request price",
        "effective_date": "2026-07-31",
    },
    "lambda_x86_duration": {
        "label": "Lambda x86 duration",
        "rate": Decimal("0.0000166667"),
        "unit": "USD/GB-second",
        "source_url": AWS_LAMBDA_PRICING_URL,
        "source_basis": "AWS Lambda public on-demand duration price",
        "effective_date": "2026-07-31",
    },
    "glue_data_catalog_object_month": {
        "label": "Glue Data Catalog metadata objects",
        "rate": Decimal("0.00001"),
        "unit": "USD/object-month",
        "source_url": AWS_GLUE_PRICING_URL,
        "source_basis": "AWS Glue Data Catalog marginal storage price after free tier",
        "effective_date": "2026-07-31",
    },
    "glue_data_catalog_request": {
        "label": "Glue Data Catalog API requests",
        "rate": Decimal("0.000001"),
        "unit": "USD/request",
        "source_url": AWS_GLUE_PRICING_URL,
        "source_basis": "AWS Glue Data Catalog marginal request price after free tier",
        "effective_date": "2026-07-31",
    },
    "cloudwatch_logs_ingestion": {
        "label": "CloudWatch Logs ingestion",
        "rate": Decimal("0.50"),
        "unit": "USD/GB ingested",
        "source_url": AWS_CLOUDWATCH_PRICING_URL,
        "source_basis": "Amazon CloudWatch Logs public ingestion price example",
        "effective_date": "2026-07-31",
    },
    "dynamodb_write_request": {
        "label": "DynamoDB on-demand write requests",
        "rate": Decimal("0.00000125"),
        "unit": "USD/write request",
        "source_url": AWS_DYNAMODB_PRICING_URL,
        "source_basis": "DynamoDB on-demand public write request pricing",
        "effective_date": "2026-07-31",
    },
    "dynamodb_read_request": {
        "label": "DynamoDB on-demand read requests",
        "rate": Decimal("0.00000025"),
        "unit": "USD/read request",
        "source_url": AWS_DYNAMODB_PRICING_URL,
        "source_basis": "DynamoDB on-demand public read request pricing",
        "effective_date": "2026-07-31",
    },
    "sqs_request": {
        "label": "SQS requests",
        "rate": Decimal("0.0000004"),
        "unit": "USD/request",
        "source_url": AWS_SQS_PRICING_URL,
        "source_basis": "Amazon SQS public request pricing",
        "effective_date": "2026-07-31",
    },
    "sns_publish": {
        "label": "SNS publishes",
        "rate": Decimal("0.0000005"),
        "unit": "USD/request",
        "source_url": AWS_SNS_PRICING_URL,
        "source_basis": "Amazon SNS public request pricing",
        "effective_date": "2026-07-31",
    },
    "athena_scanned": {
        "label": "Athena data scanned",
        "rate": Decimal("5.00"),
        "unit": "USD/TB scanned",
        "source_url": AWS_ATHENA_PRICING_URL,
        "source_basis": "Amazon Athena public SQL query pricing",
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
    "low": {"label": "低用量", "hours": Decimal("0.5"), "artifact_gb": Decimal("0.01"), "lambda_requests": Decimal("5"), "lambda_gb_seconds": Decimal("1"), "s3_put_requests": Decimal("10"), "s3_get_requests": Decimal("10")},
    "expected": {"label": "預期用量", "hours": Decimal("1"), "artifact_gb": Decimal("0.02"), "lambda_requests": Decimal("15"), "lambda_gb_seconds": Decimal("5"), "s3_put_requests": Decimal("30"), "s3_get_requests": Decimal("30")},
    "high": {"label": "高用量", "hours": Decimal("2"), "artifact_gb": Decimal("0.05"), "lambda_requests": Decimal("50"), "lambda_gb_seconds": Decimal("20"), "s3_put_requests": Decimal("100"), "s3_get_requests": Decimal("100")},
}


GENERIC_USAGE_SCENARIOS = {
    "low": {
        "label": "低用量",
        "hours": Decimal("0.5"),
        "storage_gb": Decimal("0.01"),
        "requests": Decimal("10"),
        "lambda_gb_seconds": Decimal("1"),
        "log_gb": Decimal("0.001"),
        "athena_tb_scanned": Decimal("0.00001"),
        "catalog_objects": Decimal("5"),
        "catalog_requests": Decimal("20"),
    },
    "expected": {
        "label": "預期用量",
        "hours": Decimal("1"),
        "storage_gb": Decimal("0.10"),
        "requests": Decimal("100"),
        "lambda_gb_seconds": Decimal("5"),
        "log_gb": Decimal("0.005"),
        "athena_tb_scanned": Decimal("0.0001"),
        "catalog_objects": Decimal("20"),
        "catalog_requests": Decimal("100"),
    },
    "high": {
        "label": "高用量",
        "hours": Decimal("4"),
        "storage_gb": Decimal("1"),
        "requests": Decimal("1000"),
        "lambda_gb_seconds": Decimal("20"),
        "log_gb": Decimal("0.05"),
        "athena_tb_scanned": Decimal("0.001"),
        "catalog_objects": Decimal("100"),
        "catalog_requests": Decimal("1000"),
    },
}


SERVICE_ALIASES = {
    "amazon s3": "s3",
    "s3": "s3",
    "lambda": "lambda",
    "aws lambda": "lambda",
    "cloudwatch": "cloudwatch",
    "amazon cloudwatch": "cloudwatch",
    "glue": "glue",
    "aws glue": "glue",
    "lake formation": "lakeformation",
    "aws lake formation": "lakeformation",
    "ram": "ram",
    "resource access manager": "ram",
    "aws resource access manager": "ram",
    "dynamodb": "dynamodb",
    "amazon dynamodb": "dynamodb",
    "sqs": "sqs",
    "amazon sqs": "sqs",
    "sns": "sns",
    "amazon sns": "sns",
    "athena": "athena",
    "amazon athena": "athena",
    "cloudformation": "cloudformation",
    "aws cloudformation": "cloudformation",
    "iam": "iam",
}

ZERO_DIRECT_CHARGE_SERVICES = {
    "cloudformation": "CloudFormation stack orchestration itself has no separate direct charge.",
    "iam": "IAM roles and policies have no separate direct charge.",
    "lakeformation": "Lake Formation permissions have no direct charge; underlying services still apply.",
    "ram": "AWS RAM resource sharing has no direct charge; shared resource usage can still incur charges.",
}


def build_cost_quote(
    candidate: dict[str, Any],
    run_id: str,
    target_region: str | None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Return a reusable pre-deployment PoC quote artifact."""

    now = generated_at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    candidate_id = str(candidate.get("candidate_id") or "unknown-candidate")
    base = {
        "schema_version": "poc.cost-quote.v2",
        "quote_id": _quote_id(run_id, candidate_id),
        "run_id": run_id,
        "candidate_id": candidate_id,
        "candidate_title": candidate.get("title") or "unknown",
        "generated_at": now.isoformat(),
        "valid_until": (now + timedelta(days=7)).date().isoformat(),
        "currency": "USD",
        "target_region": target_region or "ap-southeast-1",
        "quote_kind": "non_binding_public_price_estimate",
        "estimation_method": "pre_deployment_cost_estimation",
        "rate_card_source": "static_public_rate_card",
        "live_pricing_api_used": False,
        "formal_procurement_quote_ready": False,
        "disclaimer": (
            "這是 PoC 前的非正式公開牌價估算，用於 Skill 3 審查與 Skill 4 小額上限控管。"
            "它不是 AWS 帳單、正式採購報價，也未套用稅務、折扣、credits、Free Tier 或公司私有價格。"
        ),
    }
    if _is_s3_files(candidate):
        return _build_s3_files_quote(base)
    if _is_lambda_self_managed_storage(candidate):
        return _build_lambda_self_managed_quote(base)

    services = _detected_services(candidate)
    if _billable_generic_services(services):
        return _build_generic_usage_quote(base, services, candidate)

    return {
        **base,
        "status": "incomplete",
        "confidence": "low",
        "pricing_confidence": "low",
        "pricing_level": "Level C incomplete",
        "pricing_basis": "候選項目沒有足夠的服務、IaC resource type 或用量線索，無法產生可審核的 PoC 估價。",
        "detected_services": sorted(services),
        "scenarios": {},
        "expected_total_usd": None,
        "estimated_range_usd": None,
        "recommended_approval_ceiling_usd": None,
        "missing_inputs": ["aws_service_or_iac_resource_scope", "usage_assumptions"],
        "next_steps": [
            "補上候選項目的 AWS service/resource type。",
            "提供 PoC 低/中/高用量假設，或加入 deployable recipe 後重跑 Skill 3。",
        ],
    }


def _build_s3_files_quote(base: dict[str, Any]) -> dict[str, Any]:
    scenarios = {
        name: _price_s3_files_scenario(name, assumptions)
        for name, assumptions in S3_FILES_SCENARIOS.items()
    }
    high_total = Decimal(str(scenarios["high"]["total_usd"]))
    return {
        **base,
        "status": "estimated",
        "confidence": "medium",
        "pricing_confidence": "high",
        "pricing_level": "Level A registered recipe",
        "recipe": "s3_files_cdk",
        "pricing_basis": "已登錄 S3 Files CDK PoC recipe；用固定低/中/高用量和公開牌價試算。",
        "price_snapshot_date": "2026-07-30",
        "scenarios": scenarios,
        "expected_total_usd": scenarios["expected"]["total_usd"],
        "estimated_range_usd": {name: scenarios[name]["total_usd"] for name in ("low", "expected", "high")},
        "recommended_approval_ceiling_usd": _money(_round_up(high_total, Decimal("0.05"))),
        "approval_ceiling_basis": "高用量情境往上取到下一個 USD 0.05。",
        "verified_recipe_facts": [
            "Registered recipe creates one t3.micro test instance when createTestInstance=true.",
            "Amazon Linux 2023 public AMI root volume is treated as 8 GiB gp3.",
        ],
        "zero_direct_charge_resources": [
            "VPC, subnet, route table, internet gateway, security groups, IAM role, and CloudFormation have no separate hourly line item in this recipe.",
        ],
        "exclusions": _standard_exclusions() + [
            "Unexpected data transfer, retries, log ingestion, and resources outside the registered recipe are excluded.",
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
    return {
        **base,
        "status": "estimated",
        "confidence": "medium",
        "pricing_confidence": "high",
        "pricing_level": "Level A registered recipe",
        "recipe": "lambda_self_managed_s3_code_storage_cdk",
        "pricing_basis": "已登錄 Lambda self-managed S3 code storage CDK PoC recipe；用固定低/中/高用量和公開牌價試算。",
        "price_snapshot_date": "2026-07-31",
        "scenarios": scenarios,
        "expected_total_usd": scenarios["expected"]["total_usd"],
        "estimated_range_usd": {name: scenarios[name]["total_usd"] for name in ("low", "expected", "high")},
        "recommended_approval_ceiling_usd": _money(_round_up(high_total, Decimal("0.05"))),
        "approval_ceiling_basis": "高用量情境往上取到下一個 USD 0.05。",
        "verified_recipe_facts": [
            "Registered recipe creates one versioned S3 bucket and one Lambda function using S3ObjectStorageMode=REFERENCE.",
        ],
        "zero_direct_charge_resources": [
            "CloudFormation, IAM role, S3 bucket policy, and Lambda function configuration have no separate direct charge.",
        ],
        "exclusions": _standard_exclusions() + [
            "Unexpected data transfer, retries, CloudWatch log ingestion, and resources outside the registered recipe are excluded.",
        ],
        "sources": _quote_sources(
            "lambda_request", "lambda_x86_duration", "s3_standard_storage", "s3_tier1_request", "s3_tier2_request",
        ),
    }


def _build_generic_usage_quote(base: dict[str, Any], services: set[str], candidate: dict[str, Any]) -> dict[str, Any]:
    scenarios = {
        name: _price_generic_scenario(name, assumptions, services)
        for name, assumptions in GENERIC_USAGE_SCENARIOS.items()
    }
    high_total = Decimal(str(scenarios["high"]["total_usd"]))
    used_rate_keys = sorted(
        {
            item["rate_key"]
            for scenario in scenarios.values()
            for item in scenario.get("line_items", [])
            if item.get("rate_key")
        }
    )
    return {
        **base,
        "status": "estimated",
        "confidence": "medium",
        "pricing_confidence": "medium",
        "pricing_level": "Level B generic usage model",
        "recipe": "generic_usage_model",
        "deployable_recipe_registered": False,
        "pricing_basis": (
            "未找到 candidate-specific 成本 recipe，但已從 S2/IaC/文字線索抓到可計價 AWS 服務，"
            "因此用通用低/中/高 PoC 用量模型先產出可審核估價。"
        ),
        "price_snapshot_date": "2026-07-31",
        "detected_services": sorted(services),
        "service_detection_basis": _service_detection_basis(candidate),
        "scenarios": scenarios,
        "expected_total_usd": scenarios["expected"]["total_usd"],
        "estimated_range_usd": {name: scenarios[name]["total_usd"] for name in ("low", "expected", "high")},
        "recommended_approval_ceiling_usd": _money(max(_round_up(high_total, Decimal("0.05")), Decimal("0.05"))),
        "approval_ceiling_basis": "高用量情境往上取到下一個 USD 0.05；極小估價至少保留 USD 0.05 審查上限。",
        "verified_recipe_facts": [
            "This is an IaC/service-derived estimate, not a deployable Skill 4 recipe.",
            "A separate S4 deployment recipe is still required before any AWS resources can be created.",
        ],
        "zero_direct_charge_resources": [
            ZERO_DIRECT_CHARGE_SERVICES[service]
            for service in sorted(services)
            if service in ZERO_DIRECT_CHARGE_SERVICES
        ],
        "exclusions": _standard_exclusions() + [
            "Service dimensions not detected by S2/IaC are excluded.",
            "Provisioned capacity, NAT/data transfer, long-running compute, managed ingestion pipelines, and downstream analytics are excluded unless detected and modeled.",
            "Use AWS Pricing Calculator, CloudFormation estimate-template-cost, Infracost, or AWS Price List API for a stronger quote before a larger PoC.",
        ],
        "sources": _quote_sources(*used_rate_keys) + [
            {"url": AWS_PRICE_LIST_QUERY_API_URL, "purpose": "Future Level B enhancement: query current SKU prices programmatically"},
            {"url": AWS_CFN_ESTIMATE_URL, "purpose": "Future Level B enhancement: estimate monthly cost from CloudFormation templates"},
            {"url": AWS_PRICING_CALCULATOR_URL, "purpose": "Manual cross-check and formal estimate workflow"},
        ],
    }


def _price_s3_files_scenario(name: str, assumptions: dict[str, Decimal]) -> dict[str, Any]:
    hours = assumptions["hours"]
    active_gb = assumptions["active_gb"]
    items = [
        _line("ec2_t3_micro", hours, "hours", "hours x USD/instance-hour"),
        _line("ebs_gp3", Decimal("8") * hours / HOURS_PER_MONTH, "GB-month", "8 GiB x hours / 730 x USD/GB-month"),
        _line("s3_files_storage", active_gb * hours / HOURS_PER_MONTH, "GB-month", "active GB x hours / 730 x USD/GB-month"),
        _line("s3_files_write", assumptions["write_gb"], "GB", "write GB x USD/GB"),
        _line("s3_files_export_read", assumptions["export_read_gb"], "GB", "export/read GB x USD/GB"),
        _line("s3_files_small_read", assumptions["small_read_gb"], "GB", "small-read GB x USD/GB"),
        _line("s3_files_import_write", assumptions["import_write_gb"], "GB", "import/write GB x USD/GB"),
        _line("s3_standard_storage", active_gb * hours / HOURS_PER_MONTH, "GB-month", "stored GB x hours / 730 x USD/GB-month"),
        _line("s3_tier1_request", assumptions["tier1_requests"], "requests", "request count x USD/request"),
        _line("s3_tier2_request", assumptions["tier2_requests"], "requests", "request count x USD/request"),
    ]
    return _scenario(name, assumptions, items)


def _price_lambda_self_managed_scenario(name: str, assumptions: dict[str, Decimal]) -> dict[str, Any]:
    items = [
        _line("lambda_request", assumptions["lambda_requests"], "requests", "invocations x USD/request"),
        _line("lambda_x86_duration", assumptions["lambda_gb_seconds"], "GB-seconds", "allocated GB-seconds x USD/GB-second"),
        _line("s3_standard_storage", assumptions["artifact_gb"] * assumptions["hours"] / HOURS_PER_MONTH, "GB-month", "artifact GB x hours / 730 x USD/GB-month"),
        _line("s3_tier1_request", assumptions["s3_put_requests"], "requests", "PUT/COPY/POST/LIST count x USD/request"),
        _line("s3_tier2_request", assumptions["s3_get_requests"], "requests", "GET count x USD/request"),
    ]
    return _scenario(name, assumptions, items)


def _price_generic_scenario(name: str, assumptions: dict[str, Decimal], services: set[str]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    if "lambda" in services:
        items.extend(
            [
                _line("lambda_request", assumptions["requests"], "requests", "generic PoC Lambda requests x USD/request"),
                _line("lambda_x86_duration", assumptions["lambda_gb_seconds"], "GB-seconds", "generic PoC Lambda GB-seconds x USD/GB-second"),
                _line("cloudwatch_logs_ingestion", assumptions["log_gb"], "GB ingested", "generic PoC log GB x USD/GB"),
            ]
        )
    if "s3" in services:
        items.extend(
            [
                _line("s3_standard_storage", assumptions["storage_gb"] * assumptions["hours"] / HOURS_PER_MONTH, "GB-month", "generic PoC S3 GB x hours / 730 x USD/GB-month"),
                _line("s3_tier1_request", assumptions["requests"], "requests", "generic PoC S3 write/list requests x USD/request"),
                _line("s3_tier2_request", assumptions["requests"], "requests", "generic PoC S3 read requests x USD/request"),
            ]
        )
    if "glue" in services or "lakeformation" in services:
        items.extend(
            [
                _line("glue_data_catalog_object_month", assumptions["catalog_objects"] * assumptions["hours"] / HOURS_PER_MONTH, "object-month", "metadata objects x PoC hours / 730 x USD/object-month"),
                _line("glue_data_catalog_request", assumptions["catalog_requests"], "requests", "Data Catalog API requests x USD/request"),
            ]
        )
    if "dynamodb" in services:
        items.extend(
            [
                _line("dynamodb_write_request", assumptions["requests"], "write requests", "generic PoC write requests x USD/request"),
                _line("dynamodb_read_request", assumptions["requests"], "read requests", "generic PoC read requests x USD/request"),
            ]
        )
    if "sqs" in services:
        items.append(_line("sqs_request", assumptions["requests"], "requests", "generic PoC SQS requests x USD/request"))
    if "sns" in services:
        items.append(_line("sns_publish", assumptions["requests"], "requests", "generic PoC SNS publishes x USD/request"))
    if "athena" in services:
        items.append(_line("athena_scanned", assumptions["athena_tb_scanned"], "TB scanned", "generic PoC TB scanned x USD/TB"))
    return _scenario(name, assumptions, items)


def _scenario(name: str, assumptions: dict[str, Decimal], items: list[dict[str, Any]]) -> dict[str, Any]:
    total = sum((Decimal(str(item["subtotal_usd"])) for item in items), Decimal("0"))
    return {
        "scenario": name,
        "label": str(assumptions["label"]),
        "assumptions": {key: _number(value) for key, value in assumptions.items() if key != "label"},
        "line_items": items,
        "total_usd": _money(total),
        "display_total_usd": f"{total.quantize(Decimal('0.01'), rounding=ROUND_CEILING):.2f}",
    }


def _line(rate_key: str, quantity: Decimal, quantity_unit: str, formula: str) -> dict[str, Any]:
    rate = RATE_CARD[rate_key]
    subtotal = quantity * rate["rate"]
    return {
        "rate_key": rate_key,
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


def _detected_services(candidate: dict[str, Any]) -> set[str]:
    services: set[str] = set()
    scope = ((candidate.get("comparison_dimensions") or {}).get("technology_scope") or {})
    for service in scope.get("services_detected") or []:
        normalized = _normalize_service(str(service))
        if normalized:
            services.add(normalized)
    for resource_type in _iter_iac_resource_types(candidate):
        service = _service_from_resource_type(resource_type)
        if service:
            services.add(service)
    haystack = _candidate_text(candidate)
    for alias, service in SERVICE_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", haystack):
            services.add(service)
    return services


def _billable_generic_services(services: set[str]) -> set[str]:
    return services & {"lambda", "s3", "glue", "dynamodb", "sqs", "sns", "athena", "cloudwatch"}


def _candidate_text(candidate: dict[str, Any]) -> str:
    try:
        return json.dumps(candidate, ensure_ascii=False).lower()
    except (TypeError, ValueError):
        return " ".join(str(value) for value in candidate.values()).lower()


def _iter_iac_resource_types(candidate: dict[str, Any]) -> list[str]:
    values: list[str] = []
    stack = [candidate]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            for key, value in item.items():
                if str(key).lower() in {"type", "resource_type", "resourceType"} and isinstance(value, str):
                    if value.startswith("AWS::"):
                        values.append(value)
                stack.append(value)
        elif isinstance(item, list):
            stack.extend(item)
    return values


def _service_from_resource_type(resource_type: str) -> str | None:
    parts = resource_type.split("::")
    if len(parts) < 2 or parts[0] != "AWS":
        return None
    return _normalize_service(parts[1])


def _normalize_service(value: str) -> str | None:
    cleaned = value.strip().lower().replace("_", " ").replace("-", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    if cleaned in SERVICE_ALIASES:
        return SERVICE_ALIASES[cleaned]
    if cleaned == "s3files":
        return "s3"
    return None


def _service_detection_basis(candidate: dict[str, Any]) -> str:
    scope = ((candidate.get("comparison_dimensions") or {}).get("technology_scope") or {})
    if scope.get("services_detected"):
        return "S2 technology_scope.services_detected plus candidate text/IaC hints."
    if _iter_iac_resource_types(candidate):
        return "IaC resource types embedded in the candidate artifact."
    return "Candidate title, source URL, excerpts, and linked evidence text."


def _is_s3_files(candidate: dict[str, Any]) -> bool:
    haystack = _candidate_text(candidate)
    return "s3 files" in haystack or "launching-s3-files" in haystack


def _is_lambda_self_managed_storage(candidate: dict[str, Any]) -> bool:
    haystack = _candidate_text(candidate)
    return "self-managed" in haystack and ("lambda" in haystack or "function-code" in haystack)


def _quote_sources(*rate_keys: str) -> list[dict[str, str]]:
    seen: set[str] = set()
    sources: list[dict[str, str]] = []
    for rate_key in rate_keys:
        rate = RATE_CARD[rate_key]
        url = str(rate["source_url"])
        if url in seen:
            continue
        seen.add(url)
        sources.append({"url": url, "purpose": str(rate["source_basis"])})
    sources.append({"url": AWS_PRICE_LIST_DOC_URL, "purpose": "AWS Price List files/rate card interpretation"})
    return sources


def _standard_exclusions() -> list[str]:
    return [
        "Tax, private pricing, Savings Plans, credits, enterprise discounts, and Free Tier are excluded.",
        "This quote must be regenerated if the public pricing page changes or the quote expires.",
        "Actual billing must be checked separately after Skill 4, using Billing/Cost Explorer/CUR evidence when attributable.",
    ]


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
