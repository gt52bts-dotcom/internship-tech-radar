var radarConfig = window.RADAR_CONFIG || { apiBaseUrl: "http://127.0.0.1:8080/api" };
var radarState = { runId: null, s1: null, s2: null, s3: null, s4: null, s5: null, selectedId: null };
var radarStages = [
  {
    code: "S1", name: "掃描", en: "SCAN", title: "Skill 1 Scan", sub: "公開來源與政策檢查",
    hint: "貼入一篇 AWS 官方消息，讓圓圓搬運可回查的來源訊號。",
    labels: ["URL", "AWS", "GA"],
    focus: "蒐集可回查的官方訊號，不把推論當成證據。",
    checklist: ["官方 HTTPS URL", "GA 訊號", "政策排除檢查"]
  },
  {
    code: "S2", name: "比較", en: "COMPARE", title: "Skill 2 Compare", sub: "候選證據卡與資料缺口",
    hint: "把已證實、規劃推論與未知資料拆開，才不會把希望當成證據。",
    labels: ["FACT", "GAP", "REGION"],
    focus: "建立每個候選的官方證據卡，並保留 region 與定價缺口。",
    checklist: ["官方事實", "region warning", "官方價格來源"]
  },
  {
    code: "S3", name: "評估", en: "EVALUATE", title: "Skill 3 Evaluate", sub: "真人 shortlist 與固定 rubric",
    hint: "真人先選候選，再用固定 rubric 評估，不讓權重隨候選改變。",
    labels: ["PROBLEM", "ENV", "BOUNDARY"],
    focus: "真人選擇候選即可評估；問題、環境與邊界可在知道後再補充。",
    checklist: ["真人選擇候選", "固定 rubric", "PoC 估算報價單"]
  },
  {
    code: "S4", name: "驗證", en: "VALIDATE", title: "Skill 4 Validate", sub: "受控驗證與完整 PoC Gate",
    hint: "低風險驗證可以前進；完整 PoC 必須保留人工核准。",
    labels: ["APPROVE", "BUDGET", "CLEANUP"],
    focus: "先建立可回查的驗證 artifact，再決定是否進入完整 PoC。",
    checklist: ["具名核准", "成本上限", "Console review 與 cleanup"]
  },
  {
    code: "S5", name: "報告", en: "REPORT", title: "Skill 5 Report", sub: "artifact-only 評估報告",
    hint: "每句結論都有 artifact；沒有證據的地方就保留為 unknown。",
    labels: ["LEDGER", "REPORT", "REVIEW"],
    focus: "將評估、驗證與待確認事項整理成可交接的決策包。",
    checklist: ["證據帳本", "unknown 不補造", "人工 PoC review"]
  }
];

function radarEscape(value) {
  return String(value == null ? "" : value).replace(/[&<>"']/g, function (character) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[character];
  });
}

function radarApi(path, options) {
  var base = radarConfig.apiBaseUrl.replace(/\/$/, "");
  return fetch(base + path, Object.assign({ headers: { "Content-Type": "application/json" } }, options || {})).then(function (response) {
    return response.json().then(function (payload) {
      if (!response.ok) throw new Error(payload.message || "Radar API request failed");
      return payload;
    });
  });
}

function radarPanelMarkup(index, metrics, statusText) {
  var stage = radarStages[index];
  var checks = stage.checklist.map(function (item, itemIndex) {
    return "<li><span>" + (itemIndex + 1) + "</span>" + radarEscape(item) + "</li>";
  }).join("");
  var progress = radarStages.map(function (_, stageIndex) {
    var state = stageIndex < index ? "done" : stageIndex === index ? "active" : "";
    return "<i class=\"" + state + "\"></i>";
  }).join("");
  var summary = statusText || stage.focus;
  return "<section class=\"radar-panel\">" +
    "<div class=\"radar-panel-top\"><div><span class=\"radar-eyebrow\">流程進度</span><strong>第 " + (index + 1) + " 關 <em>/ 5</em></strong></div><span class=\"radar-code\">" + stage.code + "</span></div>" +
    "<div class=\"radar-progress\">" + progress + "</div>" +
    "<div class=\"radar-focus\"><span>本關目標</span><p>" + radarEscape(summary) + "</p></div>" +
    "<div class=\"radar-checklist\"><span>完成這一關，需要</span><ul>" + checks + "</ul></div>" +
    "<div class=\"radar-metrics\">" + metrics.map(function (metric) {
      return "<div><span>" + radarEscape(metric.label) + "</span><b>" + radarEscape(metric.value) + "</b></div>";
    }).join("") + "</div>" +
    "</section>";
}

function radarSetStage(index, entries, metrics, statusText) {
  var stage = radarStages[index];
  station = index;
  total = Math.max(total, index * 3);
  pts = total * 10;
  document.getElementById("pts").textContent = pts;
  document.getElementById("cnt").textContent = total;
  document.getElementById("bTitle").textContent = stage.title;
  document.getElementById("bSub").textContent = stage.sub + (radarState.runId ? " · " + radarState.runId.slice(-8) : "");
  document.getElementById("hint").innerHTML = "<b>第 " + (index + 1) + " 關 / 5 · " + stage.name + "</b>　" + stage.hint;
  document.getElementById("boardContext").innerHTML = radarPanelMarkup(index, metrics, statusText);
  document.getElementById("log").innerHTML = entries.map(function (entry, entryIndex) {
    return "<div class=\"ln\" style=\"animation-delay:" + (entryIndex * 0.06) + "s\">" + entry + "</div>";
  }).join("");
  document.getElementById("metrics").innerHTML = "";
  radarSpawnBlocks();
  layout();
  placeYuan();
}

function radarSpawnBlocks() {
  var stage = radarStages[station];
  var wrap = document.getElementById("blocks");
  var width = document.getElementById("stage").clientWidth;
  wrap.innerHTML = "";
  blocks = stage.labels.map(function (label, index) {
    var block = document.createElement("div");
    block.className = "block " + (index % 2 ? "red" : "blue") + " radar-block";
    block.innerHTML = "<div class=\"cube\">" + radarEscape(label) + "</div>";
    block.style.left = Math.max(26, width - 120 - index * 105) + "px";
    wrap.appendChild(block);
    return { el: block, idx: index, eaten: false };
  });
}

function radarSetBusy(message) {
  var focus = document.querySelector(".radar-focus p");
  if (focus) focus.textContent = message;
  var panel = document.querySelector(".radar-panel");
  if (panel) panel.classList.add("is-busy");
}

function radarFinishCurrentStage(nextIndex, callback) {
  var pending = blocks.filter(function (block) { return !block.eaten; });
  var blockIndex = 0;
  function eatNextBlock() {
    if (blockIndex >= pending.length) {
      radarJump(nextIndex, callback);
      return;
    }
    eat(pending[blockIndex]);
    blockIndex += 1;
    setTimeout(eatNextBlock, 520);
  }
  eatNextBlock();
}

function radarJump(nextIndex, callback) {
  if (nextIndex == null || nextIndex === station) {
    callback();
    return;
  }
  var current = platRects[station];
  var next = platRects[nextIndex];
  var yuanElement = document.getElementById("yuan");
  yuanElement.classList.remove("bob");
  sfx.jump();
  yuanElement.animate([
    { transform: "translate(0,0)" },
    { transform: "translate(" + ((next.left - current.left) * 0.5) + "px," + (-((next.top - current.top) + 76)) + "px)", offset: 0.5 },
    { transform: "translate(" + (next.left - current.left) + "px," + (-(next.top - current.top)) + "px)" }
  ], { duration: 660, easing: "cubic-bezier(.3,.1,.3,1)" }).onfinish = function () {
    sfx.land();
    document.getElementById("pile").innerHTML = "";
    yuanElement.classList.add("bob");
    callback();
  };
}

function radarStartPanel(message) {
  radarSetStage(0,
    ["<span class=\"h\">$ scan -- 等待一篇可公開回查的 AWS 官方 URL</span>", "<span class=\"ok\">○</span> S1 只讀來源，不把 LLM 推論當作證據。", message ? "<span class=\"num\">!</span> " + radarEscape(message) : ""],
    [{ label: "Run", value: "ready" }, { label: "Policy", value: "on" }]
  );
  document.getElementById("log").insertAdjacentHTML("beforeend", "<form class=\"radar-form\" id=\"radar-url-form\"><label>AWS 官方 URL<input name=\"url\" type=\"url\" required placeholder=\"https://aws.amazon.com/...\" value=\"https://aws.amazon.com/tw/about-aws/whats-new/2026/07/lambda-self-managed-code-storage/\"></label><button type=\"submit\">開始偵察</button><p>送出後會先跑 Skill 1 與 Skill 2，再由真人決定是否進入評估。</p></form>");
  document.getElementById("radar-url-form").addEventListener("submit", radarStartUrl);
}

function radarStartUrl(event) {
  event.preventDefault();
  var url = new FormData(event.currentTarget).get("url");
  radarSetBusy("正在抓取官方來源並檢查 GA、政策與區域訊號。");
  radarApi("/runs/url", { method: "POST", body: JSON.stringify({ url: url }) }).then(function (result) {
    radarState = Object.assign(radarState, result, { runId: result.run_id, selectedId: null, s3: null, s4: null, s5: null });
    radarFinishCurrentStage(1, radarShowCandidates);
  }).catch(function (error) { radarStartPanel(error.message); });
}

function radarShowCandidates() {
  var candidates = radarState.s2.candidates || [];
  var candidate = candidates[0] || {};
  var region = candidate.comparison_dimensions && candidate.comparison_dimensions.target_region_eligibility || {};
  var facts = candidate.proposal_card && candidate.proposal_card.candidate_opportunity && candidate.proposal_card.candidate_opportunity.source_backed_mechanism || [];
  radarSetStage(1,
    ["<span class=\"h\">$ compare -- " + radarEscape(candidates.length) + " 張候選證據卡可供人工檢視</span>", "<span class=\"ok\">✓</span> Region：" + radarEscape(region.status || "unknown"), "<span class=\"num\">!</span> 未證實的定價與 Region 資訊會保留為提醒。"],
    [{ label: "候選", value: String(candidates.length) }, { label: "Region", value: region.status === "available_ap_southeast_1" ? "ready" : "check" }],
    candidates.length ? "直接選擇候選即可依公開證據評估，不需要額外填寫使用環境。" : "沒有可比較候選，請回到 Skill 1 檢查來源。"
  );
  var content = candidates.length ? "<form class=\"radar-form\" id=\"radar-shortlist-form\"><div class=\"candidate-pick\"><label><input type=\"radio\" name=\"candidate\" value=\"" + radarEscape(candidate.candidate_id) + "\" checked><span><b>" + radarEscape(candidate.title) + "</b><small>" + radarEscape((facts[0] || "官方來源尚未提供足夠的候選機制說明。").slice(0, 170)) + "</small></span></label></div><div class=\"radar-optional-note\">Skill 3 會直接依公開證據評估；不需要填寫公司問題、使用環境或資料限制。</div><button type=\"submit\">確認候選，開始評估</button></form>" : "<div class=\"radar-empty\">此來源沒有可供 Skill 3 評估的候選。</div>";
  document.getElementById("log").insertAdjacentHTML("beforeend", content);
  var form = document.getElementById("radar-shortlist-form");
  if (form) form.addEventListener("submit", radarEvaluate);
}

function radarEvaluate(event) {
  event.preventDefault();
  var form = new FormData(event.currentTarget);
  radarState.selectedId = form.get("candidate");
  var payload = { selected_candidate_ids: [radarState.selectedId], selected_by: "GUI human reviewer" };
  radarSetBusy("正在依固定 rubric 計算評估結果與停損條件。");
  radarApi("/runs/" + radarState.runId + "/shortlist", { method: "POST", body: JSON.stringify(payload) }).then(function (artifact) {
    radarFinishCurrentStage(2, function () { radarState.s3 = artifact; radarShowEvaluation(); });
  }).catch(function (error) { radarShowCandidates(); document.getElementById("log").insertAdjacentHTML("beforeend", "<div class=\"ln\"><span class=\"no\">×</span> " + radarEscape(error.message) + "</div>"); });
}

function radarShowEvaluation() {
  var candidate = radarState.s3.evaluated_candidates[0];
  var score = candidate.dimension_scores || {};
  var quote = candidate.cost_estimate && candidate.cost_estimate.quote || {};
  var lowRisk = candidate.recommend_low_risk_validation !== undefined ? candidate.recommend_low_risk_validation : candidate.recommend_s4;
  var pocReview = candidate.eligible_for_poc_review !== undefined
    ? candidate.eligible_for_poc_review
    : (candidate.eligible_for_paid_poc_review !== undefined ? candidate.eligible_for_paid_poc_review : candidate.recommend_s4);
  var decisionText = lowRisk
    ? (pocReview
      ? "建議建立低風險驗證 artifact；公開證據也已達 PoC 審查門檻。"
      : "建議建立低風險驗證 artifact；公開證據尚未達 PoC 審查門檻。")
    : "目前不建議低風險 Skill 4 驗證，報告會保留原因。";
  radarSetStage(2,
    ["<span class=\"h\">$ evaluate -- 固定 rubric 已完成</span>", "<span class=\"ok\">✓</span> 技術價值 " + radarEscape(score.technical_value) + " · 導入前提 " + radarEscape(score.adoption_prerequisites), "<span class=\"ok\">✓</span> 可驗證性 " + radarEscape(score.verifiability) + " · 風險與停損 " + radarEscape(score.risk_and_stop_conditions), "<span class=\"num\">★</span> 加權分 " + radarEscape(candidate.weighted_score) + " / 5 · " + radarEscape(candidate.confidence) + " confidence", "<span class=\"ok\">$</span> 報價單 " + radarEscape(quote.quote_id || "待建立") + " · 預期 USD " + radarEscape(quote.expected_total_usd == null ? "unknown" : quote.expected_total_usd) + " · 建議上限 USD " + radarEscape(quote.recommended_approval_ceiling_usd == null ? "unknown" : quote.recommended_approval_ceiling_usd)],
    [{ label: "Score", value: String(candidate.weighted_score) }, { label: "Estimate", value: quote.expected_total_usd == null ? "pending" : "$" + quote.expected_total_usd }, { label: "PoC", value: pocReview ? "eligible" : "hold" }],
    decisionText
  );
  document.getElementById("log").insertAdjacentHTML("beforeend", "<div class=\"radar-action\"><b>下一關：Skill 4 Validate</b><p>現在只會建立低風險驗證 artifact，不會自行部署任何 AWS 資源。</p><button id=\"radar-validate\">建立驗證 artifact</button></div>");
  document.getElementById("radar-validate").addEventListener("click", radarValidate);
}

function radarValidate() {
  radarSetBusy("正在檢查 lineage、停止條件與受控驗證規則。");
  radarApi("/runs/" + radarState.runId + "/validate", { method: "POST", body: JSON.stringify({ validation_type: "low_risk_validation" }) }).then(function (artifact) {
    radarFinishCurrentStage(3, function () { radarState.s4 = artifact; radarShowValidation(); });
  }).catch(function (error) { alert(error.message); });
}

function radarShowValidation() {
  var candidate = radarState.s4.validated_candidates[0] || {};
  radarSetStage(3,
    ["<span class=\"h\">$ validate -- " + radarEscape(candidate.validation_status || radarState.s4.status) + "</span>", "<span class=\"ok\">✓</span> Skill 3 lineage、來源與停損條件已檢查。", "<span class=\"num\">!</span> 完整 PoC 仍需要具名核准、成本上限、Console review 與 cleanup。"],
    [{ label: "Validation", value: "ready" }, { label: "Resources", value: "0" }],
    "低風險驗證已完成；完整 PoC 要由受控的 S4 deployer 執行。"
  );
  document.getElementById("log").insertAdjacentHTML("beforeend", "<div class=\"radar-action warning\"><b>完整 PoC gate 尚未開啟</b><p>這次沒有建立 AWS 資源。請先完成受控的 deploy approval，才可使用 S4 deployer。</p><button id=\"radar-report\">產生 artifact 報告</button></div>");
  document.getElementById("radar-report").addEventListener("click", radarReport);
}

function radarReport() {
  radarSetBusy("正在彙整 S1 至 Skill 4 artifact，未知事項不會由 UI 補造。");
  radarApi("/runs/" + radarState.runId + "/report", { method: "POST", body: "{}" }).then(function (artifact) {
    radarFinishCurrentStage(4, function () { radarState.s5 = artifact; radarShowReportStage(); });
  }).catch(function (error) { alert(error.message); });
}

function radarShowReportStage() {
  var model = radarState.s5.gui_model || {};
  radarSetStage(4,
    ["<span class=\"h\">$ report -- 只使用 S1-Skill 4 artifact</span>", "<span class=\"ok\">✓</span> " + radarEscape(model.header && model.header.conclusion && model.header.conclusion.text || "報告已建立"), "<span class=\"num\">!</span> unknown 會保留為 unknown，不由 UI 補造。"],
    [{ label: "Report", value: "ready" }, { label: "Evidence", value: String((model.evidence_ledger || []).length) }],
    "報告已整理完成，準備交由真人檢閱下一步。"
  );
  radarFinishCurrentStage(null, function () { radarShowReport(model); });
}

function radarShowReport(model) {
  var score = model.score || {};
  var quote = model.cost_quote || {};
  var range = quote.estimated_range_usd || {};
  var verified = (model.verified_facts || []).map(function (item) { return "<div class=\"r\">" + radarEscape(item) + "</div>"; }).join("") || "unknown";
  var unknown = (model.unknown_or_not_verified || []).map(function (item) { return "<div class=\"r\">" + radarEscape(item) + "</div>"; }).join("") || "unknown";
  document.getElementById("repBox").innerHTML = "<h3>技術評估報告<button class=\"x\" id=\"repX\">×</button></h3><div class=\"meta\">S1 → S2 → Skill 3 → Skill 4 → Skill 5 · " + radarEscape(radarState.runId) + "</div><div class=\"rgrid\"><div class=\"rcell\"><div class=\"k\">Skill 3 分數</div><div class=\"v s\">" + radarEscape(score.weighted_score || "unknown") + "</div></div><div class=\"rcell\"><div class=\"k\">PoC 預期成本</div><div class=\"v q\">USD " + radarEscape(quote.expected_total_usd == null ? "unknown" : quote.expected_total_usd) + "</div></div><div class=\"rcell\"><div class=\"k\">建議核准上限</div><div class=\"v q\">USD " + radarEscape(quote.recommended_approval_ceiling_usd == null ? "unknown" : quote.recommended_approval_ceiling_usd) + "</div></div></div><div class=\"rb\"><div class=\"bk\">成本估算報價單</div><p>" + radarEscape(quote.quote_id || "尚無可稽核報價單") + " · 低／預期／高：USD " + radarEscape(range.low == null ? "?" : range.low) + " / " + radarEscape(range.expected == null ? "?" : range.expected) + " / " + radarEscape(range.high == null ? "?" : range.high) + "。此為公開牌價估算，不是 AWS 帳單。</p></div><div class=\"rb\"><div class=\"bk\">結論</div><p>" + radarEscape(model.header && model.header.conclusion && model.header.conclusion.text || "unknown") + "</p></div><div class=\"rb\"><div class=\"bk\">已驗證</div><div class=\"risks\">" + verified + "</div></div><div class=\"rb\"><div class=\"bk\">待確認</div><div class=\"risks\">" + unknown + "</div></div>";
  document.getElementById("repOverlay").classList.add("show");
  document.getElementById("repX").addEventListener("click", function () { document.getElementById("repOverlay").classList.remove("show"); });
}

document.addEventListener("DOMContentLoaded", function () {
  document.querySelector(".brand .t1").innerHTML = "AI Agentic 雲端技術雷達與評估系統<small>ARTIFACT-FIRST · S1 → S5 · HUMAN-GATED POC</small>";
  document.querySelector(".scen").innerHTML = "模式<span class=\"toggle\"><button type=\"button\" class=\"on\">實際資料</button></span>";
  STATIONS.splice.apply(STATIONS, [0, STATIONS.length].concat(radarStages.map(function (stage) {
    return { code: stage.code, name: stage.name, en: stage.en, hint: stage.hint, bTitle: stage.title, bSub: stage.sub, labels: stage.labels, init: "", eat: [], sum: "", metrics: [] };
  })));
  STATIONS.forEach(function (_, index) { if (!document.getElementById("dots").children[index]) document.getElementById("dots").appendChild(document.createElement("i")); });
  radarStartPanel();
});
