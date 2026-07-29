"""S2: turn S1 evidence into a comparable decision board.

S2 does real comparison work, but deliberately stops before choosing a winner:
it normalizes every usable candidate into the same evidence dimensions, records
what is verified versus unknown, and exposes the precise questions a human must
answer before S3. It never fabricates a price, Region, business fit, or PoC
feasibility verdict.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import re
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


ALLOWED_S1_STATUSES = {"scanned", "scanned_with_gaps"}
GA_REQUIRED = "ga_evidence_required"
AWS_HOST_SUFFIXES = ("aws.amazon.com", "docs.aws.amazon.com")
FETCH_TIMEOUT_SECONDS = 15
MAX_LINKED_EVIDENCE_PER_CANDIDATE = 3
MAX_REGION_LOOKUP_RESULTS = 5
MAX_SOURCE_EXCERPTS_PER_DIMENSION = 3
DEFAULT_TARGET_REGION = "ap-southeast-1"
TARGET_REGION_LABELS = {"ap-southeast-1": "Asia Pacific (Singapore)"}
# An AWS feature statement that it is available in all commercial Regions is
# feature-level availability evidence for Singapore too. Keep this explicit:
# a broad "AWS Regions" statement alone is not sufficient.
COMMERCIAL_AWS_REGIONS = {"ap-southeast-1"}
ALL_COMMERCIAL_REGIONS_PATTERN = re.compile(
    r"\b(?:all|every)\s+(?:commercial\s+)?(?:aws\s+)?regions?\b|所有\s*(?:商業\s*)?(?:AWS\s*)?區域",
    re.IGNORECASE,
)
# This AWS-owned search API is only a discovery mechanism. Its result snippets
# never count as evidence; S2 separately fetches and validates every result URL.
AWS_OFFICIAL_SEARCH_ENDPOINT = "https://prod.search.marketing.aws.dev/api/v1/search"


@dataclass(frozen=True)
class CompareIssue:
    code: str
    message: str
    severity: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "severity": self.severity}


@dataclass
class CompareResult:
    comparison: dict[str, Any]
    issues: list[CompareIssue] = field(default_factory=list)

    @property
    def status(self) -> str:
        if any(issue.severity == "blocker" for issue in self.issues):
            return "blocked_s1_not_usable"
        if any(issue.severity == "error" for issue in self.issues):
            return "needs_revision"
        if not self.comparison["candidates"]:
            return "no_comparable_candidates"
        return "ready_for_human_shortlist"

    def to_dict(self) -> dict[str, Any]:
        payload = dict(self.comparison)
        payload["status"] = self.status
        payload["comparison_issues"] = [issue.to_dict() for issue in self.issues]
        return payload


def build_compare(scan: dict[str, Any]) -> CompareResult:
    """Normalize S1 candidates into one evidence-backed comparison artifact."""

    issues = _validate_s1(scan)
    comparison = _base_comparison(scan)
    if issues:
        return CompareResult(comparison, issues)

    discovery_ref = scan.get("discovery_request_ref") or scan.get("demand_card_ref") or {}
    ga_required = discovery_ref.get("maturity_requirement") == GA_REQUIRED
    target_region = str(discovery_ref.get("target_region") or scan.get("target_region") or DEFAULT_TARGET_REGION)
    for candidate in scan.get("candidates") or []:
        compared, exclusion_reason = _compare_candidate(candidate, ga_required, target_region, issues)
        if compared is None:
            comparison["excluded_candidates"].append(
                {
                    "candidate_id": candidate.get("candidate_id"),
                    "title": candidate.get("title"),
                    "reason": exclusion_reason,
                }
            )
            continue
        comparison["candidates"].append(compared)

    comparison["comparison_matrix"] = _comparison_matrix(comparison["candidates"])
    comparison["cross_candidate_findings"] = _cross_candidate_findings(comparison["candidates"])
    comparison["shortlist_policy"]["eligible_candidate_count"] = sum(
        1 for candidate in comparison["candidates"] if candidate["shortlist_eligibility"]["eligible"]
    )
    comparison["shortlist_policy"]["region_verified_candidate_count"] = sum(
        1
        for candidate in comparison["candidates"]
        if candidate["comparison_dimensions"]["target_region_eligibility"]["status"]
        == f"available_{target_region.replace('-', '_')}"
    )
    comparison["shortlist_policy"]["region_warning_candidate_count"] = (
        len(comparison["candidates"]) - comparison["shortlist_policy"]["region_verified_candidate_count"]
    )
    comparison["data_gaps"].extend(scan.get("data_gaps") or [])
    if not comparison["candidates"]:
        comparison["data_gaps"].append("No S1 candidate satisfied the S2 evidence contract.")
    return CompareResult(comparison, issues)


def _base_comparison(scan: dict[str, Any]) -> dict[str, Any]:
    demand_ref = scan.get("demand_card_ref") or {}
    discovery_ref = scan.get("discovery_request_ref") or {}
    direct_import = (scan.get("entry_point") or {}).get("type") == "direct_url_import"
    target_region = str(discovery_ref.get("target_region") or scan.get("target_region") or DEFAULT_TARGET_REGION)
    return {
        "schema_version": "s2.comparison.v2",
        "run_id": scan.get("run_id", "unknown-run"),
        "stage": "S2",
        "status": "draft",
        "compared_at": datetime.now(timezone.utc).isoformat(),
        "s1_artifact_ref": {
            "schema_version": scan.get("schema_version"),
            "stage": scan.get("stage"),
            "status": scan.get("status"),
            "scanned_at": scan.get("scanned_at"),
            "entry_point": (scan.get("entry_point") or {}).get("type", "technology_discovery"),
            "problem_statement_hint": discovery_ref.get("problem_statement_hint", demand_ref.get("problem_statement", "")),
            "desired_outcome_hint": discovery_ref.get("desired_outcome_hint", demand_ref.get("desired_outcome", "")),
            "maturity_requirement": discovery_ref.get("maturity_requirement", demand_ref.get("maturity_requirement", "not_requested_for_direct_import")),
            "target_region": target_region,
        },
        "comparison_contract": {
            "method": "normalized_source_backed_comparison_without_automatic_ranking",
            "automatic_shortlist": False,
            "maximum_human_shortlist_size": 3,
            "required_dimensions": [
                "technology_scope",
                "delivery_model",
                "source_backed_capabilities",
                "environment_signals",
                "maturity",
                "official_docs_pricing_region_evidence",
                "business_context",
                "unknowns_and_next_validation_question",
            ],
            "direct_import_limit": (
                "No S0 context exists for this artifact; S2 can compare technical evidence only."
                if direct_import
                else None
            ),
        },
        "candidates": [],
        "excluded_candidates": [],
        "comparison_matrix": [],
        "cross_candidate_findings": {},
        "data_gaps": [],
        "human_review_required": {
            "decision": "Choose at most three evidence-backed candidates for S3, and record the reason for each selection.",
            "required_inputs": [
                "Which concrete business or engineering problem matters now?",
                "Which existing non-production environment is available for safe validation?",
                "Which data, permissions, and governance boundaries must not be touched?",
                "What is the candidate's Region status, and must paid PoC support be deferred until S4?",
            ],
        },
        "shortlist_policy": {
            "target_region": target_region,
            "target_region_label": TARGET_REGION_LABELS.get(target_region, target_region),
            "rule": "Target Region evidence is recorded as a warning/status in S2 and does not block S3. Paid PoC still requires feature-level official target Region evidence.",
            "eligible_candidate_count": 0,
            "region_verified_candidate_count": 0,
            "region_warning_candidate_count": 0,
        },
        "notes": [
            "A populated field is source-backed or a transparent rule-based classification; it is not an LLM-generated product claim.",
            "Unknown means the fetched sources did not establish the fact. It is a required follow-up, not a negative conclusion.",
            "S2 creates decision material. It does not recommend a winner, create cloud resources, or authorize a PoC.",
        ],
    }


def _validate_s1(scan: dict[str, Any]) -> list[CompareIssue]:
    if scan.get("stage") != "S1" or scan.get("status") not in ALLOWED_S1_STATUSES:
        return [
            CompareIssue(
                "s1_not_usable",
                "S2 requires an S1 artifact with status scanned or scanned_with_gaps.",
                "blocker",
            )
        ]
    return []


def _compare_candidate(
    candidate: dict[str, Any], ga_required: bool, target_region: str, issues: list[CompareIssue]
) -> tuple[dict[str, Any] | None, str]:
    if not candidate.get("external_fetch_performed"):
        return None, "S1 did not fetch this candidate from an external public source."
    if not candidate.get("official_source") and not candidate.get("open_source"):
        return None, "S2 accepts only official AWS or traceable public open-source candidates."

    maturity = candidate.get("maturity_evidence") or {}
    if ga_required and maturity.get("status") != "official_ga_evidence_found":
        return None, "This scan requires official GA evidence, but this candidate does not contain it."

    source_evidence = _collect_source_evidence(candidate, target_region, issues)
    excerpts = _source_excerpts(candidate)
    technology_scope = list(candidate.get("related_aws_services") or [])
    delivery_model = _delivery_model(candidate, excerpts)
    environment_signals = _environment_signals(excerpts)
    business_context = _business_context(candidate)
    region_eligibility = _region_eligibility(candidate, source_evidence, target_region)
    evidence_coverage = _evidence_coverage(candidate, source_evidence, business_context)
    unknowns = _unknowns(candidate, source_evidence, business_context)
    dimensions = {
        "technology_scope": {
            "services_detected": technology_scope,
            "basis": "S1 service detector applied to the fetched page text.",
            "status": "source_detected" if technology_scope else "not_detected_from_source",
        },
        "delivery_model": delivery_model,
        "source_backed_capabilities": {
            "excerpts": excerpts["capabilities"],
            "basis": "Sentences retained from the S1-fetched source; no capability was invented by S2.",
            "status": "source_excerpt_available" if excerpts["capabilities"] else "not_extracted_from_source",
        },
        "environment_signals": environment_signals,
        "maturity": {
            "status": maturity.get("status", "not_requested"),
            "evidence_excerpts": maturity.get("evidence_excerpts") or [],
            "basis": maturity.get("evidence_basis", "not_available"),
        },
        "official_docs_pricing_region_evidence": _official_evidence_summary(source_evidence),
        "target_region_eligibility": region_eligibility,
        "business_context": business_context,
        "unknowns_and_next_validation_question": {
            "unknowns": unknowns,
            "next_question": _next_validation_question(
                technology_scope, delivery_model, environment_signals, business_context
            ),
        },
    }

    return {
        "candidate_id": candidate.get("candidate_id"),
        "title": candidate.get("title"),
        "source_url": candidate.get("source_url"),
        "source_category": (candidate.get("rss_source") or {}).get("feed_name"),
        "published_at": (candidate.get("rss_source") or {}).get("feed_item_published_at"),
        "source_provenance": {
            "official_aws_source": bool(candidate.get("official_source")),
            "public_open_source": bool(candidate.get("open_source")),
            "external_fetch_performed": True,
            "source_selection": candidate.get("source_selection"),
        },
        "comparison_dimensions": dimensions,
        "shortlist_eligibility": {
            "eligible": True,
            "reason": region_eligibility["shortlist_reason"],
        },
        "proposal_card": _proposal_card(candidate, dimensions, source_evidence, evidence_coverage),
        "evidence_coverage": evidence_coverage,
        "linked_evidence": source_evidence,
        "evidence_limits": list(candidate.get("data_gaps") or []) + list(source_evidence.get("data_gaps") or []),
    }, ""


def _collect_source_evidence(
    candidate: dict[str, Any], target_region: str, issues: list[CompareIssue]
) -> dict[str, Any]:
    """Collect source-linked and official-search evidence for one AWS candidate.

    A direct open-source import is already a traceable primary source. S2 does
    not pretend that a GitHub project has AWS pricing or GA evidence.

    The second path deliberately fixes a coverage limitation in the first S2
    version: a launch article need not link to its feature's Region document.
    AWS search supplies discovery URLs only. A result can upgrade Region status
    only after its official page is fetched and a candidate-specific passage
    explicitly names the target Region.
    """

    if not candidate.get("official_source"):
        return {
            "primary_source": {"url": candidate.get("source_url"), "status": "fetched_in_s1"},
            "linked_sources": [],
            "target_region_evidence": _no_region_evidence(target_region, "Non-official primary sources cannot prove AWS feature availability."),
            "data_gaps": [
                "This is not an official AWS source; S2 did not treat it as proof of AWS pricing, Region availability, or GA status."
            ],
        }

    source_url = str(candidate.get("source_url") or "")
    linked_sources: list[dict[str, Any]] = []
    region_matches: list[str] = []
    data_gaps: list[str] = []
    primary_source: dict[str, Any] = {"url": source_url, "status": "refetch_pending"}
    seen_urls = {source_url}
    try:
        source = _fetch_official_page(source_url)
    except Exception as exc:
        issues.append(CompareIssue("s2_source_refetch_failed", f"{source_url}: {exc}", "warning"))
        primary_source["status"] = "refetch_failed"
        data_gaps.append("S2 could not re-fetch the official S1 source to discover source-linked evidence.")
    else:
        primary_source = {
            "url": source_url,
            "final_url": source["final_url"],
            "title": source["title"],
            "status": "refetched",
        }
        seen_urls.add(source["final_url"])
        region_matches.extend(_target_region_matches(source["text"], target_region, candidate))
        for link in _select_linked_evidence(source["links"], candidate):
            evidence = _fetch_evidence_record(link, candidate, target_region, "source_link", issues)
            linked_sources.append(evidence)
            seen_urls.add(link["url"])
            if evidence.get("final_url"):
                seen_urls.add(evidence["final_url"])
            region_matches.extend(evidence.get("target_region_matches") or [])

    lookup_sources, lookup = _lookup_candidate_region_evidence(candidate, target_region, seen_urls, issues)
    linked_sources.extend(lookup_sources)
    for evidence in lookup_sources:
        region_matches.extend(evidence.get("target_region_matches") or [])

    found_types = {item.get("evidence_type") for item in linked_sources if item.get("status") == "fetched"}
    for evidence_type, label in (
        ("aws_docs", "documentation"),
        ("aws_pricing", "pricing"),
        ("region_availability", "Region or availability"),
    ):
        if evidence_type not in found_types:
            data_gaps.append(f"No candidate-relevant official AWS {label} page was fetched in this S2 run.")
    return {
        "primary_source": primary_source,
        "linked_sources": linked_sources,
        "official_region_lookup": lookup,
        "target_region_evidence": {
            "target_region": target_region,
            "target_region_label": TARGET_REGION_LABELS.get(target_region, target_region),
            "official_source_matches": region_matches[:6],
            "status": "official_region_text_found" if region_matches else "no_feature_level_region_evidence_found",
        },
        "data_gaps": data_gaps,
    }


def _fetch_evidence_record(
    source: dict[str, Any], candidate: dict[str, Any], target_region: str, discovery_method: str, issues: list[CompareIssue]
) -> dict[str, Any]:
    """Fetch one discovered official URL and preserve how S2 found it."""

    try:
        fetched = _fetch_official_page(str(source["url"]))
    except Exception as exc:
        issues.append(CompareIssue("linked_evidence_fetch_failed", f"{source['url']}: {exc}", "warning"))
        return {**source, "discovery_method": discovery_method, "status": "fetch_failed"}
    return {
        **source,
        "discovery_method": discovery_method,
        "evidence_type": source.get("evidence_type") or _evidence_type_for_url(fetched["final_url"]) or "candidate_feature_page",
        "status": "fetched",
        "final_url": fetched["final_url"],
        "title": fetched["title"],
        "description": fetched["description"],
        "text_excerpt": fetched["text"][:1_200],
        "target_region_matches": _target_region_matches(fetched["text"], target_region, candidate),
    }


def _lookup_candidate_region_evidence(
    candidate: dict[str, Any], target_region: str, seen_urls: set[str], issues: list[CompareIssue]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Use AWS's public search index to find official pages S1 did not link.

    The returned records contain the query, rank, provider and URL for audit.
    The search API response is never copied into evidence excerpts or used by
    the gate; only the fetched final AWS page can produce a Region match.
    """

    target_label = TARGET_REGION_LABELS.get(target_region, target_region)
    query_terms = _candidate_region_terms(str(candidate.get("title") or ""))[:8]
    # Search for the feature first. Adding a Region marker here makes AWS's
    # broad public index over-rank unrelated Singapore and endpoint pages.
    # Region eligibility is deliberately decided only from fetched page text.
    query = " ".join(query_terms).strip()
    lookup: dict[str, Any] = {
        "method": "aws_official_search_then_fetch",
        "search_endpoint": AWS_OFFICIAL_SEARCH_ENDPOINT,
        "query": query,
        "target_region": target_region,
        "query_purpose": "Find candidate-specific official pages before checking the target Region in fetched text.",
        "search_result_count": 0,
        "selected_result_count": 0,
        "status": "pending",
        "evidence_rule": "Search snippets are discovery metadata only. Only a separately fetched AWS official page with a candidate-specific Region passage can upgrade Region status.",
    }
    if not query_terms:
        lookup["status"] = "skipped_no_candidate_terms"
        return [], lookup

    body = json.dumps(
        {
            "query": {"text": query, "locale": "en-US", "pagination": {"offset": 0, "limit": MAX_REGION_LOOKUP_RESULTS}},
            "providers": [{"name": "docs"}, {"name": "pages"}, {"name": "blogs"}],
        }
    ).encode("utf-8")
    request = Request(
        AWS_OFFICIAL_SEARCH_ENDPOINT,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "agentic-cloud-radar/1.0 (S2 Region evidence lookup)"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        issues.append(CompareIssue("official_region_lookup_failed", f"{candidate.get('title')}: {exc}", "warning"))
        lookup["status"] = "search_failed"
        return [], lookup

    results = payload.get("results") or []
    lookup["search_result_count"] = len(results)
    selected: list[dict[str, Any]] = []
    for rank, result in enumerate(results, start=1):
        url = str(result.get("url") or "")
        result_title = str(result.get("title") or "")
        if (
            not _is_official_aws_url(url)
            or url in seen_urls
            or not _is_feature_specific_region_passage(f"{result_title} {url}".lower(), query_terms)
        ):
            continue
        selected.append(
            {
                "url": url,
                "link_text": str(result.get("title") or ""),
                "search_rank": rank,
                "search_provider": str(result.get("provider") or "unknown"),
            }
        )
        seen_urls.add(url)
    lookup["selected_result_count"] = len(selected)
    lookup["status"] = "search_completed" if selected else "search_completed_no_new_official_pages"
    return [
        _fetch_evidence_record(result, candidate, target_region, "official_aws_search", issues) for result in selected
    ], lookup


def _no_region_evidence(target_region: str, reason: str) -> dict[str, Any]:
    return {
        "target_region": target_region,
        "target_region_label": TARGET_REGION_LABELS.get(target_region, target_region),
        "official_source_matches": [],
        "status": "no_feature_level_region_evidence_found",
        "reason": reason,
    }


def _target_region_matches(
    source_text: str, target_region: str, candidate: dict[str, Any]
) -> list[str]:
    """Keep only a target-Region passage that also names this specific feature.

    A regional table for unrelated Local Zones or an AWS navigation list is not
    enough. A target-Region mention needs at least two non-generic title terms
    in the same extracted text block. An explicit "all commercial AWS Regions"
    statement is also accepted for a known commercial target Region, but only
    when the same passage mentions a service detected for this candidate.
    """

    label = TARGET_REGION_LABELS.get(target_region, target_region)
    markers = (target_region.lower(), label.lower(), "singapore")
    title_terms = _candidate_region_terms(str(candidate.get("title") or ""))
    passages = re.split(r"(?:[.!?]\s+|\n+)", source_text)
    return [
        passage.strip()[:500]
        for passage in passages
        if _is_target_region_passage(passage, markers, title_terms, target_region, candidate)
    ][:3]


def _is_target_region_passage(
    passage: str,
    markers: tuple[str, ...],
    title_terms: list[str],
    target_region: str,
    candidate: dict[str, Any],
) -> bool:
    """Decide whether one sentence proves availability for this candidate."""

    lowered = passage.lower()
    if any(marker in lowered for marker in markers):
        return _is_feature_specific_region_passage(lowered, title_terms)
    if target_region not in COMMERCIAL_AWS_REGIONS or not ALL_COMMERCIAL_REGIONS_PATTERN.search(lowered):
        return False
    return _mentions_candidate_service(lowered, candidate)


def _mentions_candidate_service(passage: str, candidate: dict[str, Any]) -> bool:
    """Require the global availability statement to name a candidate service."""

    services = [str(service).lower() for service in candidate.get("related_aws_services") or []]
    return any(re.search(rf"\b{re.escape(service)}\b", passage) for service in services)


def _candidate_region_terms(title: str) -> list[str]:
    ignored = {"amazon", "announcing", "available", "aws", "blog", "from", "general", "in", "is", "lets", "new", "now", "of", "on", "the", "to", "with"}
    terms = re.findall(r"[a-z0-9][a-z0-9-]{2,}", title.lower())
    return [term for term in dict.fromkeys(terms) if term not in ignored]


def _is_feature_specific_region_passage(passage: str, title_terms: list[str]) -> bool:
    matched = [term for term in title_terms if re.search(rf"\b{re.escape(term)}\b", passage)]
    return len(matched) >= 2 and any(term not in {"local", "zone", "zones"} for term in matched)


def _region_eligibility(
    candidate: dict[str, Any], source_evidence: dict[str, Any], target_region: str
) -> dict[str, Any]:
    evidence = source_evidence.get("target_region_evidence") or _no_region_evidence(target_region, "No Region check was recorded.")
    has_feature_level_evidence = (
        bool(candidate.get("official_source"))
        and evidence.get("status") == "official_region_text_found"
    )
    if has_feature_level_evidence:
        available_status = f"available_{target_region.replace('-', '_')}"
        return {
            "target_region": target_region,
            "target_region_label": TARGET_REGION_LABELS.get(target_region, target_region),
            "status": available_status,
            "evidence_excerpts": evidence.get("official_source_matches") or [],
            "severity": "info",
            "blocks_s3": False,
            "blocks_paid_poc": False,
            "shortlist_reason": "Official candidate-specific source evidence covers the target Region directly or through an all-commercial-Regions statement.",
            "paid_poc_requirement": "Already satisfies the S2 Region evidence precondition for later paid PoC review.",
        }
    return {
        "target_region": target_region,
        "target_region_label": TARGET_REGION_LABELS.get(target_region, target_region),
        "status": "region_unknown",
        "evidence_excerpts": evidence.get("official_source_matches") or [],
        "severity": "warning",
        "blocks_s3": False,
        "blocks_paid_poc": True,
        "shortlist_reason": "Region support is not proven by S2, but this is a warning rather than an S3 blocker.",
        "paid_poc_requirement": "Before a paid PoC, S4 must prove feature-level target Region support or downgrade to low-risk/local/document validation.",
    }


def _source_excerpts(candidate: dict[str, Any]) -> dict[str, list[str]]:
    """Classify S1-extracted sentences; output remains verbatim source material."""

    claims = [str(item).strip() for item in candidate.get("initial_claims") or [] if str(item).strip()]
    capability_markers = ("support", "enable", "allow", "provide", "build", "operate", "run", "access", "integrate")
    environment_markers = ("region", "local zone", "hybrid", "on-prem", "edge", "desktop", "swift", "sap", "abap", "kubernetes", "device", "instance")
    capabilities = [claim for claim in claims if any(marker in claim.lower() for marker in capability_markers)]
    environments = [claim for claim in claims if any(marker in claim.lower() for marker in environment_markers)]
    return {
        "capabilities": (capabilities or claims)[:MAX_SOURCE_EXCERPTS_PER_DIMENSION],
        "environment": environments[:MAX_SOURCE_EXCERPTS_PER_DIMENSION],
    }


def _delivery_model(candidate: dict[str, Any], excerpts: dict[str, list[str]]) -> dict[str, Any]:
    text = " ".join([str(candidate.get("title") or ""), *excerpts["capabilities"]]).lower()
    rules = (
        ("sdk_or_client_library", ("sdk", "client library")),
        ("managed_desktop_application_environment", ("workspaces", "desktop application")),
        ("compute_instance_family", ("instance", "graviton")),
        ("hybrid_infrastructure_feature", ("hybrid", "on-prem", "edge")),
        ("regional_infrastructure_extension", ("local zone",)),
        ("developer_tooling_or_ide_integration", ("mcp", "ide", "abap")),
        ("managed_cloud_service_or_feature", ("aws",)),
    )
    for label, markers in rules:
        if any(marker in text for marker in markers):
            return {
                "classification": label,
                "basis": f"Rule-based classification from source terms: {', '.join(marker for marker in markers if marker in text)}.",
                "source_excerpts": excerpts["capabilities"],
            }
    return {
        "classification": "not_classified_from_source",
        "basis": "The fetched source did not contain a supported delivery-model signal.",
        "source_excerpts": excerpts["capabilities"],
    }


def _environment_signals(excerpts: dict[str, list[str]]) -> dict[str, Any]:
    text = " ".join(excerpts["environment"]).lower()
    rules = (
        ("regional_or_locality_context", ("region", "local zone", "latency", "residency")),
        ("existing_compute_workload", ("instance", "graviton", "compute")),
        ("desktop_application_workflow", ("desktop", "workspaces")),
        ("device_or_mobile_development", ("device", "swift", "iot")),
        ("sap_abap_development_context", ("sap", "abap")),
        ("hybrid_or_kubernetes_environment", ("hybrid", "kubernetes", "on-prem", "edge", "eks")),
    )
    detected = [label for label, markers in rules if any(marker in text for marker in markers)]
    return {
        "source_indicated_contexts": detected,
        "source_excerpts": excerpts["environment"],
        "interpretation_limit": "These are source signals, not proof that the company has the required environment.",
    }


def _business_context(candidate: dict[str, Any]) -> dict[str, Any]:
    contexts = list(candidate.get("possible_application_contexts") or [])
    if contexts:
        return {
            "status": "unconfirmed_discovery_hint",
            "contexts": contexts,
            "required_human_input": "Turn the scan hint into a candidate-specific problem, target user, baseline, and success measure.",
        }
    return {
        "status": "unknown_no_problem_context",
        "contexts": [],
        "required_human_input": "State the problem, target user, and success measure before treating technical evidence as business fit.",
    }


def _evidence_coverage(
    candidate: dict[str, Any], source_evidence: dict[str, Any], business_context: dict[str, Any]
) -> dict[str, Any]:
    sources = source_evidence.get("linked_sources") or []
    found = {item.get("evidence_type") for item in sources if item.get("status") == "fetched"}
    coverage = {
        "primary_source_fetched": bool(candidate.get("external_fetch_performed")),
        "official_aws_primary_source": bool(candidate.get("official_source")),
        "public_open_source_primary_source": bool(candidate.get("open_source")),
        "official_ga_evidence": (candidate.get("maturity_evidence") or {}).get("status") == "official_ga_evidence_found",
        "official_docs_linked": "aws_docs" in found,
        "official_pricing_linked": "aws_pricing" in found,
        "official_region_or_availability_linked": "region_availability" in found,
        "business_context_available": business_context["status"] == "candidate_problem_confirmed",
    }
    coverage["verified_dimension_count"] = sum(bool(value) for value in coverage.values())
    coverage["verified_dimension_total"] = 8
    return coverage


def _unknowns(
    candidate: dict[str, Any], source_evidence: dict[str, Any], business_context: dict[str, Any]
) -> list[str]:
    unknowns: list[str] = []
    if business_context["status"] != "candidate_problem_confirmed":
        unknowns.append("Business fit is unknown until a reviewer confirms a candidate-specific problem, target user, baseline, and success measure.")
    if not candidate.get("related_aws_services"):
        unknowns.append("No supported AWS service name was detected from the fetched source text.")
    sources = source_evidence.get("linked_sources") or []
    types = {item.get("evidence_type") for item in sources if item.get("status") == "fetched"}
    if "aws_pricing" not in types:
        unknowns.append("Official pricing evidence has not been established for this candidate.")
    if "region_availability" not in types:
        unknowns.append("Supported Region or availability evidence has not been established for this candidate.")
    region_evidence = source_evidence.get("target_region_evidence") or {}
    if region_evidence.get("status") != "official_region_text_found":
        unknowns.append(
            f"Feature-level availability in {region_evidence.get('target_region', DEFAULT_TARGET_REGION)} has not been officially verified; this warns S3 but blocks only paid S4 PoC."
        )
    if not candidate.get("official_source"):
        unknowns.append("AWS GA status cannot be proven from this non-official primary source.")
    unknowns.append("Permissions, cleanup plan, and USD 3 PoC feasibility require a selected environment and S3/S4 validation.")
    return unknowns


def _proposal_card(
    candidate: dict[str, Any],
    dimensions: dict[str, Any],
    source_evidence: dict[str, Any],
    evidence_coverage: dict[str, Any],
) -> dict[str, Any]:
    """Fold S0's useful questions into a candidate-specific, honest proposal card.

    The card is a proposal hypothesis, not an assertion that the company has a
    problem or will achieve an improvement. Its fields make that distinction
    reviewable instead of burying it in prose.
    """

    capability_excerpts = dimensions["source_backed_capabilities"]["excerpts"]
    delivery_model = dimensions["delivery_model"]["classification"]
    improvement_vectors = _improvement_vectors(candidate, capability_excerpts)
    tradeoffs = _planning_tradeoffs(delivery_model, dimensions["environment_signals"])
    metrics = _validation_metrics(improvement_vectors)
    proposal_indicators = _proposal_indicators(
        dimensions, evidence_coverage, improvement_vectors, tradeoffs
    )
    services = dimensions["technology_scope"]["services_detected"]
    service_label = ", ".join(services) if services else candidate.get("title")
    return {
        "proposal_status": "candidate_hypothesis_requires_human_problem_selection",
        "candidate_opportunity": {
            "technology": candidate.get("title"),
            "technology_scope": services,
            "source_backed_mechanism": capability_excerpts,
            "plain_language": f"Evaluate whether {service_label} can improve one explicitly chosen workflow through {delivery_model}.",
        },
        "problem_definition_to_confirm": {
            "current_state": "Unknown: S1 discovers technology and does not assume a company pain point.",
            "target_user": "Unknown: choose a real user or engineering owner before S3.",
            "required_human_question": f"Which current workflow would {candidate.get('title')} change, and what is its measurable baseline?",
        },
        "improvement_hypothesis": {
            "baseline_to_change": "A before/after claim cannot be made until a current workflow baseline is measured.",
            "potential_vectors": improvement_vectors,
            "improvement_degree": _improvement_degree(capability_excerpts),
            "interpretation_limit": "Potential improvement is a proposal hypothesis. Only source quotes or a later measured baseline can support a stronger claim.",
        },
        "benefits": [
            {
                "benefit_type": vector["type"],
                "why_it_is_considered": vector["reason"],
                "source_support": vector["source_support"],
            }
            for vector in improvement_vectors
        ],
        "tradeoffs_and_risks": tradeoffs,
        "proposal_indicators": proposal_indicators,
        "validation_design": {
            "before_measurements": metrics["before"],
            "after_measurements": metrics["after"],
            "minimum_success_evidence": metrics["success"],
            "stop_conditions": [
                "No safe non-production environment or required permission is available.",
                "Official pricing or cleanup cannot be bounded within the USD 3 cap.",
                "No measurable baseline exists for the proposed workflow.",
            ],
            "next_stage_question": dimensions["unknowns_and_next_validation_question"]["next_question"],
        },
        "source_and_evidence_boundary": {
            "primary_source": candidate.get("source_url"),
            "linked_evidence_count": len(source_evidence.get("linked_sources") or []),
            "verified_dimension_count": evidence_coverage["verified_dimension_count"],
            "verified_dimension_total": evidence_coverage["verified_dimension_total"],
        },
        "target_region_gate": dimensions["target_region_eligibility"],
    }


def _improvement_vectors(candidate: dict[str, Any], excerpts: list[str]) -> list[dict[str, Any]]:
    """Map source terms to *possible* value vectors without assigning a score."""

    text = " ".join([str(candidate.get("title") or ""), *excerpts]).lower()
    rules = (
        ("performance_or_latency", ("performance", "latency", "faster", "graviton", "local zone"), "The source contains performance, latency, locality, or compute-efficiency terms."),
        ("workflow_automation", ("agent", "automate", "automation", "workflow", "operate"), "The source contains agent, automation, workflow, or operation terms."),
        ("developer_productivity", ("sdk", "ide", "mcp", "developer", "abap"), "The source contains SDK, IDE, MCP, or developer-workflow terms."),
        ("deployment_or_integration_reach", ("hybrid", "on-prem", "edge", "integrate", "device", "swift"), "The source contains hybrid, integration, device, or edge terms."),
        ("cost_or_resource_efficiency", ("cost", "efficient", "efficiency", "graviton"), "The source contains cost or efficiency terms; this is not a price calculation."),
    )
    matched = [
        {"type": kind, "reason": reason, "source_support": [excerpt for excerpt in excerpts if any(marker in excerpt.lower() for marker in markers)][:2]}
        for kind, markers, reason in rules
        if any(marker in text for marker in markers)
    ]
    if matched:
        return matched
    return [
        {
            "type": "technology_capability_only",
            "reason": "The fetched source establishes a technology candidate but did not contain a supported improvement-vector term.",
            "source_support": excerpts[:2],
        }
    ]


def _improvement_degree(excerpts: list[str]) -> dict[str, Any]:
    text = " ".join(excerpts)
    quantified = re.findall(r"\b\d+(?:\.\d+)?\s*(?:%|x|times|ms|seconds?|minutes?)\b", text, flags=re.IGNORECASE)
    if quantified:
        return {
            "status": "source_contains_quantified_claim",
            "source_numbers": quantified[:5],
            "limit": "A source number is not a company result; S3/S4 must measure the same metric against a local baseline.",
        }
    return {
        "status": "qualitative_hypothesis_only",
        "source_numbers": [],
        "limit": "No comparable improvement magnitude was found in the retained source excerpts.",
    }


def _planning_tradeoffs(delivery_model: str, environment_signals: dict[str, Any]) -> list[dict[str, str]]:
    """Expose operational tradeoffs as labelled planning inferences, never source facts."""

    tradeoffs = [
        {
            "type": "evidence_and_cost_gap",
            "status": "requires_verification",
            "detail": "Pricing, Region availability, permissions, and cleanup have not yet been proven by the comparison card.",
        }
    ]
    model_tradeoffs = {
        "compute_instance_family": ("benchmark_dependency", "A useful comparison needs a representative existing workload and a baseline instance."),
        "hybrid_infrastructure_feature": ("environment_dependency", "Hybrid validation depends on network, identity, and operational-boundary evidence."),
        "managed_desktop_application_environment": ("governance_dependency", "Desktop automation needs a permitted workflow and explicit user-control or governance checks."),
        "sdk_or_client_library": ("integration_dependency", "SDK evaluation needs a compatible application or device scenario, not only an API call."),
        "developer_tooling_or_ide_integration": ("developer_workflow_dependency", "Developer tooling needs a safe code or documentation context and an observable workflow metric."),
        "regional_infrastructure_extension": ("locality_dependency", "A locality feature needs a real latency, residency, or geographic-reach need to justify evaluation."),
    }
    if delivery_model in model_tradeoffs:
        kind, detail = model_tradeoffs[delivery_model]
        tradeoffs.append({"type": kind, "status": "planning_inference", "detail": detail})
    if not environment_signals["source_indicated_contexts"]:
        tradeoffs.append({"type": "environment_unknown", "status": "requires_human_context", "detail": "The source did not expose a clear environment signal; identify the actual validation setting before S3."})
    return tradeoffs


def _validation_metrics(improvement_vectors: list[dict[str, Any]]) -> dict[str, list[str]]:
    types = {item["type"] for item in improvement_vectors}
    before = ["Current workflow steps, elapsed time, and manual handoffs."]
    after = ["Same workflow steps, elapsed time, and observed failure or rollback behaviour."]
    success = ["A pre-agreed before/after comparison using the same non-production workload."]
    if "performance_or_latency" in types:
        before.append("Baseline latency, throughput, or workload completion time.")
        after.append("Latency, throughput, or completion time under the same workload.")
    if "workflow_automation" in types:
        before.append("Manual touchpoints and task completion rate.")
        after.append("Automated task completion rate, user intervention, and recovery path.")
    if "developer_productivity" in types:
        before.append("Time and steps needed to find or apply technical guidance.")
        after.append("Time, steps, and correction rate with the proposed developer workflow.")
    if "cost_or_resource_efficiency" in types:
        before.append("Officially priced baseline configuration and observed resource use.")
        after.append("Officially priced comparison configuration and observed resource use.")
    return {"before": before, "after": after, "success": success}


def _proposal_indicators(
    dimensions: dict[str, Any],
    coverage: dict[str, Any],
    improvement_vectors: list[dict[str, Any]],
    tradeoffs: list[dict[str, str]],
) -> dict[str, Any]:
    """Non-ranked indicators let reviewers compare readiness without a fake score."""

    return {
        "improvement_hypothesis_visibility": "source_terms_present" if improvement_vectors[0]["type"] != "technology_capability_only" else "needs_human_hypothesis",
        "maturity_evidence": dimensions["maturity"]["status"],
        "evidence_completeness": f"{coverage['verified_dimension_count']}/{coverage['verified_dimension_total']} dimensions source-verified",
        "financial_certainty": "official_pricing_linked" if coverage["official_pricing_linked"] else "pricing_not_yet_verified",
        "environment_dependency": "source_indicated" if dimensions["environment_signals"]["source_indicated_contexts"] else "unknown",
        "target_region_eligibility": dimensions["target_region_eligibility"]["status"],
        "validation_risk_count": sum(1 for item in tradeoffs if item["status"] != "planning_inference"),
        "automatic_rank": "intentionally_not_calculated",
    }


def _next_validation_question(
    services: list[str], delivery_model: dict[str, Any], environment_signals: dict[str, Any], business_context: dict[str, Any]
) -> str:
    service_label = ", ".join(services) if services else "this candidate"
    model = delivery_model["classification"]
    environment = ", ".join(environment_signals["source_indicated_contexts"]) or "the required environment"
    if business_context["status"] != "candidate_problem_confirmed":
        return f"Before comparing {service_label}, which real problem and target user would justify validating {model} in {environment}?"
    return f"For {service_label}, is a safe non-production {environment} available to validate {model}, pricing, permissions, and cleanup?"


def _official_evidence_summary(source_evidence: dict[str, Any]) -> dict[str, Any]:
    sources = source_evidence.get("linked_sources") or []
    fetched = [item for item in sources if item.get("status") == "fetched"]
    return {
        "primary_source_status": (source_evidence.get("primary_source") or {}).get("status"),
        "linked_docs": [item for item in fetched if item.get("evidence_type") == "aws_docs"],
        "linked_pricing": [item for item in fetched if item.get("evidence_type") == "aws_pricing"],
        "linked_region_or_availability": [item for item in fetched if item.get("evidence_type") == "region_availability"],
        "interpretation_limit": "A fetched page records evidence availability only; it does not calculate a cost or prove company-environment compatibility.",
    }


def _comparison_matrix(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create stable columns so a reviewer can compare candidates without reading nested JSON."""

    rows = []
    for candidate in candidates:
        dimensions = candidate["comparison_dimensions"]
        coverage = candidate["evidence_coverage"]
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "title": candidate["title"],
                "technology_scope": dimensions["technology_scope"]["services_detected"],
                "delivery_model": dimensions["delivery_model"]["classification"],
                "maturity": dimensions["maturity"]["status"],
                "environment_signals": dimensions["environment_signals"]["source_indicated_contexts"],
                "business_context": dimensions["business_context"]["status"],
                "docs_evidence": coverage["official_docs_linked"],
                "pricing_evidence": coverage["official_pricing_linked"],
                "region_evidence": coverage["official_region_or_availability_linked"],
                "target_region": dimensions["target_region_eligibility"]["target_region"],
                "target_region_status": dimensions["target_region_eligibility"]["status"],
                "shortlist_eligible": candidate["shortlist_eligibility"]["eligible"],
                "verified_dimension_count": coverage["verified_dimension_count"],
                "decisive_unknowns": dimensions["unknowns_and_next_validation_question"]["unknowns"][:3],
            }
        )
    return rows


def _cross_candidate_findings(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    service_counts = Counter(
        service
        for candidate in candidates
        for service in candidate["comparison_dimensions"]["technology_scope"]["services_detected"]
    )
    model_counts = Counter(
        candidate["comparison_dimensions"]["delivery_model"]["classification"] for candidate in candidates
    )
    return {
        "candidate_count": len(candidates),
        "shared_technology_scope": [
            {"service": service, "candidate_count": count}
            for service, count in sorted(service_counts.items())
            if count > 1
        ],
        "distinct_delivery_models": [
            {"delivery_model": model, "candidate_count": count}
            for model, count in sorted(model_counts.items())
        ],
        "comparison_reading_guide": "Compare the matrix by delivery model and source evidence coverage first; do not mistake missing pricing or Region evidence for a negative result.",
    }


def _fetch_official_page(url: str) -> dict[str, Any]:
    if not _is_official_aws_url(url):
        raise ValueError("S2 official evidence URLs must be on an official AWS host.")
    request = Request(
        url,
        headers={
            "User-Agent": "agentic-cloud-radar/1.0 (S2 evidence comparison)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
        final_url = response.geturl()
        if not _is_official_aws_url(final_url):
            raise ValueError("Official evidence redirected outside AWS hosts.")
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
            raise ValueError(f"Unsupported official evidence content type: {content_type or 'unknown'}")
        html = response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")
    parser = _OfficialEvidenceParser(final_url)
    parser.feed(html)
    return {
        "final_url": final_url,
        "title": parser.title.strip(),
        "description": parser.description.strip(),
        "text": "\n".join(_compact_text(part) for part in parser.text_parts if _compact_text(part)),
        "links": parser.links,
    }


def _select_linked_evidence(links: list[dict[str, str]], candidate: dict[str, Any]) -> list[dict[str, str]]:
    selected: list[tuple[int, dict[str, str]]] = []
    seen_urls: set[str] = set()
    terms = _candidate_evidence_terms(candidate)
    for link in links:
        url = link["url"]
        if url in seen_urls or not _is_official_aws_url(url):
            continue
        evidence_type = _evidence_type_for_url(url)
        if evidence_type is None:
            continue
        link_text = f"{url} {link['link_text']}".lower()
        matched_terms = [term for term in terms if term in link_text]
        if not matched_terms:
            continue
        seen_urls.add(url)
        selected.append((len(matched_terms), {**link, "evidence_type": evidence_type, "matched_candidate_terms": matched_terms}))
    selected.sort(key=lambda item: (-item[0], item[1]["url"]))
    return [item for _, item in selected[:MAX_LINKED_EVIDENCE_PER_CANDIDATE]]


def _candidate_evidence_terms(candidate: dict[str, Any]) -> list[str]:
    text = " ".join([str(candidate.get("title") or ""), *[str(item) for item in candidate.get("initial_claims") or []]]).lower()
    ignored = {"amazon", "announcing", "available", "aws", "blog", "cloud", "general", "generally", "launch", "new", "now", "the", "this", "today"}
    terms = re.findall(r"[a-z0-9][a-z0-9-]{2,}", text)
    return list(dict.fromkeys(term for term in terms if term not in ignored))


def _evidence_type_for_url(url: str) -> str | None:
    parsed = urlparse(url)
    path = parsed.path.lower()
    host = (parsed.hostname or "").lower()
    if host == "docs.aws.amazon.com":
        return "aws_docs"
    if "/pricing" in path or path.startswith("/pricing"):
        return "aws_pricing"
    if any(marker in path for marker in ("region", "local-zone", "availability-zone", "global-infrastructure")):
        return "region_availability"
    return None


def _is_official_aws_url(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and any(host == suffix or host.endswith(f".{suffix}") for suffix in AWS_HOST_SUFFIXES)


def _compact_text(value: str) -> str:
    return " ".join(value.split())


class _OfficialEvidenceParser(HTMLParser):
    """Extract page metadata, visible text, and the page's own outgoing links."""

    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.title = ""
        self.description = ""
        self.text_parts: list[str] = []
        self.links: list[dict[str, str]] = []
        self._in_title = False
        self._active_link: dict[str, str] | None = None
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        attributes = {key.lower(): (value or "") for key, value in attrs}
        if lowered in {"aside", "button", "footer", "form", "header", "nav", "noscript", "script", "style", "svg"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if lowered == "title":
            self._in_title = True
        elif lowered == "meta" and (attributes.get("name", "").lower() == "description" or attributes.get("property", "").lower() == "og:description"):
            self.description = attributes.get("content", "")
        elif lowered == "a" and attributes.get("href"):
            self._active_link = {"url": urljoin(self.base_url, attributes["href"]).split("#", 1)[0], "link_text": ""}

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in {"aside", "button", "footer", "form", "header", "nav", "noscript", "script", "style", "svg"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if lowered == "title":
            self._in_title = False
        elif lowered == "a" and self._active_link is not None:
            self._active_link["link_text"] = _compact_text(self._active_link["link_text"])
            self.links.append(self._active_link)
            self._active_link = None

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = _compact_text(data)
        if not text:
            return
        if self._in_title:
            self.title += text
        elif self._active_link is not None:
            self._active_link["link_text"] += f" {text}"
        elif len(text) >= 20:
            self.text_parts.append(text)
