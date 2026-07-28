"""S1: collect traceable public evidence through two explicit entries.

``build_direct_url_scan`` imports one user-specified public URL directly.
``build_scan`` is the discovery route: it uses the AWS RSS directory plus
public GitHub repository search, with optional scope hints but no S0 gate. Neither route
accepts pasted articles, invented metadata, LLM hints, fixtures, or placeholder
URLs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
from html import unescape
from html.parser import HTMLParser
import json
import re
from typing import Any
from xml.etree import ElementTree
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

from .service_detection import detect_service_signals, service_names, tags_from_text


AWS_HOST_SUFFIXES = ("aws.amazon.com", "docs.aws.amazon.com")
TRUSTED_HTML_HOST_SUFFIXES = AWS_HOST_SUFFIXES + ("github.com", "gitlab.com", "codeberg.org")
GITHUB_API_HOST = "api.github.com"
FETCH_TIMEOUT_SECONDS = 15
DEFAULT_TARGET_REGION = "ap-southeast-1"
MAX_ARTICLE_TEXT_CHARS = 8_000
MAX_CLAIMS = 3
MAX_RSS_ITEMS_PER_FEED = 20
MAX_RSS_CANDIDATES = 3
MAX_AWS_BLOG_FEEDS_PER_SCAN = 8
MAX_GITHUB_CANDIDATES = 4
MAX_GITHUB_REPOSITORIES_PER_QUERY = 2
BROAD_DISCOVERY_TERMS = {"build", "deployment", "devops", "operations", "pipeline", "workflow"}
GA_EVIDENCE_PATTERNS = (
    re.compile(r"\bnow\s+generally\s+available\b", re.IGNORECASE),
    re.compile(r"\bgenerally\s+available\b", re.IGNORECASE),
    re.compile(r"\bgeneral\s+availability\b", re.IGNORECASE),
)
NON_GA_CONTEXT_PATTERN = re.compile(
    r"\b(preview|before\s+(?:they|it)\s+become(?:s)?\s+generally\s+available|"
    r"not\s+(?:yet\s+)?generally\s+available|will\s+become\s+generally\s+available)\b",
    re.IGNORECASE,
)
ROUNDUP_TITLE_PATTERN = re.compile(
    r"\b(this\s+month\s+in|weekly\s+roundup|most\s+visited|top\s+.*blog\s+posts|"
    r"year\s+in\s+review|re:\s*invent\s+recap)\b",
    re.IGNORECASE,
)

# AWS Blogs is a dynamic, category-based technical intelligence catalog. S1
# reads the public directory at runtime, then chooses relevant category feeds
# from optional discovery hints. This prevents a hand-maintained shortlist from
# hiding most AWS work.
AWS_BLOG_DIRECTORY_URL = "https://aws.amazon.com/blogs/"
AWS_WHATS_NEW_FEED = ("aws_whats_new", "AWS What's New", "https://aws.amazon.com/new/feed/")
DEFAULT_AWS_BLOG_CATEGORY_NAMES = {"AWS News", "Architecture"}
AWS_BLOG_TOPIC_MARKERS = {
    "AWS Cloud Operations": ("ci/cd", "ci cd", "github actions", "devops", "operations", "observability", "monitoring", "reliability", "incident", "維運", "監控", "可觀測", "排查"),
    "DevOps & Developer Productivity": ("ci/cd", "ci cd", "github actions", "devops", "developer productivity", "pipeline", "開發", "排查"),
    "Developer Tools": ("ci/cd", "ci cd", "github actions", "developer", "ide", "sdk", "開發"),
    "Compute": ("ci/cd", "ci cd", "github actions", "serverless", "lambda", "containers", "deployment", "compute", "部署"),
    "Containers": ("container", "kubernetes", "eks", "ecs", "docker", "容器"),
    "Big Data": ("data", "analytics", "stream", "kinesis", "opensearch", "logs", "log", "lake", "etl", "glue", "資料", "日誌", "分析", "串流"),
    "Business Intelligence": ("business intelligence", "dashboard", "quicksight", "bi", "商業智慧"),
    "Artificial Intelligence": ("ai", "agent", "llm", "rag", "model", "inference", "machine learning", "人工智慧", "模型"),
    "Database": ("database", "sql", "dynamodb", "postgres", "mysql", "redis", "memorydb", "資料庫"),
    "Integration & Automation": ("integration", "automation", "eventbridge", "step functions", "workflow", "整合", "自動化"),
    "Open Source": ("open source", "opensource", "linux", "開源"),
    "Security": ("security", "iam", "compliance", "audit", "threat", "encryption", "資安", "安全", "稽核"),
    "Storage": ("storage", "s3", "file", "backup", "archive", "儲存"),
    "Networking & Content Delivery": ("network", "cloudfront", "dns", "vpc", "cdn", "網路"),
    "Migration & Modernization": ("migration", "modernization", "legacy", "遷移", "現代化"),
}

# GitHub Search is public, queryable at runtime, and returns repository
# provenance (owner, licence, stars, activity) without user-supplied data.
GITHUB_SEARCH_ENDPOINT = "https://api.github.com/search/repositories"


@dataclass(frozen=True)
class ScanIssue:
    """A machine-readable reason why this S1 run cannot be treated as complete."""

    code: str
    message: str
    severity: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "severity": self.severity}


@dataclass(frozen=True)
class FetchedSource:
    """The evidence S1 actually retrieved after HTTP redirects completed."""

    requested_url: str
    final_url: str
    title: str
    description: str
    text: str
    content_type: str


@dataclass(frozen=True)
class RssItem:
    """One latest-news record fetched from an official AWS RSS feed."""

    feed_name: str
    feed_url: str
    title: str
    url: str
    published_at: str
    summary: str


@dataclass(frozen=True)
class AwsBlogCategory:
    """One category discovered from the live AWS Blogs directory."""

    key: str
    name: str
    category_url: str
    feed_url: str


@dataclass(frozen=True)
class GitHubRepository:
    """Public repository metadata returned by GitHub Search during this run."""

    full_name: str
    html_url: str
    api_url: str
    description: str
    updated_at: str
    pushed_at: str
    stars: int
    forks: int
    license_name: str | None
    topics: list[str]
    default_branch: str
    archived: bool
    search_query: str


@dataclass
class ScanResult:
    scan: dict[str, Any]
    issues: list[ScanIssue] = field(default_factory=list)

    @property
    def status(self) -> str:
        if any(issue.severity == "blocker" for issue in self.issues):
            return "blocked_s0_not_confirmed"
        if any(issue.severity == "error" for issue in self.issues):
            return "needs_revision"
        if not self.scan["candidates"]:
            return "no_candidates"
        if self.scan["data_gaps"]:
            return "scanned_with_gaps"
        return "scanned"

    def to_dict(self) -> dict[str, Any]:
        payload = dict(self.scan)
        payload["status"] = self.status
        payload["scan_issues"] = [issue.to_dict() for issue in self.issues]
        return payload


def build_scan(discovery_request: dict[str, Any]) -> ScanResult:
    """Run the S1 discovery route without requiring an S0 entry card.

    Any problem statement here is only a scan hint. S2 turns each discovered
    candidate into its own proposal card, so a blank landscape scan remains valid.
    """

    request = _normalize_discovery_request(discovery_request)
    issues = _validate_discovery_request(request)
    scan = _base_scan(request)
    if issues:
        return ScanResult(scan, issues)

    scan["scan_mode"] = "technology_discovery_rss"
    _scan_latest_official_rss(request, scan, issues)
    if request.get("maturity_requirement") == "ga_evidence_required":
        scan["source_catalog"]["github_repository_queries"].append(
            {
                "status": "skipped",
                "reason": "GA verification requires an official AWS source; GitHub repository metadata cannot prove AWS GA status.",
            }
        )
    else:
        _scan_github_open_source_repositories(request, scan, issues)

    scan["evidence_summary"] = _evidence_summary(scan["candidates"])
    scan["external_fetch_performed"] = any(
        candidate["external_fetch_performed"] for candidate in scan["candidates"]
    )
    return ScanResult(scan, issues)


def build_direct_url_scan(requested_url: str) -> ScanResult:
    """Import one URL without S0 while keeping the public-source safety checks.

    This path has no problem statement or business fit because none was supplied.
    That absence is recorded for S2/S3 rather than silently filled with a guess.
    """

    clean_url = str(requested_url or "").strip()
    scan = _base_direct_url_scan(clean_url)
    issues: list[ScanIssue] = []
    if not clean_url:
        issues.append(ScanIssue("missing_direct_url", "Direct URL import requires a public HTTPS URL.", "error"))
        return ScanResult(scan, issues)
    if not _is_trusted_html_url(clean_url):
        issues.append(
            ScanIssue(
                "untrusted_direct_url",
                "Direct URL import accepts AWS, GitHub, GitLab, or Codeberg HTTPS pages.",
                "error",
            )
        )
        return ScanResult(scan, issues)

    try:
        fetched = _fetch_trusted_html_url(clean_url)
    except Exception as exc:  # Network, TLS, HTTP, and parser failures vary by host.
        issues.append(ScanIssue("direct_url_fetch_failed", str(exc), "error"))
        return ScanResult(scan, issues)

    direct_context = {"run_id": scan["run_id"]}
    candidate = _candidate_from_fetched_source(
        direct_context,
        fetched,
        source_selection="direct_user_url_import",
        source_type="direct_trusted_public_url",
        official_source=_is_official_aws_url(fetched.final_url),
        open_source=_is_open_source_host(fetched.final_url),
    )
    scan["candidates"].append(candidate)
    scan["source_catalog"]["direct_url_import"].update(
        {"status": "fetched", "final_url": fetched.final_url, "content_type": fetched.content_type}
    )
    scan["data_gaps"].extend(candidate["data_gaps"])
    scan["data_gaps"].append(
        "Direct URL import has no business-problem context; S2 can compare source evidence but cannot judge business fit until a human adds context.",
    )
    scan["evidence_summary"] = _evidence_summary(scan["candidates"])
    scan["external_fetch_performed"] = True
    return ScanResult(scan, issues)


def _normalize_discovery_request(raw: dict[str, Any]) -> dict[str, Any]:
    """Accept optional scan hints without turning them into a mandatory gate."""

    return {
        "run_id": raw.get("run_id"),
        "problem_statement": str(raw.get("problem_statement") or "").strip(),
        "desired_outcome": str(raw.get("desired_outcome") or "").strip(),
        "business_domain": str(raw.get("business_domain") or "").strip(),
        "evaluation_priority": [str(value).strip() for value in raw.get("evaluation_priority") or [] if str(value).strip()],
        "constraints": dict(raw.get("constraints") or {}),
        "target_region": str((raw.get("constraints") or {}).get("preferred_region") or raw.get("target_region") or DEFAULT_TARGET_REGION).strip(),
        "discovery_scope": str(raw.get("discovery_scope") or "landscape").strip().lower(),
        "max_source_age_days": raw.get("max_source_age_days", 365),
        "max_candidates": raw.get("max_candidates", 20),
        "maturity_requirement": str(raw.get("maturity_requirement") or "any").strip().lower(),
    }


def _base_scan(discovery_request: dict[str, Any]) -> dict[str, Any]:
    """Create the artifact shell before any network call, so failures stay auditable."""

    return {
        "schema_version": "s1.scan.v2",
        "run_id": str(discovery_request.get("run_id") or _make_discovery_run_id(discovery_request)),
        "stage": "S1",
        "status": "draft",
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "entry_point": {"type": "technology_discovery", "s0_required": False},
        "discovery_request_ref": {
            "problem_statement_hint": discovery_request.get("problem_statement", ""),
            "desired_outcome_hint": discovery_request.get("desired_outcome", ""),
            "discovery_scope": discovery_request.get("discovery_scope", "landscape"),
            "max_source_age_days": discovery_request.get("max_source_age_days", 365),
            "max_candidates": discovery_request.get("max_candidates", 20),
            "maturity_requirement": discovery_request.get("maturity_requirement", "any"),
            "target_region": discovery_request.get("target_region", DEFAULT_TARGET_REGION),
        },
        "demand_card_ref": None,
        "source_mode": "rss_discovery",
        "scan_mode": "pending_source_selection",
        "external_fetch_performed": False,
        "candidates": [],
        "evidence_summary": _evidence_summary([]),
        "data_gaps": [],
        "maturity_filter": {
            "requirement": discovery_request.get("maturity_requirement", "any"),
            "included_with_official_ga_evidence": 0,
            "excluded_without_official_ga_evidence": 0,
        },
        "notes": [
            "S1 is an entry stage. It collects candidates; S2 converts them into proposal cards and comparison material.",
            "Focused discovery uses optional hints; landscape discovery reads the full AWS Blogs directory and returns a cross-domain set of candidates.",
            "When maturity_requirement is ga_evidence_required, S1 only retains AWS candidates whose fetched source explicitly states general availability; this is not a complete AWS release-history archive.",
            "Every candidate is based on data fetched during this run; no fixture, pasted text, LLM hint, or manually supplied metadata is used.",
        ],
        "source_catalog": {
            "aws_blog_directory": {"url": AWS_BLOG_DIRECTORY_URL, "status": "pending", "category_count": 0},
            "aws_rss_feeds": [],
            "github_repository_queries": [],
        },
    }


def _base_direct_url_scan(requested_url: str) -> dict[str, Any]:
    """Create an S1 artifact for the direct-import entry without fabricating business context."""

    now = datetime.now(timezone.utc)
    run_seed = f"direct-url|{requested_url}|{now.isoformat()}"
    run_id = f"direct-url-{now.strftime('%Y%m%d')}-{hashlib.sha1(run_seed.encode('utf-8')).hexdigest()[:8]}"
    return {
        "schema_version": "s1.scan.v2",
        "run_id": run_id,
        "stage": "S1",
        "status": "draft",
        "scanned_at": now.isoformat(),
        "entry_point": {
            "type": "direct_url_import",
            "requested_url": requested_url,
            "s0_required": False,
            "human_action": "user_supplied_url",
        },
        "target_region": DEFAULT_TARGET_REGION,
        "demand_card_ref": None,
        "source_mode": "direct_url_import",
        "scan_mode": "direct_user_url_import",
        "external_fetch_performed": False,
        "candidates": [],
        "evidence_summary": _evidence_summary([]),
        "data_gaps": [],
        "maturity_filter": {
            "requirement": "not_requested_for_direct_import",
            "included_with_official_ga_evidence": 0,
            "excluded_without_official_ga_evidence": 0,
        },
        "notes": [
            "The user intentionally selected this URL, so this entry begins directly at S1.",
            "HTTPS, trusted-host, redirect, and HTML content-type validation still apply before any content is recorded.",
            "No problem statement is fabricated; business fit remains explicitly unknown until a human provides context.",
        ],
        "source_catalog": {
            "direct_url_import": {"requested_url": requested_url, "status": "pending"},
            "aws_blog_directory": None,
            "aws_rss_feeds": [],
            "github_repository_queries": [],
        },
    }


def _validate_discovery_request(request: dict[str, Any]) -> list[ScanIssue]:
    """Validate scan parameters only; S1 is intentionally not a demand gate."""

    issues: list[ScanIssue] = []
    if request.get("discovery_scope") not in {"focused", "landscape"}:
        issues.append(ScanIssue("invalid_discovery_scope", "discovery_scope must be focused or landscape.", "error"))
    if request.get("maturity_requirement") not in {"any", "ga_evidence_required"}:
        issues.append(ScanIssue("invalid_maturity_requirement", "maturity_requirement must be any or ga_evidence_required.", "error"))
    for field_name, maximum in (("max_source_age_days", 3650), ("max_candidates", 50)):
        value = request.get(field_name)
        if isinstance(value, bool) or not str(value).isdigit() or not 0 < int(value) <= maximum:
            issues.append(ScanIssue(f"invalid_{field_name}", f"{field_name} must be an integer from 1 to {maximum}.", "error"))
    return issues
    return []


def _scan_latest_official_rss(
    demand_card: dict[str, Any], scan: dict[str, Any], issues: list[ScanIssue]
) -> None:
    """Discover relevant AWS technology from real RSS feeds, then fetch selected pages."""

    scan["scan_mode"] = "aws_blog_category_and_open_source_discovery"
    try:
        categories = _fetch_aws_blog_catalog()
        scan["source_catalog"]["aws_blog_directory"] = {
            "url": AWS_BLOG_DIRECTORY_URL,
            "status": "fetched",
            "category_count": len(categories),
        }
    except Exception as exc:
        issues.append(ScanIssue("aws_blog_directory_fetch_failed", str(exc), "warning"))
        categories = _fallback_aws_blog_categories()
        scan["source_catalog"]["aws_blog_directory"] = {
            "url": AWS_BLOG_DIRECTORY_URL,
            "status": "failed_using_baseline_fallback",
            "category_count": len(categories),
        }

    items: list[RssItem] = []
    for category, selection_reason in _select_aws_blog_feeds(demand_card, categories):
        try:
            items.extend(_fetch_rss_items(category.name, category.feed_url))
            scan["source_catalog"]["aws_rss_feeds"].append(
                {
                    "feed_key": category.key,
                    "feed_name": category.name,
                    "category_url": category.category_url,
                    "feed_url": category.feed_url,
                    "selection_reason": selection_reason,
                    "status": "fetched",
                }
            )
        except Exception as exc:  # One unavailable feed must not discard the other official feeds.
            issues.append(ScanIssue("rss_feed_fetch_failed", f"{category.name}: {exc}", "warning"))
            scan["source_catalog"]["aws_rss_feeds"].append(
                {
                    "feed_key": category.key,
                    "feed_name": category.name,
                    "category_url": category.category_url,
                    "feed_url": category.feed_url,
                    "selection_reason": selection_reason,
                    "status": "failed",
                }
            )

    selected = _select_rss_items(demand_card, items)
    if not selected:
        scan["data_gaps"].append("No current AWS RSS item met the confirmed problem's relevance threshold.")
        return

    selected_before_maturity_filter = len(selected)
    for item in selected:
        try:
            fetched = _fetch_trusted_html_url(item.url)
        except Exception as exc:
            issues.append(ScanIssue("rss_article_fetch_failed", f"{item.url}: {exc}", "warning"))
            scan["data_gaps"].append(f"Selected RSS article could not be fetched: {item.url}")
            continue

        candidate = _candidate_from_fetched_source(
            demand_card,
            fetched,
            source_selection="latest_official_aws_rss",
            rss_item=item,
            source_type="official_aws_rss_article",
            official_source=True,
        )
        if (
            demand_card.get("maturity_requirement") == "ga_evidence_required"
            and candidate["maturity_evidence"]["status"] != "official_ga_evidence_found"
        ):
            scan["maturity_filter"]["excluded_without_official_ga_evidence"] += 1
            continue
        scan["candidates"].append(candidate)
        if candidate["maturity_evidence"]["status"] == "official_ga_evidence_found":
            scan["maturity_filter"]["included_with_official_ga_evidence"] += 1
        scan["data_gaps"].extend(candidate["data_gaps"])

    if (
        selected_before_maturity_filter
        and demand_card.get("maturity_requirement") == "ga_evidence_required"
        and not scan["candidates"]
    ):
        scan["data_gaps"].append(
            "The scanned RSS items did not contain explicit official general-availability wording; this run cannot claim any GA candidate."
        )


def _fetch_aws_blog_catalog() -> list[AwsBlogCategory]:
    """Parse the live AWS Blogs category menu instead of maintaining a short list."""

    request = Request(
        AWS_BLOG_DIRECTORY_URL,
        headers={
            "User-Agent": "agentic-cloud-radar/1.0 (S1 AWS Blog category catalog)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
        final_url = response.geturl()
        if not _is_official_aws_url(final_url):
            raise ValueError("AWS Blogs directory redirected outside an AWS host.")
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
            raise ValueError(f"Unexpected AWS Blogs directory content type: {content_type or 'unknown'}")
        raw_html = response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")

    menu_html = unescape(raw_html.replace(r'\"', '"'))
    categories: list[AwsBlogCategory] = []
    seen_urls: set[str] = set()
    for category_url, label in re.findall(r'<a\s+href="([^"]+)"[^>]*>([^<]+)</a>', menu_html, re.IGNORECASE):
        normalized_url = urljoin(AWS_BLOG_DIRECTORY_URL, category_url).split("?", 1)[0]
        parsed = urlparse(normalized_url)
        path_parts = [part for part in parsed.path.split("/") if part]
        name = _compact_text(label)
        if (
            not _is_official_aws_url(normalized_url)
            or len(path_parts) != 2
            or path_parts[0] != "blogs"
            or not name
            or normalized_url in seen_urls
        ):
            continue
        seen_urls.add(normalized_url)
        categories.append(
            AwsBlogCategory(
                key=_source_key(name),
                name=name,
                category_url=normalized_url.rstrip("/") + "/",
                feed_url=normalized_url.rstrip("/") + "/feed/",
            )
        )
    if not categories:
        raise ValueError("AWS Blogs directory did not yield any category links.")
    return categories


def _fallback_aws_blog_categories() -> list[AwsBlogCategory]:
    """Keep a minimal auditable path when the live directory is temporarily unavailable."""

    return [
        AwsBlogCategory("aws_whats_new", "AWS What's New", "https://aws.amazon.com/new/", AWS_WHATS_NEW_FEED[2]),
        AwsBlogCategory("architecture", "Architecture", "https://aws.amazon.com/blogs/architecture/", "https://aws.amazon.com/blogs/architecture/feed/"),
        AwsBlogCategory("aws_news", "AWS News", "https://aws.amazon.com/blogs/aws/", "https://aws.amazon.com/blogs/aws/feed/"),
    ]


def _select_aws_blog_feeds(
    demand_card: dict[str, Any], categories: list[AwsBlogCategory]
) -> list[tuple[AwsBlogCategory, str]]:
    """Choose live AWS Blog categories from the confirmed problem, not recency alone."""

    if demand_card.get("discovery_scope") == "landscape":
        whats_new = AwsBlogCategory(
            AWS_WHATS_NEW_FEED[0],
            AWS_WHATS_NEW_FEED[1],
            "https://aws.amazon.com/new/",
            AWS_WHATS_NEW_FEED[2],
        )
        return [(whats_new, "landscape baseline")] + [
            (category, "landscape: full AWS Blogs directory") for category in categories
        ]

    demand_text = " ".join(
        [
            str(demand_card.get("business_domain", "")),
            str(demand_card.get("problem_statement", "")),
            str(demand_card.get("desired_outcome", "")),
            " ".join(str(value) for value in demand_card.get("evaluation_priority", [])),
        ]
    ).lower()
    reasons: dict[str, list[str]] = {}
    for category in categories:
        if category.name in DEFAULT_AWS_BLOG_CATEGORY_NAMES:
            reasons[category.key] = ["baseline AWS technology coverage"]
    for category_name, markers in AWS_BLOG_TOPIC_MARKERS.items():
        matched_markers = [marker for marker in markers if marker in demand_text]
        if matched_markers:
            category = next((item for item in categories if item.name == category_name), None)
            if category:
                reasons[category.key] = [f"discovery hint match: {', '.join(matched_markers[:3])}"]
    for category in categories:
        if category.key in reasons:
            continue
        category_terms = _meaningful_terms(category.name)
        matched_terms = [term for term in category_terms if term in demand_text]
        if matched_terms:
            reasons[category.key] = [f"discovery category-name match: {', '.join(matched_terms[:3])}"]

    selected: list[tuple[AwsBlogCategory, str]] = [
        (AwsBlogCategory(*AWS_WHATS_NEW_FEED[:2], "https://aws.amazon.com/new/", AWS_WHATS_NEW_FEED[2]), "baseline AWS technology coverage")
    ]
    for category in categories:
        if category.key in reasons:
            selected.append((category, "; ".join(reasons[category.key])))
        if len(selected) >= MAX_AWS_BLOG_FEEDS_PER_SCAN:
            break
    return selected


def _fetch_rss_items(feed_name: str, feed_url: str) -> list[RssItem]:
    """Fetch and parse an AWS RSS feed without replacing it with cached content."""

    request = Request(feed_url, headers={"User-Agent": "agentic-cloud-radar/1.0 (S1 official RSS scan)", "Accept": "application/rss+xml,application/xml,text/xml"})
    with urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
        final_url = response.geturl()
        if not _is_official_aws_url(final_url):
            raise ValueError("Official RSS feed redirected to a non-official host.")
        xml = response.read()

    root = ElementTree.fromstring(xml)
    rss_items = root.findall(".//item")
    if not rss_items:
        rss_items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

    parsed: list[RssItem] = []
    for element in rss_items[:MAX_RSS_ITEMS_PER_FEED]:
        title = _xml_text(element, "title")
        link = _rss_link(element)
        if not title or not link or not _is_official_aws_url(link):
            continue
        parsed.append(
            RssItem(
                feed_name=feed_name,
                feed_url=final_url,
                title=title,
                url=link,
                published_at=_xml_text(element, "pubDate") or _xml_text(element, "published") or _xml_text(element, "updated"),
                summary=_compact_text(_strip_html(_xml_text(element, "description") or _xml_text(element, "summary"))),
            )
        )
    return parsed


def _select_rss_items(demand_card: dict[str, Any], items: list[RssItem]) -> list[RssItem]:
    """Keep official items that match the confirmed problem and maturity gate."""

    if demand_card.get("discovery_scope") == "landscape":
        return _select_landscape_rss_items(demand_card, items)

    excluded = {str(service).lower() for service in (demand_card.get("constraints") or {}).get("excluded_services", [])}
    query_terms = _discovery_terms(demand_card)
    requires_ci_specific_match = _is_ci_cd_intent(demand_card)
    scored: list[tuple[int, int, RssItem]] = []
    for position, item in enumerate(items):
        searchable = f"{item.title} {item.summary}".lower()
        if any(service in searchable for service in excluded):
            continue
        if (
            demand_card.get("maturity_requirement") == "ga_evidence_required"
            and not _has_explicit_ga_wording(searchable)
        ):
            continue
        matched_terms = [term for term in query_terms if term in searchable]
        strong_matches = [term for term in matched_terms if term not in BROAD_DISCOVERY_TERMS]
        if requires_ci_specific_match and not strong_matches:
            continue
        if not requires_ci_specific_match and not strong_matches and len(matched_terms) < 2:
            continue
        score = len(strong_matches) * 3 + len(matched_terms)
        scored.append((score, -position, item))

    scored.sort(reverse=True, key=lambda record: (record[0], record[1]))
    return [item for _, _, item in scored[:MAX_RSS_CANDIDATES]]


def _select_landscape_rss_items(demand_card: dict[str, Any], items: list[RssItem]) -> list[RssItem]:
    """Keep cross-domain candidates, prioritizing explicit GA RSS wording when required."""

    excluded = {
        str(service).lower()
        for service in (demand_card.get("constraints") or {}).get("excluded_services", [])
    }
    max_age_days = int(demand_card.get("max_source_age_days", 365))
    newest_by_feed: dict[str, RssItem] = {}
    for item in items:
        searchable = f"{item.title} {item.summary}".lower()
        if any(service in searchable for service in excluded):
            continue
        if (
            demand_card.get("maturity_requirement") == "ga_evidence_required"
            and not _has_explicit_ga_wording(searchable)
        ):
            continue
        published_at = _published_at_or_none(item.published_at)
        if published_at is None or (datetime.now(timezone.utc) - published_at).days > max_age_days:
            continue
        existing = newest_by_feed.get(item.feed_url)
        if existing is None or _published_at_or_none(existing.published_at) < published_at:
            newest_by_feed[item.feed_url] = item

    selected = list(newest_by_feed.values())
    selected.sort(
        key=lambda item: (_published_at_or_none(item.published_at) or datetime.min.replace(tzinfo=timezone.utc), item.title),
        reverse=True,
    )
    return selected[: int(demand_card.get("max_candidates", 20))]


def _has_explicit_ga_wording(text: str) -> bool:
    """Use the same narrow GA wording gate for RSS preselection and page evidence."""

    return any(pattern.search(text) for pattern in GA_EVIDENCE_PATTERNS)


def _scan_github_open_source_repositories(
    demand_card: dict[str, Any], scan: dict[str, Any], issues: list[ScanIssue]
) -> None:
    """Discover active public open-source repositories relevant to optional scan hints."""

    selected: list[GitHubRepository] = []
    seen_urls: set[str] = set()
    for query in _github_search_queries(demand_card):
        try:
            repositories = _fetch_github_repositories(query)
            scan["source_catalog"]["github_repository_queries"].append(
                {"query": query, "status": "fetched", "result_count": len(repositories)}
            )
        except Exception as exc:  # Public API quotas or temporary failures should remain visible.
            issues.append(ScanIssue("github_repository_search_failed", f"{query}: {exc}", "warning"))
            scan["source_catalog"]["github_repository_queries"].append(
                {"query": query, "status": "failed", "result_count": 0}
            )
            continue

        selected_from_query = 0
        for repository in repositories:
            if repository.html_url in seen_urls:
                continue
            seen_urls.add(repository.html_url)
            selected.append(repository)
            selected_from_query += 1
            if selected_from_query >= MAX_GITHUB_REPOSITORIES_PER_QUERY:
                break
        if len(selected) >= MAX_GITHUB_CANDIDATES:
            break

    if not selected:
        scan["data_gaps"].append("No public GitHub repository matched the confirmed discovery queries during this scan.")
        return

    for repository in selected:
        scan["candidates"].append(_candidate_from_github_repository(demand_card, repository))


def _github_search_queries(demand_card: dict[str, Any]) -> list[str]:
    """Translate recurring radar intents into transparent, bounded public searches."""

    text = " ".join(
        [
            str(demand_card.get("problem_statement", "")),
            str(demand_card.get("desired_outcome", "")),
            " ".join(str(value) for value in demand_card.get("evaluation_priority", [])),
        ]
    ).lower()
    queries: list[str] = []
    if any(term in text for term in ("ci/cd", "ci cd", "github actions", "pipeline", "deployment", "build", "開發", "排查")):
        queries.extend(("topic:github-actions archived:false", "topic:continuous-integration archived:false"))
    if any(term in text for term in ("operations", "observability", "monitoring", "reliability", "維運", "監控", "可觀測")):
        queries.append("topic:devops archived:false")
    if not queries:
        queries.append("topic:cloud-native archived:false")
    return list(dict.fromkeys(queries))[:2]


def _fetch_github_repositories(query: str) -> list[GitHubRepository]:
    """Call GitHub's public search API and retain only non-archived repositories."""

    request_url = f"{GITHUB_SEARCH_ENDPOINT}?{urlencode({'q': query, 'sort': 'stars', 'order': 'desc', 'per_page': MAX_GITHUB_REPOSITORIES_PER_QUERY})}"
    request = Request(
        request_url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "agentic-cloud-radar/1.0 (S1 public open-source discovery)",
        },
    )
    with urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
        if (urlparse(response.geturl()).hostname or "").lower() != GITHUB_API_HOST:
            raise ValueError("GitHub repository search redirected away from api.github.com.")
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            raise ValueError(f"Unexpected GitHub Search content type: {content_type or 'unknown'}")
        payload = json.loads(response.read().decode("utf-8", errors="replace"))

    repositories: list[GitHubRepository] = []
    for item in payload.get("items", []):
        html_url = str(item.get("html_url") or "")
        if not _is_github_repository_url(html_url) or bool(item.get("archived")):
            continue
        licence = item.get("license") or {}
        repositories.append(
            GitHubRepository(
                full_name=str(item.get("full_name") or ""),
                html_url=html_url,
                api_url=str(item.get("url") or ""),
                description=_compact_text(str(item.get("description") or "")),
                updated_at=str(item.get("updated_at") or ""),
                pushed_at=str(item.get("pushed_at") or ""),
                stars=int(item.get("stargazers_count") or 0),
                forks=int(item.get("forks_count") or 0),
                license_name=str(licence.get("spdx_id") or licence.get("name") or "") or None,
                topics=[str(topic) for topic in item.get("topics") or []],
                default_branch=str(item.get("default_branch") or ""),
                archived=False,
                search_query=query,
            )
        )
    return repositories


def _candidate_from_github_repository(
    demand_card: dict[str, Any], repository: GitHubRepository
) -> dict[str, Any]:
    """Record public project metadata as a candidate, not as a recommendation."""

    evidence_text = _compact_text(
        " ".join([repository.description, " ".join(repository.topics), repository.full_name])
    )
    run_id = str(demand_card.get("run_id") or "unknown-run")
    return {
        "candidate_id": _make_candidate_id(run_id, repository.full_name, repository.html_url),
        "title": repository.full_name,
        "source_type": "github_open_source_repository",
        "requested_url": repository.html_url,
        "source_url": repository.html_url,
        "official_source": False,
        "open_source": True,
        "external_fetch_performed": True,
        "source_selection": "github_public_repository_search",
        "rss_discovered": False,
        "seed_article": False,
        "evidence_confidence": "medium",
        "evidence_basis": "public_github_repository_search_metadata",
        "retrieved_content_type": "application/json",
        "related_aws_services": service_names(detect_service_signals(evidence_text)),
        "service_detection": detect_service_signals(evidence_text),
        "initial_claims": _claims_from_source(repository.description, " ".join(repository.topics)),
        "possible_application_contexts": _application_contexts(demand_card),
        "tags": tags_from_text(evidence_text),
        "data_gaps": (["The repository search result has no description; inspect its README before S2."] if not repository.description else []),
        "fetched_source": {
            "title": repository.full_name,
            "description": repository.description,
            "text_excerpt": evidence_text[:1_200],
        },
        "github_source": {
            "api_url": repository.api_url,
            "search_query": repository.search_query,
            "updated_at": repository.updated_at,
            "pushed_at": repository.pushed_at,
            "stars": repository.stars,
            "forks": repository.forks,
            "license": repository.license_name,
            "topics": repository.topics,
            "default_branch": repository.default_branch,
            "archived": repository.archived,
        },
        "rss_source": None,
    }


def _candidate_from_fetched_source(
    demand_card: dict[str, Any],
    fetched: FetchedSource,
    *,
    source_selection: str,
    source_type: str,
    official_source: bool,
    open_source: bool = False,
    rss_item: RssItem | None = None,
) -> dict[str, Any]:
    """Turn fetched evidence into one traceable candidate for S2/S3."""

    title = fetched.title or _title_from_url(fetched.final_url)
    article_text = fetched.text[:MAX_ARTICLE_TEXT_CHARS]
    detection_text = " ".join(
        [title, fetched.description, article_text, str(demand_card.get("problem_statement", "")), str(demand_card.get("desired_outcome", ""))]
    )
    service_detection = detect_service_signals(detection_text)
    related_services = service_names(service_detection)
    maturity_evidence = (
        _maturity_evidence(title, article_text)
        if official_source
        else {
            "status": "not_checked_for_non_official_source",
            "evidence_basis": "GA is an AWS release-state claim and is not inferred from a non-official source.",
            "evidence_excerpts": [],
            "rejected_evidence_excerpts": [],
            "limits": ["Inspect the project release or upstream official service documentation separately if maturity is required."],
        }
    )
    data_gaps: list[str] = []
    if not article_text:
        data_gaps.append("The official page was fetched but no readable article text was extracted.")
    if not related_services:
        data_gaps.append("No supported AWS service name was detected in the fetched official page text.")

    run_id = str(demand_card.get("run_id") or "unknown-run")
    return {
        "candidate_id": _make_candidate_id(run_id, title, fetched.final_url),
        "title": title,
        "source_type": source_type,
        "requested_url": fetched.requested_url,
        "source_url": fetched.final_url,
        "official_source": official_source,
        "open_source": open_source,
        "external_fetch_performed": True,
        "source_selection": source_selection,
        "rss_discovered": rss_item is not None,
        "seed_article": False,
        "evidence_confidence": "medium",
        "evidence_basis": "single_fetched_public_html_page",
        "retrieved_content_type": fetched.content_type,
        "related_aws_services": related_services,
        "service_detection": service_detection,
        "initial_claims": _claims_from_source(fetched.description, article_text),
        "possible_application_contexts": _application_contexts(demand_card),
        "tags": tags_from_text(detection_text),
        "maturity_evidence": maturity_evidence,
        "data_gaps": data_gaps,
        "fetched_source": {
            "title": fetched.title,
            "description": fetched.description,
            "text_excerpt": article_text[:1_200],
        },
        "rss_source": (
            {
                "feed_name": rss_item.feed_name,
                "feed_url": rss_item.feed_url,
                "feed_item_title": rss_item.title,
                "feed_item_published_at": rss_item.published_at,
                "feed_item_summary": rss_item.summary,
            }
            if rss_item
            else None
        ),
    }


def _maturity_evidence(title: str, article_text: str) -> dict[str, Any]:
    """Return only explicit GA wording found in the fetched source text.

    An AWS service mention does not itself prove GA. This deliberately narrow
    rule makes an absence of evidence visible instead of inferring maturity.
    """

    if ROUNDUP_TITLE_PATTERN.search(title):
        return {
            "status": "not_a_single_technology_announcement",
            "evidence_basis": "source_title_indicates_roundup_or_recap",
            "evidence_excerpts": [],
            "limits": [
                "A roundup can mention several historical GA releases but is not one atomic technology candidate.",
            ],
        }

    snippets: list[str] = []
    rejected_snippets: list[str] = []
    for sentence in re.split(r"(?<=[.!?。！？])\s+", article_text):
        compact_sentence = _compact_text(sentence)
        if not compact_sentence or not _has_explicit_ga_wording(compact_sentence):
            continue
        if NON_GA_CONTEXT_PATTERN.search(f"{title} {compact_sentence}"):
            rejected_snippets.append(compact_sentence[:400])
            continue
        snippets.append(compact_sentence[:400])
    if snippets:
        status = "official_ga_evidence_found"
    elif rejected_snippets:
        status = "preview_or_future_ga_not_eligible"
    else:
        status = "not_verified_by_this_source"
    return {
        "status": status,
        "evidence_basis": "explicit_general_availability_wording_in_fetched_official_source",
        "evidence_excerpts": snippets[:3],
        "rejected_evidence_excerpts": rejected_snippets[:3],
        "limits": [
            "A source without explicit GA wording is not treated as proof that the technology is preview-only.",
            "S1 does not search the complete AWS release archive in this version.",
        ],
    }


def _evidence_summary(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "official_source_count": sum(1 for item in candidates if item["official_source"]),
        "open_source_repository_count": sum(1 for item in candidates if item.get("open_source")),
        "external_fetch_performed": any(item["external_fetch_performed"] for item in candidates),
        "rss_discovered_count": sum(1 for item in candidates if item["rss_discovered"]),
        "evidence_level": "mixed_public_sources" if candidates else "none",
    }


def _application_contexts(demand_card: dict[str, Any]) -> list[str]:
    """Carry optional scan hints forward without claiming they are confirmed fit."""

    values = [str(demand_card.get("business_domain", "")).strip(), str(demand_card.get("problem_statement", "")).strip()]
    return [value for value in values if value][:2]


def _claims_from_source(description: str, article_text: str) -> list[str]:
    """Keep only source text; S1 does not generate claims that the page did not state."""

    source_text = _compact_text(" ".join([description, article_text]))
    if not source_text:
        return []
    sentences = re.split(r"(?<=[.!?。！？])\s+", source_text)
    return [sentence.strip() for sentence in sentences if sentence.strip()][:MAX_CLAIMS]


def _is_official_aws_url(url: str) -> bool:
    """Check the URL host, rather than trusting a lookalike string in its path/query."""

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https":
        return False
    return any(host == suffix or host.endswith(f".{suffix}") for suffix in AWS_HOST_SUFFIXES)


def _is_trusted_html_url(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and any(
        host == suffix or host.endswith(f".{suffix}")
        for suffix in TRUSTED_HTML_HOST_SUFFIXES
    )


def _is_open_source_host(url: str) -> bool:
    """Mark a directly imported code-host page without assuming a project licence."""

    host = (urlparse(url).hostname or "").lower()
    return host in {"github.com", "gitlab.com", "codeberg.org"}


def _is_github_repository_url(url: str) -> bool:
    parsed = urlparse(url)
    path_parts = [part for part in parsed.path.split("/") if part]
    return (
        parsed.scheme == "https"
        and (parsed.hostname or "").lower() == "github.com"
        and len(path_parts) >= 2
    )


def _fetch_trusted_html_url(requested_url: str) -> FetchedSource:
    """Fetch HTML and reject redirects outside the public source allowlist."""

    request = Request(
        requested_url,
        headers={
            "User-Agent": "agentic-cloud-radar/1.0 (S1 public evidence fetch)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
        final_url = response.geturl()
        if not _is_trusted_html_url(final_url):
            raise ValueError("The public source URL redirected outside the trusted host allowlist.")

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
            raise ValueError(f"Unsupported source content type: {content_type or 'unknown'}")

        charset = response.headers.get_content_charset() or "utf-8"
        html = response.read().decode(charset, errors="replace")

    parser = _HtmlTextExtractor()
    parser.feed(html)
    return FetchedSource(
        requested_url=requested_url,
        final_url=final_url,
        title=parser.title.strip(),
        description=parser.description.strip(),
        text=_clean_extracted_article_text(parser.text_parts),
        content_type=content_type,
    )


class _HtmlTextExtractor(HTMLParser):
    """Extract visible AWS article text while discarding scripts and page chrome."""

    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.description = ""
        self.text_parts: list[str] = []
        self._in_title = False
        self._skip_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if self._skip_stack:
            if lowered not in _VOID_TAGS:
                self._skip_stack.append(lowered)
            return
        if lowered in _SKIP_TAGS or _looks_like_page_chrome(attrs):
            if lowered not in _VOID_TAGS:
                self._skip_stack.append(lowered)
            return
        if lowered == "title":
            self._in_title = True
        if lowered == "meta":
            attributes = {key.lower(): (value or "") for key, value in attrs}
            if attributes.get("name", "").lower() == "description" or attributes.get("property", "").lower() == "og:description":
                self.description = attributes.get("content", "")

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if self._skip_stack:
            if lowered in self._skip_stack:
                while self._skip_stack:
                    if self._skip_stack.pop() == lowered:
                        break
            return
        if lowered == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._skip_stack:
            return
        text = _compact_text(data)
        if not text:
            return
        if self._in_title:
            self.title += text
        elif len(text) >= 20:
            self.text_parts.append(text)


_SKIP_TAGS = {"aside", "button", "footer", "form", "header", "nav", "noscript", "script", "style", "svg"}
_VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
_PAGE_CHROME_MARKERS = {"breadcrumb", "cookie", "drawer", "footer", "header", "language", "menu", "modal", "navigation", "navbar", "promo", "search", "share", "sidebar", "skip"}


def _looks_like_page_chrome(attrs: list[tuple[str, str | None]]) -> bool:
    values = " ".join(value or "" for key, value in attrs if key.lower() in {"class", "id", "aria-label", "role"})
    return any(marker in values.lower() for marker in _PAGE_CHROME_MARKERS)


def _clean_extracted_article_text(parts: list[str]) -> str:
    meaningful: list[str] = []
    seen: set[str] = set()
    for part in parts:
        text = _compact_text(part)
        if not text or text in seen or _is_page_chrome_text(text.lower()):
            continue
        seen.add(text)
        meaningful.append(text)
    return _compact_text(" ".join(meaningful))


def _is_page_chrome_text(text: str) -> bool:
    chrome_phrases = {"skip to main content", "create an aws account", "sign in to the console", "amazon web services", "contact sales", "support center", "privacy notice", "terms of use"}
    return any(phrase in text for phrase in chrome_phrases)


def _title_from_url(url: str) -> str:
    slug = urlparse(url).path.rstrip("/").split("/")[-1]
    return slug.replace("-", " ").replace("_", " ").strip().title() or "AWS official source"


def _compact_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _source_key(value: str) -> str:
    """Create a stable artifact key from an AWS category name without trusting its URL slug."""

    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _strip_html(value: str) -> str:
    return _compact_text(re.sub(r"<[^>]+>", " ", value))


def _xml_text(element: ElementTree.Element, local_name: str) -> str:
    for child in element:
        if child.tag.rsplit("}", 1)[-1] == local_name:
            return _compact_text(child.text or "")
    return ""


def _published_at_or_none(value: str) -> datetime | None:
    """Parse RSS/Atom publication timestamps without treating missing dates as current."""

    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _rss_link(element: ElementTree.Element) -> str:
    direct = _xml_text(element, "link")
    if direct:
        return direct
    for child in element:
        if child.tag.rsplit("}", 1)[-1] == "link" and child.attrib.get("href"):
            return child.attrib["href"]
    return ""


def _meaningful_terms(text: str) -> list[str]:
    stop_words = {"about", "after", "and", "are", "assess", "aws", "can", "for", "from", "into", "new", "that", "the", "this", "to", "whether", "with"}
    terms = re.findall(r"[a-z0-9][a-z0-9-]{2,}", text.lower())
    return list(dict.fromkeys(term for term in terms if term not in stop_words))


def _discovery_terms(demand_card: dict[str, Any]) -> list[str]:
    """Use concrete workflow vocabulary, including common Chinese radar intents."""

    text = " ".join(
        [
            str(demand_card.get("problem_statement", "")),
            str(demand_card.get("desired_outcome", "")),
            " ".join(str(value) for value in demand_card.get("evaluation_priority", [])),
        ]
    ).lower()
    terms = _meaningful_terms(text)
    if _is_ci_cd_intent(demand_card):
        terms.extend(("ci/cd", "github actions", "continuous integration", "continuous deployment", "pipeline", "build", "deployment", "workflow", "devops"))
    if any(term in text for term in ("operations", "observability", "monitoring", "reliability", "維運", "監控", "可觀測")):
        terms.extend(("operations", "observability", "monitoring", "reliability", "incident", "devops"))
    return list(dict.fromkeys(terms))


def _is_ci_cd_intent(demand_card: dict[str, Any]) -> bool:
    text = " ".join(
        [str(demand_card.get("problem_statement", "")), str(demand_card.get("desired_outcome", ""))]
    ).lower()
    return any(term in text for term in ("ci/cd", "ci cd", "github actions", "pipeline", "deployment", "build", "開發", "排查"))


def _make_candidate_id(run_id: str, title: str, source_url: str) -> str:
    digest = hashlib.sha1("|".join([run_id, title, source_url]).encode("utf-8")).hexdigest()[:12].upper()
    return f"S1-{digest}"


def _make_discovery_run_id(request: dict[str, Any]) -> str:
    """Generate a traceable run ID without needing a separate S0 artifact."""

    now = datetime.now(timezone.utc)
    seed = f"{now.isoformat()}|{request.get('discovery_scope')}|{request.get('problem_statement')}"
    return f"discovery-{now.strftime('%Y%m%d')}-{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:8]}"
