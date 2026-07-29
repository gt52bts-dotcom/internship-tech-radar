var radarConfig = window.RADAR_CONFIG || { apiBaseUrl: "http://127.0.0.1:8080/api" };
var radarState = { runId: null, s1: null, s2: null, s3: null, s4: null, s5: null, selectedId: null };
var radarStages = [
  { code: "S1", name: "掃描", en: "SCAN", hint: "貼入一篇 AWS 官方消息，讓圓圓搬運可回查的來源訊號。", labels: ["URL", "AWS", "GA"], title: "Skill 1 Scan", sub: "公開來源與區域訊號" },
  { code: "S2", name: "比較", en: "COMPARE", hint: "把已證實、推論與資料缺口分開，才不會把希望當成證據。", labels: ["FACT", "GAP", "REGION"], title: "Skill 2 Compare", sub: "候選證據卡" },
  { code: "S3", name: "評估", en: "EVALUATE", hint: "真人先選候選，再用固定 rubric 評估。", labels: ["PROBLEM", "ENV", "BOUNDARY"], title: "Skill 3 Evaluate", sub: "人工 shortlist gate" },
  { code: "S4", name: "驗證", en: "VALIDATE", hint: "低風險驗證可以前進；完整 PoC 必須保留人工核准。", labels: ["APPROVE", "BUDGET", "CLEANUP"], title: "Skill 4 Validate", sub: "受控驗證與 PoC gate" },
  { code: "S5", name: "報告", en: "REPORT", hint: "每句結論都有 artifact；沒有證據的地方就留在 unknown。", labels: ["LEDGER", "REPORT", "REVIEW"], title: "Skill 5 Report", sub: "artifact-only report" },
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

function radarSetStage(index, entries, metrics) {
  station = index;
  total = index * 3;
  pts = total * 10;
  document.getElementById("pts").textContent = pts;
  document.getElementById("cnt").textContent = total;
  document.getElementById("bTitle").textContent = radarStages[index].title;
  document.getElementById("bSub").textContent = radarStages[index].sub + (radarState.runId ? " · " + radarState.runId.slice(-8) : "");
  document.getElementById("hint").innerHTML = "<b>第 " + (index + 1) + " 站 / 5 · " + radarStages[index].name + "</b>　" + radarStages[index].hint;
  document.getElementById("log").innerHTML = entries.map(function (entry, entryIndex) {
    return "<div class=\"ln\" style=\"animation-delay:" + (entryIndex * 0.06) + "s\">" + entry + "</div>";
  }).join("");
  document.getElementById("metrics").innerHTML = metrics.map(function (metric) {
    return "<div class=\"m\"><div class=\"mk\">" + radarEscape(metric.label) + "</div><div class=\"mv\">" + radarEscape(metric.value) + "</div></div>";
  }).join("");
  document.getElementById("blocks").innerHTML = radarStages[index].labels.map(function (label, labelIndex) {
    return "<div class=\"block " + (labelIndex % 2 ? "red" : "blue") + " radar-block\" style=\"left:" + (18 + labelIndex * 68) + "%\"><div class=\"cube\">" + label + "</div></div>";
  }).join("");
  layout();
  placeYuan();
}

function radarStartPanel(message) {
  radarSetStage(0, ["<span class=\"h\">$ scan -- 等待一篇可公開回查的 AWS 官方 URL</span>", "<span class=\"ok\">○</span> S1 只讀來源，不把 LLM 推論當作證據。", message ? "<span class=\"num\">! </span>" + radarEscape(message) : ""], [{ label: "Run", value: "ready" }, { label: "Policy", value: "on" }]);
  document.getElementById("log").insertAdjacentHTML("beforeend", "<form class=\"radar-form\" id=\"radar-url-form\"><label>AWS 官方 URL<input name=\"url\" type=\"url\" required placeholder=\"https://aws.amazon.com/...\" value=\"https://aws.amazon.com/tw/about-aws/whats-new/2026/07/lambda-self-managed-code-storage/\"></label><button type=\"submit\">開始偵察</button><p>也可用本機伺服器的 API 進行真正的 S1 → S5 artifact 流程。</p></form>");
  document.getElementById("radar-url-form").addEventListener("submit", radarStartUrl);
}

function radarStartUrl(event) {
  event.preventDefault();
  var url = new FormData(event.currentTarget).get("url");
  radarSetStage(0, ["<span class=\"h\">$ scan -- 正在讀取官方來源...</span>", "<span class=\"num\">○</span> 將建立 S1 與 S2 artifact。"], [{ label: "Fetch", value: "working" }, { label: "Policy", value: "on" }]);
  radarApi("/runs/url", { method: "POST", body: JSON.stringify({ url: url }) }).then(function (result) {
    radarState = Object.assign(radarState, result, { runId: result.run_id, selectedId: null, s3: null, s4: null, s5: null });
    radarShowCandidates();
  }).catch(function (error) { radarStartPanel(error.message); });
}

function radarShowCandidates() {
  var candidates = radarState.s2.candidates || [];
  var candidate = candidates[0] || {};
  var region = candidate.comparison_dimensions && candidate.comparison_dimensions.target_region_eligibility || {};
  var facts = candidate.proposal_card && candidate.proposal_card.candidate_opportunity && candidate.proposal_card.candidate_opportunity.source_backed_mechanism || [];
  radarSetStage(1, ["<span class=\"h\">$ compare -- " + radarEscape(candidates.length) + " 張證據卡可供人工檢視</span>", "<span class=\"ok\">✓</span> Region：" + radarEscape(region.status || "unknown"), "<span class=\"num\">!</span> 定價、公司環境與 cleanup 必須另行證實。"], [{ label: "候選", value: String(candidates.length) }, { label: "Region", value: region.status === "available_ap_southeast_1" ? "ready" : "check" }]);
  var content = candidates.length ? "<form class=\"radar-form\" id=\"radar-shortlist-form\"><div class=\"candidate-pick\"><label><input type=\"radio\" name=\"candidate\" value=\"" + radarEscape(candidate.candidate_id) + "\" checked><span><b>" + radarEscape(candidate.title) + "</b><small>" + radarEscape((facts[0] || "官方來源已取得，請確認業務情境。").slice(0, 170)) + "</small></span></label></div><label>想解決的問題<textarea name=\"problem\" required placeholder=\"請填寫真實技術問題\"></textarea></label><label>可用環境<textarea name=\"environment\" required placeholder=\"例如：non-production 帳號與可用權限\"></textarea></label><label>不可碰的資料與權限<textarea name=\"boundary\" required placeholder=\"例如：PII、production data、production role\"></textarea></label><button type=\"submit\">確認 shortlist，前往評估</button></form>" : "<div class=\"radar-empty\">這次沒有可用候選，請檢查 Scan artifact 的資料缺口。</div>";
  document.getElementById("log").insertAdjacentHTML("beforeend", content);
  var form = document.getElementById("radar-shortlist-form");
  if (form) form.addEventListener("submit", radarEvaluate);
}

function radarEvaluate(event) {
  event.preventDefault();
  var form = new FormData(event.currentTarget);
  radarState.selectedId = form.get("candidate");
  var payload = { selected_candidate_ids: [radarState.selectedId], selected_by: "GUI human reviewer", problem_to_solve: form.get("problem"), available_environment: form.get("environment"), forbidden_data_and_permissions: form.get("boundary") };
  radarApi("/runs/" + radarState.runId + "/shortlist", { method: "POST", body: JSON.stringify(payload) }).then(function (artifact) {
    radarState.s3 = artifact;
    radarShowEvaluation();
  }).catch(function (error) { radarShowCandidates(); document.getElementById("log").insertAdjacentHTML("beforeend", "<div class=\"ln\"><span class=\"no\">✕</span> " + radarEscape(error.message) + "</div>"); });
}

function radarShowEvaluation() {
  var candidate = radarState.s3.evaluated_candidates[0];
  var score = candidate.dimension_scores || {};
  radarSetStage(2, ["<span class=\"h\">$ evaluate -- 固定 rubric 已完成</span>", "<span class=\"ok\">✓</span> 技術價值 " + radarEscape(score.technical_value) + " · 導入前提 " + radarEscape(score.adoption_prerequisites), "<span class=\"ok\">✓</span> 可驗證性 " + radarEscape(score.verifiability) + " · 風險與停損 " + radarEscape(score.risk_and_stop_conditions), "<span class=\"num\">★</span> 加權分 " + radarEscape(candidate.weighted_score) + " / 5 · " + radarEscape(candidate.confidence) + " confidence"], [{ label: "Score", value: String(candidate.weighted_score) }, { label: "S4", value: candidate.recommend_s4 ? "review" : "hold" }]);
  document.getElementById("log").insertAdjacentHTML("beforeend", "<div class=\"radar-action\"><b>下一關：Skill 4 Validate</b><p>現在只會建立低風險驗證 artifact，不會自行部署任何 AWS 資源。</p><button id=\"radar-validate\">建立驗證 artifact</button></div>");
  document.getElementById("radar-validate").addEventListener("click", radarValidate);
}

function radarValidate() {
  radarApi("/runs/" + radarState.runId + "/validate", { method: "POST", body: JSON.stringify({ validation_type: "low_risk_validation" }) }).then(function (artifact) {
    radarState.s4 = artifact;
    var candidate = artifact.validated_candidates[0] || {};
    radarSetStage(3, ["<span class=\"h\">$ validate -- " + radarEscape(candidate.validation_status || artifact.status) + "</span>", "<span class=\"ok\">✓</span> S3 lineage、來源與停損條件已檢查。", "<span class=\"num\">!</span> 完整 PoC 仍需要具名核准、成本上限、Console review 與 cleanup。"], [{ label: "Validation", value: "ready" }, { label: "Resources", value: "0" }]);
    document.getElementById("log").insertAdjacentHTML("beforeend", "<div class=\"radar-action warning\"><b>完整 PoC gate 尚未開啟</b><p>這次沒有建立 AWS 資源。請先完成受控的 deploy approval，才可使用 S4 deployer。</p><button id=\"radar-report\">產生 artifact 報告</button></div>");
    document.getElementById("radar-report").addEventListener("click", radarReport);
  }).catch(function (error) { alert(error.message); });
}

function radarReport() {
  radarApi("/runs/" + radarState.runId + "/report", { method: "POST", body: "{}" }).then(function (artifact) {
    radarState.s5 = artifact;
    var model = artifact.gui_model || {};
    radarSetStage(4, ["<span class=\"h\">$ report -- 只使用 S1-S4 artifact</span>", "<span class=\"ok\">✓</span> " + radarEscape(model.header && model.header.conclusion && model.header.conclusion.text || "報告已建立"), "<span class=\"num\">!</span> unknown 會保留為 unknown，不由 UI 補造。"], [{ label: "Report", value: "ready" }, { label: "Evidence", value: String((model.evidence_ledger || []).length) }]);
    radarShowReport(model);
  }).catch(function (error) { alert(error.message); });
}

function radarShowReport(model) {
  var score = model.score || {};
  var verified = (model.verified_facts || []).map(function (item) { return "<div class=\"r\">" + radarEscape(item) + "</div>"; }).join("") || "unknown";
  var unknown = (model.unknown_or_not_verified || []).map(function (item) { return "<div class=\"r\">" + radarEscape(item) + "</div>"; }).join("") || "unknown";
  document.getElementById("repBox").innerHTML = "<h3>技術評估報告<button class=\"x\" id=\"repX\">✕</button></h3><div class=\"meta\">S1 → S2 → Skill 3 → Skill 4 → Skill 5 · " + radarEscape(radarState.runId) + "</div><div class=\"rgrid\"><div class=\"rcell\"><div class=\"k\">Skill 3 分數</div><div class=\"v s\">" + radarEscape(score.weighted_score || "unknown") + "</div></div><div class=\"rcell\"><div class=\"k\">Confidence</div><div class=\"v q\">" + radarEscape(score.confidence || "unknown") + "</div></div><div class=\"rcell\"><div class=\"k\">Skill 4</div><div class=\"v q\">" + radarEscape(radarState.s4 && radarState.s4.status || "unknown") + "</div></div></div><div class=\"rb\"><div class=\"bk\">結論</div><p>" + radarEscape(model.header && model.header.conclusion && model.header.conclusion.text || "unknown") + "</p></div><div class=\"rb\"><div class=\"bk\">已驗證</div><div class=\"risks\">" + verified + "</div></div><div class=\"rb\"><div class=\"bk\">待確認</div><div class=\"risks\">" + unknown + "</div></div>";
  document.getElementById("repOverlay").classList.add("show");
  document.getElementById("repX").addEventListener("click", function () { document.getElementById("repOverlay").classList.remove("show"); });
}

document.addEventListener("DOMContentLoaded", function () {
  document.querySelector(".brand .t1").innerHTML = "圓圓的雲端技術偵察大冒險<small>AGENTIC CLOUD RADAR · S1 → S5 artifact workflow</small>";
  document.querySelector(".scen").innerHTML = "模式<span class=\"toggle\"><button type=\"button\" class=\"on\">實際資料</button></span>";
  STATIONS.splice.apply(STATIONS, [0, STATIONS.length].concat(radarStages.map(function (stage) {
    return { code: stage.code, name: stage.name, en: stage.en, hint: stage.hint, bTitle: stage.title, bSub: stage.sub, labels: stage.labels, init: "", eat: [], sum: "", metrics: [] };
  })));
  STATIONS.forEach(function (_, index) { if (!document.getElementById("dots").children[index]) document.getElementById("dots").appendChild(document.createElement("i")); });
  radarStartPanel();
});
