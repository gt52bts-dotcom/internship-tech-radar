"""Skill 3 評分準則：構面定義、逐級判定條件、以及每項輸入的來源階段。

這個模組是評分準則的**唯一來源**。分數由這裡的訊號決定，說明文件也從這裡產生，
所以文件不可能與實際行為不一致——兩者讀的是同一份資料。

三個設計約束：

1. **不得針對特定候選寫死分數。** 每一級的判定條件都必須是任何候選都適用的訊號。
   若某個候選得到不合理的分數，要修的是訊號定義，不是為它加一個分支。

2. **每項輸入都標示來源階段。** S1 提供原文與解釋層，S2 提供比較與提案卡，
   S3 自己產生報價與 recipe 判定。標示來源才能看出一個分數是建立在誰的產出上。

3. **證據不足與表現不佳要分開。** 缺乏證據時給中間值並標記，不與「確實表現差」
   混為一談；後者才應該落到否決門檻。
"""

from __future__ import annotations

import re
from typing import Any


# 來源階段標籤。用於報告中標示每項資訊由誰產生。
STAGE_S1 = "S1"
STAGE_S2 = "S2"
STAGE_S3 = "S3"

QUANTIFIED_PATTERN = re.compile(r"\d+\s*(%|％|倍|秒|分鐘|小時|GB|MB|TB|ms)")

# 只擴充既有能力、不改變做法的字樣。
EXPANSION_TERMS = ("配額", "quota", "區域", "region", "規格", "instance type", "size", "上限提高")


RUBRIC_CRITERIA: dict[str, dict[str, Any]] = {
    "technical_value": {
        "label": "技術能力",
        "weight": 0.30,
        "veto_at_or_below": None,
        "question": "這項能力相對於現有做法的改善幅度有多大？",
        "smi": "SMI Capability",
        "inputs": [
            {"field": "explanation.significance", "stage": STAGE_S1, "note": "以前／現在／差別三段對比"},
            {"field": "explanation.key_points", "stage": STAGE_S1, "note": "原文重點"},
            {"field": "proposal_card.improvement_hypothesis", "stage": STAGE_S2, "note": "改善假設向量"},
            {"field": "comparison_dimensions.delivery_model", "stage": STAGE_S2, "note": "交付模式"},
        ],
        "levels": [
            {"score": 5, "condition": "原文明述可量化的改善（含數字與單位），且說明改善機制",
             "evidence": "significance.difference 含數量詞，且 before／after 皆成立",
             "why": "有數字才談得上幅度；有機制才排除只是行銷語言"},
            {"score": 4, "condition": "原文明述質性改善並說明機制，但未提供量化數據",
             "evidence": "significance 三段完整，或改善向量存在且交付模式為受管服務",
             "why": "機制清楚即可判斷是否適用，缺數字只影響精確度不影響方向"},
            {"score": 3, "condition": "原文宣稱改善，但未說明改善機制",
             "evidence": "存在改善向量，但 significance 缺 before 或機制描述",
             "why": "無機制則無法判斷改善是否適用於自身情境"},
            {"score": 2, "condition": "屬既有能力的擴充（新區域、新規格、配額提高）",
             "evidence": "改善向量或原文重點僅出現擴充類字樣",
             "why": "擴充改變的是可用範圍，不是做法本身"},
            {"score": 1, "condition": "僅為介面或整合層的便利性改變",
             "evidence": "偵測到服務但無任何改善主張",
             "why": "便利性改變通常可由既有工具替代"},
            {"score": 0, "condition": "原文未主張任何改善",
             "evidence": "無 significance、無改善向量、無偵測服務",
             "why": "無主張即無評估對象"},
        ],
    },
    "verifiability": {
        "label": "證據可驗證性",
        "weight": 0.20,
        "veto_at_or_below": 1,
        "question": "新聞主張的核心能力，能否被一次受控實驗證實或推翻？",
        "smi": "SMI Assurance（證據可驗證性）",
        "inputs": [
            {"field": "proposal_card.validation_design", "stage": STAGE_S2, "note": "驗證設計與成功證據"},
            {"field": "poc_recipe.recipe.success_criteria", "stage": STAGE_S3, "note": "recipe 成功條件"},
            {"field": "explanation.significance", "stage": STAGE_S1, "note": "核心主張內容"},
        ],
        "levels": [
            {"score": 5, "condition": "核心主張可由明確的通過／失敗條件驗證，且條件已寫入可部署 recipe",
             "evidence": "recipe 已登錄，且驗證設計含成功證據與前後量測",
             "why": "寫進 recipe 才代表驗證會真的執行，而非停留在設計"},
            {"score": 4, "condition": "來源已提供足夠實作線索，且已有成功證據與前後量測，但尚未寫入 recipe",
             "evidence": "驗證設計完整，且 S1/S2 至少能支撐最小架構與多個原文明述元件",
             "why": "設計必須被來源實作線索支撐，否則只是 AI 推導的測試想像"},
            {"score": 3, "condition": "只能驗證部分主張，核心能力未納入成功條件",
             "evidence": "recipe 已登錄但成功條件未涵蓋核心主張；或缺前後量測",
             "why": "能證明建得起來，不等於證明新聞說的效果"},
            {"score": 2, "condition": "只能驗證周邊事實，核心主張無法檢驗",
             "evidence": "僅有成功證據或僅有前後量測其一",
             "why": "周邊事實不構成對主張的檢驗"},
            {"score": 1, "condition": "來源缺少實作細節，無法定義來源支撐的可否證實驗",
             "evidence": "無 recipe 成功條件，且最小架構主要是 inferred/drafted 或只有一個原文明述元件",
             "why": "沒有資源清單、資料流、權限、成功條件或部署步驟時，PoC 設計只是推測，不能提高可驗證性"},
            {"score": 0, "condition": "無任何可驗證內容",
             "evidence": "無主張亦無驗證設計",
             "why": "無可檢驗對象"},
        ],
    },
    "adoption_prerequisites": {
        "label": "導入前置條件",
        "weight": 0.20,
        "veto_at_or_below": None,
        "question": "導入所需的前置條件有多少、取得難度多高？",
        "smi": "SMI Agility",
        "inputs": [
            {"field": "region_status", "stage": STAGE_S2, "note": "目標區域證據狀態"},
            {"field": "poc_recipe.recipe.required_aws_services", "stage": STAGE_S3, "note": "所需服務數"},
            {"field": "poc_recipe.recipe.required_region_capabilities", "stage": STAGE_S3, "note": "所需區域能力"},
            {"field": "cost_estimate.quote.exclusions", "stage": STAGE_S3, "note": "授權與採購前提"},
        ],
        "levels": [
            {"score": 5, "condition": "現有帳號可直接使用，無需申請、無需新環境",
             "evidence": "前置條件計數為 0",
             "why": "可立即開始，導入摩擦最低"},
            {"score": 4, "condition": "需要建立標準資源，但無需申請或審核",
             "evidence": "前置條件計數為 1",
             "why": "可自行完成，不受他人排程影響"},
            {"score": 3, "condition": "需要一項需申請或審核的前置條件",
             "evidence": "前置條件計數為 2",
             "why": "引入等待時間，但範圍可控"},
            {"score": 2, "condition": "需要兩項以上前置條件，或需要新的授權模式",
             "evidence": "前置條件計數為 3，或報價載明授權待確認",
             "why": "多項並行等待，導入時程難以估計"},
            {"score": 1, "condition": "需要組織層級變更或跨部門協調",
             "evidence": "前置條件計數為 4 以上",
             "why": "超出單一團隊可決定的範圍"},
            {"score": 0, "condition": "現行環境無法滿足",
             "evidence": "區域明確不支援且無可接受替代",
             "why": "無法導入"},
        ],
        "prerequisite_signals": [
            "目標區域未經功能層級確認",
            "recipe 需要兩項以上區域能力",
            "recipe 需要四項以上 AWS 服務",
            "報價載明授權模式或採購前提待確認",
            "recipe 標記需要環境準備",
        ],
    },
    "risk_and_stop_conditions": {
        "label": "可控制性與停止機制",
        "weight": 0.15,
        "veto_at_or_below": 2,
        "question": "PoC 證據不支持原判斷、部署異常或前提不明時，AI/流程能否承認問題並暫停行動？",
        "smi": "SMI Assurance（風險可停止性）",
        "inputs": [
            {"field": "proposal_card.validation_design.stop_conditions", "stage": STAGE_S2, "note": "AI/流程何時必須停止或改成人工判斷"},
            {"field": "comparison_dimensions.unknowns", "stage": STAGE_S2, "note": "未知項目是否多到必須承認證據不足"},
            {"field": "poc_blockers / veto_violations", "stage": STAGE_S3, "note": "是否能把 blocker 視為暫停訊號，而不是硬做 PoC"},
        ],
        "levels": [
            {"score": 5, "condition": "停止條件已定義且可自動觸發，AI 能在證據不支持時停止下一步",
             "evidence": "停止條件存在，未知項少於四項，且有明確 abort / awaiting human gate 訊號",
             "why": "重點不是把流程跑完，而是能在判斷錯誤或證據不足時先停住"},
            {"score": 4, "condition": "停止條件已定義，AI 能標出風險並等待人工判斷",
             "evidence": "停止條件存在，未知項少於四項",
             "why": "流程知道不能硬做，但暫停時機仍依賴人類確認"},
            {"score": 3, "condition": "有停止條件但涵蓋不全，AI 可能太晚承認證據不足",
             "evidence": "停止條件存在，未知項四項以上",
             "why": "未知項太多時，AI 可能仍能停，但容易誤判何時該停"},
            {"score": 2, "condition": "停止條件模糊，AI 只能事後標記風險，無法在行動前暫停",
             "evidence": "只有泛用風險提示，沒有明確 blocker、abort path 或人工 gate",
             "why": "看得出有風險，但不足以阻止錯誤行動繼續發生"},
            {"score": 1, "condition": "未定義停止條件，AI 無法知道何時該承認錯誤並暫停",
             "evidence": "無停止條件",
             "why": "沒有事先定義，模型容易把不確定當成可繼續推進"},
            {"score": 0, "condition": "無任何中止途徑",
             "evidence": "無停止條件且無清除策略",
             "why": "無法停止"},
        ],
    },
    "reversibility_and_cleanup": {
        "label": "可逆性與終止",
        "weight": 0.15,
        "veto_at_or_below": 1,
        "question": "停止之後，已發生的支出能否收回？",
        "smi": "SMI Accountability / ISO/IEC 19086-1 可逆性與終止程序",
        "inputs": [
            {"field": "cost_estimate.quote.scenarios[].line_items", "stage": STAGE_S3, "note": "費率表計價單位"},
            {"field": "poc_recipe.recipe.cleanup_strategy", "stage": STAGE_S3, "note": "清除策略"},
            {"field": "poc_recipe.recipe.cleanup_verification", "stage": STAGE_S3, "note": "清除後回查"},
        ],
        "levels": [
            {"score": 5, "condition": "資源清除即停止計費，且 recipe 已宣告清除策略與清除後回查",
             "evidence": "費率表無非按比例計費項目，且清除策略與回查皆已宣告",
             "why": "宣告清除與驗證清除是兩回事，兩者齊備才算可逆"},
            {"score": 3, "condition": "含持續計費資源，但未宣告清除策略或回查",
             "evidence": "費率表含小時計費項目，recipe 未宣告清除或回查",
             "why": "可停但無人確認是否真的停了"},
            {"score": 1, "condition": "費率表存在不隨清除退回的費用",
             "evidence": "計價單位或公式含按月計收、預付或最低承諾",
             "why": "清除對這部分支出無效，成本在啟動瞬間即已固定"},
            {"score": 0, "condition": "無明確清除途徑",
             "evidence": "recipe 未宣告清除策略且無資源範圍",
             "why": "無法終止"},
        ],
    },
}

VETO_THRESHOLDS = {
    name: spec["veto_at_or_below"]
    for name, spec in RUBRIC_CRITERIA.items()
    if spec["veto_at_or_below"] is not None
}

WEIGHTS = {name: spec["weight"] for name, spec in RUBRIC_CRITERIA.items()}


# --------------------------------------------------------------------------
# 訊號抽取：所有評分只讀這裡定義的訊號，不得針對特定候選寫死
# --------------------------------------------------------------------------


def _text_of(*values: Any) -> str:
    return " ".join(str(v or "") for v in values).lower()


def score_technical_value(
    explanation: dict[str, Any], proposal: dict[str, Any], dimensions: dict[str, Any]
) -> tuple[int, str]:
    significance = explanation.get("significance") or {}
    vectors = (proposal.get("improvement_hypothesis") or {}).get("potential_vectors") or []
    key_points = [str(item.get("point") or "") for item in explanation.get("key_points") or []]
    delivery = str((dimensions.get("delivery_model") or {}).get("classification") or "").lower()

    derived = significance.get("status") == "derived" or bool(
        significance.get("before") and significance.get("after")
    )
    difference = str(significance.get("difference") or "")
    has_before = bool(significance.get("before"))
    quantified = bool(QUANTIFIED_PATTERN.search(difference))
    claim_text = _text_of(difference, *key_points, *[str(v) for v in vectors])
    expansion_only = bool(claim_text) and any(t in claim_text for t in EXPANSION_TERMS) and not derived

    if derived and has_before and quantified:
        return 5, "原文明述可量化的改善並說明前後差異。"
    if expansion_only:
        return 2, "改善內容屬既有能力的擴充（區域、規格或配額）。"
    if derived and has_before:
        return 4, "原文明述質性改善並說明改變機制，但未提供量化數據。"
    if derived or vectors or "managed" in delivery:
        return 3, "原文宣稱改善，但改善機制未充分說明。"
    if (dimensions.get("technology_scope") or {}).get("services_detected"):
        return 1, "只看得到服務或整合層變化，未形成明確技術改善主張。"
    return 0, "原文未主張任何改善。"


def score_verifiability(
    proposal: dict[str, Any], recipe_decision: dict[str, Any], explanation: dict[str, Any]
) -> tuple[int, str]:
    validation = proposal.get("validation_design") or {}
    has_success_evidence = bool(validation.get("minimum_success_evidence"))
    has_before_after = bool(validation.get("before_measurements") and validation.get("after_measurements"))
    recipe = recipe_decision.get("recipe") or {}
    registered = bool(recipe_decision.get("deployable_recipe_registered"))
    criteria = [str(item) for item in recipe.get("success_criteria") or []]
    architecture = explanation.get("implementation_architecture") or {}
    architecture_status = str(architecture.get("status") or "")
    stated_components = [
        item for item in architecture.get("core_components") or []
        if item.get("stated_in_source")
    ]
    lacks_source_backed_implementation = (
        not registered
        and architecture_status in {"needs_service_evidence", "drafted"}
        and len(stated_components) <= 1
    )

    # 核心主張是否被 recipe 的成功條件涵蓋：以 significance 的關鍵動詞比對。
    significance = explanation.get("significance") or {}
    claim = _text_of(significance.get("after"), significance.get("difference"))
    claim_terms = {word for word in re.findall(r"[a-z]{4,}|[\u4e00-\u9fff]{2,}", claim)}
    criteria_text = _text_of(*criteria)
    covered = bool(claim_terms) and any(term in criteria_text for term in claim_terms)

    if registered and covered and has_success_evidence and has_before_after:
        return 5, "核心主張可由明確通過／失敗條件驗證，且已寫入可部署 recipe。"
    if registered and not covered:
        return 3, "recipe 的成功條件未涵蓋核心主張，只能驗證周邊事實。"
    if lacks_source_backed_implementation:
        return 1, "來源缺少可部署實作細節；目前的驗證設計主要是 AI 推導，無法支撐可否證 PoC。"
    if has_success_evidence and has_before_after:
        return 4, "驗證設計完整，但尚未寫入可部署 recipe 的成功條件。"
    if has_success_evidence or has_before_after:
        return 2, "只能驗證部分周邊事實，核心主張未被檢驗。"
    if registered:
        return 3, "已有 recipe 成功條件，但缺乏前後量測設計。"
    return 1, "無驗證設計，也無 recipe 成功條件，主張目前不可否證。"


def score_adoption_prerequisites(
    region: dict[str, Any], recipe_decision: dict[str, Any], quote: dict[str, Any]
) -> tuple[int, str]:
    recipe = recipe_decision.get("recipe") or {}
    reasons: list[str] = []

    region_status = str(region.get("status") or "")
    if region_status not in {"feature_confirmed", "available_ap_southeast_1"} or region.get(
        "requires_region_confirmation"
    ):
        reasons.append("目標區域未經功能層級確認")
    if len(recipe.get("required_region_capabilities") or []) >= 2:
        reasons.append("需要兩項以上區域能力")
    if len(recipe.get("required_aws_services") or []) >= 4:
        reasons.append("需要四項以上 AWS 服務")
    exclusions = _text_of(*(quote.get("exclusions") or []))
    if any(t in exclusions for t in ("授權", "licens", "byol", "採購")):
        reasons.append("授權模式或採購前提待確認")
    if recipe.get("blocking_flags"):
        reasons.append("recipe 標記尚需環境準備")

    count = len(reasons)
    note = "；".join(reasons) if reasons else "未偵測到額外前置條件"
    if count == 0:
        return 5, f"現有帳號可直接使用（{note}）。"
    if count == 1:
        return 4, f"需要建立標準資源：{note}。"
    if count == 2:
        return 3, f"需要一項需申請或審核的前置條件：{note}。"
    if count == 3:
        return 2, f"前置條件多且部分需審查：{note}。"
    return 1, f"前置條件涉及組織層級或跨部門協調：{note}。"


def score_risk_and_stop_conditions(
    stop_conditions: list[str], unknowns: list[str], quote: dict[str, Any]
) -> tuple[int, str]:
    del quote

    if not stop_conditions:
        return 1, "未定義停止條件，AI 無法知道何時該承認錯誤並暫停。"
    if len(unknowns) >= 4:
        return 3, "已定義停止條件，但未知項目較多，AI 可能太晚承認證據不足。"
    return 4, "停止條件已定義，AI 能標出風險並等待人工判斷。"


def score_reversibility(quote: dict[str, Any], recipe_decision: dict[str, Any]) -> tuple[int, str]:
    scenarios = (quote or {}).get("scenarios") or {}
    items: list[dict[str, Any]] = []
    for scenario in scenarios.values():
        items.extend(scenario.get("line_items") or [])
    containment = (quote or {}).get("cost_containment_model") or {}
    if containment.get("cleanup_cannot_refund"):
        names = "、".join(str(x) for x in containment["cleanup_cannot_refund"][:2])
        return 1, f"費率表存在不隨清除退回的費用：{names}。清除無法止血。"
    if not items:
        return 3, "報價無明細，無法判定清除是否止血。"

    def text(item: dict[str, Any]) -> str:
        return _text_of(item.get("formula"), item.get("quantity_unit"))

    if any(
        token in text(item)
        for item in items
        for token in ("user-month", "per month", "/month", "monthly", "minimum commitment", "prepaid")
    ):
        return 1, "費率表含按月計收或預付項目，清除無法止血。"

    recipe = (recipe_decision or {}).get("recipe") or {}
    has_teardown = bool(recipe.get("cleanup_strategy")) and bool(recipe.get("cleanup_verification"))
    if not has_teardown:
        return 3, "尚無已登錄 recipe 的清除策略與回查方式，無法確認清除是否真的止血。"
    always_on = any(
        token in text(item)
        for item in items
        for token in ("instance-hour", "gateway-hour", "provisioned", "reserved")
    )
    if always_on and not has_teardown:
        return 3, "含持續計費資源，但 recipe 未宣告清除策略與清除後回查。"
    return 5, "資源清除即停止計費，且 recipe 已宣告清除與回查方式。"


# --------------------------------------------------------------------------
# 說明文件由同一份資料產生，因此不可能與行為不一致
# --------------------------------------------------------------------------


def render_criteria_markdown() -> str:
    lines = [
        "# Skill 3 評分準則",
        "",
        "本文件由 `agentic_cloud_radar/rubric.py` 產生，與實際評分讀取同一份定義，"
        "不會出現文件與行為不一致的情況。重新產生：",
        "",
        "```powershell",
        "python -m agentic_cloud_radar.cli rubric --output docs\\評分準則.md",
        "```",
        "",
        "## SMI 對應",
        "",
        "`SMI` 是 Service Measurement Index，這裡只拿來當雲服務評估面向的參考標籤，"
        "例如 Capability、Assurance、Agility、Accountability。它不另外計分，也不是另一個 gate；"
        "真正影響 Skill 3 結果的是構面分數、權重、否決門檻與 blocker。",
        "",
        "## 彙總",
        "",
        "| 構面 | 權重（加權計算） | 否決門檻 | SMI 對應 | 評的是什麼 |",
        "| --- | ---: | :---: | --- | --- |",
    ]
    for name, spec in RUBRIC_CRITERIA.items():
        floor = spec["veto_at_or_below"]
        weight = float(spec["weight"])
        lines.append(
            f"| {spec['label']} | {weight:g}（分數 × {weight:g}） | "
            f"{('≤ ' + str(floor)) if floor is not None else '—'} | {spec['smi']} | {spec['question']} |"
        )
    lines.extend([
        "",
        "**加權分**：Skill 3 報告中的每一列加權分，都是該構面的 `分數 × 權重`。"
        "總分是所有構面加權分相加，滿分仍是 5 分。",
        "",
        "**否決門檻**：任一構面分數觸及門檻，該候選一律不得進入 Skill 4，"
        "不論加權總分。加權總和是完全補償性彙總，單一構面的嚴重缺陷會被其他構面抵銷；"
        "設下限是為了讓那些缺陷無法被抵銷。",
        "",
        "**通過門檻**：加權分 ≥ 3.75，且無否決、無 blocker。",
        "",
    ])

    for name, spec in RUBRIC_CRITERIA.items():
        lines.extend([
            f"## {spec['label']}（權重 {spec['weight']}）",
            "",
            f"**評的是什麼**：{spec['question']}",
            "",
            "### 判定所需的輸入與來源",
            "",
            "| 欄位 | 由誰產生 | 用途 |",
            "| --- | :---: | --- |",
        ])
        for item in spec["inputs"]:
            lines.append(f"| `{item['field']}` | {item['stage']} | {item['note']} |")
        lines.extend(["", "### 逐級判定條件", "", "| 分數 | 條件 | 判定依據 | 為什麼是這一級 |", "| :---: | --- | --- | --- |"])
        for level in spec["levels"]:
            lines.append(
                f"| **{level['score']}** | {level['condition']} | {level['evidence']} | {level['why']} |"
            )
        if spec.get("prerequisite_signals"):
            lines.extend(["", "### 前置條件的計數依據", "",
                          "分數 = 5 − 命中項數（最低 1）。命中的項目會列在報告的判定理由中。", ""])
            for signal in spec["prerequisite_signals"]:
                lines.append(f"- {signal}")
        lines.append("")

    lines.extend([
        "## 兩條共通規則",
        "",
        "**不得為特定候選寫死分數。** 每一級的判定條件都必須是任何候選都適用的訊號。"
        "若某個候選得到不合理的分數，要修的是訊號定義，不是為它加一個分支——"
        "否則評分準則就退化成查表，個案結果也不能作為方法有效的證據。",
        "",
        "**證據不足與表現不佳要分開。** 缺乏證據時給中間值並在理由中標明；"
        "確實表現差才落到否決門檻。把兩者混為一談，會讓「文件寫得少」看起來像「技術不好」。",
    ])
    return "\n".join(lines) + "\n"
