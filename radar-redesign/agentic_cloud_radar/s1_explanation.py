"""S1 explanation layer: distil a fetched source into reviewable structure.

The scan artifact keeps two separate layers.  The evidence layer holds text the
page actually contains.  This module builds the explanation layer on top of it:
key points, an implementation architecture sketch, why the change matters, and
where it might apply.

Every explanation entry carries a ``derivation`` tag and, where the wording
comes from the page, an ``evidence_span`` into the same text the scan recorded.
Nothing here invents a fact.  Anything the page does not state is marked so a
later stage can keep it out of the verified-fact list:

    source_verbatim        the page says this
    derived_summary        compressed from the page, no new fact
    inferred_architecture  needed to implement, not necessarily stated
    hypothesis             plausible application, unproven

The whole module is deterministic: same text in, same structure out.  It uses
ordered rules rather than a model so a reviewer can replay any line.
"""

from __future__ import annotations

import re
from typing import Any


MAX_KEY_POINTS = 5
MAX_APPLICATION_CONTEXTS = 4
MIN_SENTENCE_CHARS = 12

CAPABILITY_TERMS = (
    "支援", "現在可", "可直接", "無需", "不需", "讓您", "新增", "提供", "允許",
    "now supports", "you can now", "no longer", "without", "removes", "enables",
    "introduces", "adds", "allows",
)
BENEFIT_TERMS = (
    "縮短", "消除", "提升", "改善", "降低", "減少", "加快", "節省", "避免",
    "eliminates", "reduces", "improves", "faster", "lower", "shortens", "saves",
    "avoids", "speeds",
)
PRIOR_STATE_TERMS = (
    "先前", "以前", "過去", "原本", "舊有", "一律會",
    "previously", "used to", "before this", "in the past", "until now",
)
NEW_STATE_TERMS = (
    "現在", "自即日起", "從今天起",
    "now supports", "you can now", "is now", "starting today",
)
PAIN_TERMS = (
    "限制", "配額", "上限", "必須", "支援工單", "瓶頸", "延遲", "問題", "困難",
    "quota", "limit", "bottleneck", "latency", "support ticket", "constraint",
    "manual", "workaround",
)
MARKETING_TERMS = (
    "了解更多", "了解有關", "更多信息", "更多資訊", "立即開始", "免費", "定價頁面", "請參閱", "部落格",
    "learn more", "get started", "sign up", "read the blog", "available now in the console",
)

# Roles are keyed on the service names the scan detector already emits.
SERVICE_ROLES = {
    "Lambda": "無伺服器函數執行",
    "S3": "物件儲存",
    "EC2": "運算執行個體",
    "EBS": "區塊儲存",
    "CloudFormation": "基礎設施即程式碼部署",
    "IAM": "身分與存取授權",
    "CloudWatch": "日誌與指標",
    "Glue": "資料目錄與 ETL",
    "Athena": "查詢引擎",
    "DynamoDB": "NoSQL 資料表",
    "SQS": "訊息佇列",
    "SNS": "發布訂閱通知",
    "LakeFormation": "資料湖權限治理",
    "Connect": "客服聯絡中心",
    "Bedrock": "基礎模型推論",
}

# Components almost every deployable AWS PoC needs even when no page mentions
# them.  Recording them as unstated is the point: they are what a reviewer asks
# about and what a Skill 4 recipe draft has to supply.
IMPLICIT_COMPONENTS = {
    "IAM": "授予各資源之間所需的最小權限",
    "CloudWatch": "接收執行日誌，預設 log group 會產生費用",
}


def build_explanation(
    title: str,
    description: str,
    article_text: str,
    related_services: list[str],
    demand_card: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the explanation block for one candidate."""

    source_text = _strip_lead(_compact(" ".join([description or "", article_text or ""])), title)
    sentences = _sentences(source_text)
    key_points = _key_points(sentences)
    return {
        "derivation_legend": {
            "source_verbatim": "頁面原文即有此陳述",
            "derived_summary": "由原文壓縮，未加入新事實",
            "inferred_architecture": "實作所需，原文未必提及",
            "hypothesis": "可能的應用，尚未證實",
        },
        "evidence_text": source_text,
        "evidence_text_note": "所有 evidence_span 都是這段 evidence_text 的字元區間；重播時請以此欄位為準，勿用 fetched_source.text_excerpt。",
        "key_points": key_points,
        "significance": _significance(title, sentences, key_points),
        "implementation_architecture": _architecture(related_services, source_text),
        "possible_application_contexts": _application_contexts(sentences, demand_card),
        "explanation_gaps": _gaps(key_points, related_services, sentences),
    }


def _sentences(source_text: str) -> list[dict[str, Any]]:
    """Split into sentences and keep each one's offset into the source text."""

    spans: list[dict[str, Any]] = []
    cursor = 0
    for raw in re.split(r"(?<=[。！？；])|(?<=[.!?])\s+", source_text):
        piece = raw.strip()
        if not piece:
            continue
        start = source_text.find(piece, cursor)
        if start < 0:
            continue
        cursor = start + len(piece)
        if len(piece) < MIN_SENTENCE_CHARS:
            continue
        spans.append({"text": piece, "span": [start, cursor]})
    return spans


def _score(text: str) -> int:
    lowered = text.lower()
    score = 0
    for term in CAPABILITY_TERMS:
        if term in lowered or term in text:
            score += 3
    for term in BENEFIT_TERMS:
        if term in lowered or term in text:
            score += 2
    for term in PAIN_TERMS:
        if term in lowered or term in text:
            score += 2
    for term in MARKETING_TERMS:
        if term in lowered or term in text:
            score -= 4
    return score


def _key_points(sentences: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pick the sentences that carry capability, benefit, or pain information."""

    ranked = sorted(
        ({**item, "score": _score(item["text"])} for item in sentences),
        key=lambda item: (-item["score"], item["span"][0]),
    )
    points: list[dict[str, Any]] = []
    for index, item in enumerate(ranked[:MAX_KEY_POINTS], start=1):
        if item["score"] <= 0:
            continue
        points.append(
            {
                "id": f"KP-{index}",
                "point": item["text"],
                "evidence_span": item["span"],
                "derivation": "source_verbatim",
                "signal_score": item["score"],
            }
        )
    points.sort(key=lambda item: item["evidence_span"][0])
    for index, point in enumerate(points, start=1):
        point["id"] = f"KP-{index}"
    return points


def _significance(title: str, sentences: list[dict[str, Any]], key_points: list[dict[str, Any]]) -> dict[str, Any]:
    """State what changed as before/after, supported by recorded key points."""

    after = next((item for item in sentences if _has(item["text"], NEW_STATE_TERMS)), None) or next(
        (item for item in sentences if _has(item["text"], CAPABILITY_TERMS)), None
    )
    used = {id(after)} if after else set()
    before = next(
        (item for item in sentences if _has(item["text"], PRIOR_STATE_TERMS) and id(item) not in used),
        None,
    ) or next(
        (item for item in sentences if _has(item["text"], PAIN_TERMS) and id(item) not in used),
        None,
    )
    if before:
        used.add(id(before))
    benefit = next(
        (item for item in sentences if _has(item["text"], BENEFIT_TERMS) and id(item) not in used),
        None,
    )
    supported_by = [point["id"] for point in key_points]
    if not (before or after):
        return {
            "status": "not_derivable",
            "derivation": "derived_summary",
            "supported_by": supported_by,
            "note": "取回的頁面文字不足以整理出改變前後的對比。",
        }
    return {
        "status": "derived",
        "derivation": "derived_summary",
        "supported_by": supported_by,
        "subject": title,
        "before": before["text"] if before else "原文未描述先前做法。",
        "before_span": before["span"] if before else None,
        "after": after["text"] if after else "原文未描述新的做法。",
        "after_span": after["span"] if after else None,
        "difference": benefit["text"] if benefit else "原文未量化改善幅度。",
        "difference_span": benefit["span"] if benefit else None,
        "limits": [
            "這是原文陳述的壓縮，不是實測結果。",
            "任何量化改善若原文未給數據，仍屬未驗證。",
        ],
    }


def _architecture(related_services: list[str], source_text: str) -> dict[str, Any]:
    """Sketch the minimum shape a PoC of this capability would take."""

    stated = [name for name in related_services if name in SERVICE_ROLES]
    components = [
        {
            "service": name,
            "role": SERVICE_ROLES[name],
            "stated_in_source": True,
            "derivation": "source_verbatim",
        }
        for name in stated
    ]
    for name, role in IMPLICIT_COMPONENTS.items():
        if name in stated:
            continue
        components.append(
            {
                "service": name,
                "role": role,
                "stated_in_source": False,
                "derivation": "inferred_architecture",
            }
        )
    unstated = [item["service"] for item in components if not item["stated_in_source"]]
    if not stated:
        return {
            "status": "needs_service_evidence",
            "derivation": "inferred_architecture",
            "core_components": components,
            "note": "頁面文字未偵測到受支援的 AWS 服務名稱，無法草擬架構。",
            "unstated_prerequisites": unstated,
        }
    return {
        "status": "drafted",
        "derivation": "inferred_architecture",
        "core_components": components,
        "data_flow": " → ".join(f"{item['service']}（{item['role']}）" for item in components if item["stated_in_source"]),
        "minimal_poc_shape": [
            f"建立 {name}（{SERVICE_ROLES[name]}）" for name in stated
        ]
        + ["以最小輸入執行一次，確認回讀結果符合預期"],
        "unstated_prerequisites": unstated,
        "recipe_draft_hint": "此草案供 Skill 4 在候選未登錄 recipe 時交由人工審閱，不得直接部署。",
        "limits": [
            "元件由偵測到的服務名稱推導，不是官方參考架構。",
            "標記 stated_in_source=false 的元件原文未提及，需人工確認。",
        ],
    }


def _application_contexts(
    sentences: list[dict[str, Any]],
    demand_card: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Combine the operator's stated demand with contexts the page describes."""

    contexts: list[dict[str, Any]] = []
    card = demand_card or {}
    for field in ("business_domain", "problem_statement"):
        value = str(card.get(field, "")).strip()
        if value:
            contexts.append(
                {
                    "context": value,
                    "derivation": "source_verbatim",
                    "origin": f"demand_card.{field}",
                }
            )
    for item in sentences:
        if len(contexts) >= MAX_APPLICATION_CONTEXTS:
            break
        if not _has(item["text"], PAIN_TERMS):
            continue
        contexts.append(
            {
                "context": item["text"],
                "derivation": "hypothesis",
                "origin": "fetched_source",
                "evidence_span": item["span"],
                "assumption": "原文描述了這個情境，但未證實此功能能解決你的工作負載。",
            }
        )
    return contexts[:MAX_APPLICATION_CONTEXTS]


def _gaps(
    key_points: list[dict[str, Any]],
    related_services: list[str],
    sentences: list[dict[str, Any]],
) -> list[str]:
    gaps: list[str] = []
    if not sentences:
        gaps.append("取回的頁面沒有可供整理的內文。")
    if not key_points:
        gaps.append("頁面文字沒有可辨識的能力、效益或痛點陳述，無法整理重點。")
    if not related_services:
        gaps.append("未偵測到受支援的 AWS 服務，實作架構僅能列出通用前提。")
    return gaps


def _has(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(term in lowered or term in text for term in terms)


def _strip_lead(source_text: str, title: str) -> str:
    """Drop the meta-description and repeated title that precede the article.

    Fetched AWS pages often begin with a boilerplate lead-in and the headline
    twice.  Cutting to the last headline occurrence inside the opening keeps
    the offsets honest for everything that follows, because the trim happens
    once, before any span is recorded.
    """

    headline = _compact(title or "").split(" - ")[0].strip()
    if not headline:
        return source_text
    opening = source_text[:400]
    last = opening.rfind(headline)
    if last <= 0:
        return source_text
    return source_text[last:].strip()


def _compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
