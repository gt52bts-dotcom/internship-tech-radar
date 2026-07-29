const config = window.RADAR_CONFIG || { apiBaseUrl: "http://localhost:3000" };
const state = { runId: null, s1: null, s2: null, s3: null, s4: null, s5: null, selected: [] };
const stageMeta = {
  s1: { number: "01", title: "Scan", description: "選擇來源入口" },
  s2: { number: "02", title: "Compare", description: "檢視證據卡" },
  s3: { number: "03", title: "Evaluate", description: "等候人工 shortlist" },
  s4: { number: "04", title: "Validate", description: "受控驗證與 PoC 審核" },
  s5: { number: "05", title: "Report", description: "組成可追溯報告" },
};
const $ = (selector) => document.querySelector(selector);

document.addEventListener("DOMContentLoaded", () => {
  lucide.createIcons();
  $("#url-form").addEventListener("submit", startUrlRun);
  $("#discovery-form").addEventListener("submit", startDiscoveryRun);
  $("#evaluate-form").addEventListener("submit", evaluate);
  $("#validate-button").addEventListener("click", validate);
  $("#report-button").addEventListener("click", report);
  document.querySelectorAll(".entry-tab").forEach((button) => button.addEventListener("click", switchEntry));
  document.querySelectorAll(".stage").forEach((button) => button.addEventListener("click", () => scrollToStage(button.dataset.stage)));
  updateBoard();
});

async function api(path, options = {}) {
  const response = await fetch(`${config.apiBaseUrl.replace(/\/$/, "")}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.message || "API request failed");
  return payload;
}

function switchEntry(event) {
  const entry = event.currentTarget.dataset.entry;
  document.querySelectorAll(".entry-tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.entry === entry));
  document.querySelectorAll("[data-entry-panel]").forEach((panel) => panel.classList.toggle("hidden", panel.dataset.entryPanel !== entry));
}

async function startUrlRun(event) {
  event.preventDefault();
  await startRun("/runs/url", { url: $("#url").value.trim() });
}

async function startDiscoveryRun(event) {
  event.preventDefault();
  const form = Object.fromEntries(new FormData(event.currentTarget).entries());
  form.max_candidates = Number(form.max_candidates);
  await startRun("/runs/discovery", form);
}

async function startRun(path, payload) {
  setConnection("正在建立 Skill 1 與 Skill 2 artifact", "neutral");
  try {
    const result = await api(path, { method: "POST", body: JSON.stringify(payload) });
    Object.assign(state, result, { runId: result.run_id, selected: [], s3: null, s4: null, s5: null });
    $("#run-badge").textContent = `Run ${state.runId}`;
    $("#run-badge").classList.remove("hidden");
    $("#validate-panel").classList.add("hidden");
    $("#report-panel").classList.add("hidden");
    renderRun();
    setConnection("Skill 1 與 Skill 2 已完成", "ready");
    setActiveStage("s2");
    scrollToStage("s2");
  } catch (error) {
    setConnection(error.message, "error");
  }
}

function renderRun() {
  const candidates = state.s2?.candidates || [];
  $("#run-panel").classList.remove("hidden");
  $("#run-title").textContent = candidates.length ? `找到 ${candidates.length} 個可回查候選` : "沒有可進入比較的候選";
  const first = candidates[0] || {};
  $("#source-link").href = first.source_url || "#";
  $("#source-link").style.visibility = first.source_url ? "visible" : "hidden";
  renderFunnel();
  $("#candidates").innerHTML = candidates.length ? candidates.map(candidateCard).join("") : emptyState("沒有候選可供人工 shortlist。請檢查 Scan artifact 的資料缺口與排除原因。");
  document.querySelectorAll(".candidate-check").forEach((checkbox) => checkbox.addEventListener("change", selectCandidate));
  $("#evaluate-panel").classList.toggle("hidden", !candidates.length);
  updateBoard();
}

function candidateCard(candidate) {
  const dimensions = candidate.comparison_dimensions || {};
  const region = dimensions.target_region_eligibility || {};
  const proposal = candidate.proposal_card || {};
  const facts = proposal.candidate_opportunity?.source_backed_mechanism || dimensions.source_backed_capabilities?.excerpts || [];
  const unknowns = (dimensions.unknowns_and_next_validation_question || {}).unknowns || candidate.evidence_limits || [];
  const checked = state.selected.includes(candidate.candidate_id) ? "checked" : "";
  return `<article class="candidate-card">
    <div class="candidate-select"><input class="candidate-check" id="${escapeAttr(candidate.candidate_id)}" type="checkbox" value="${escapeAttr(candidate.candidate_id)}" ${checked}><label for="${escapeAttr(candidate.candidate_id)}">加入 shortlist</label></div>
    <div class="candidate-main"><div class="candidate-kicker"><span class="status-tag ${regionTag(region.status)}">${escapeHtml(region.status || "region_unknown")}</span><span class="source-tag">官方來源</span></div><h3><a href="${escapeAttr(candidate.source_url || "#")}" target="_blank" rel="noreferrer">${escapeHtml(candidate.title || "Untitled candidate")}</a></h3><p>${escapeHtml(proposal.candidate_opportunity?.plain_language || candidate.summary || candidate.description || "沒有摘要")}</p></div>
    <div class="evidence-columns"><div><p class="evidence-label">已證實</p>${listItems(facts, "目前沒有擷取到可呈現的來源事實。")}</div><div><p class="evidence-label">待釐清</p>${listItems(unknowns, "沒有記錄資料缺口。")}</div></div>
  </article>`;
}

function selectCandidate(event) {
  const id = event.currentTarget.value;
  const next = event.currentTarget.checked ? [...state.selected, id] : state.selected.filter((item) => item !== id);
  if (next.length > 3) {
    event.currentTarget.checked = false;
    setConnection("Skill 3 最多只能 shortlist 3 個候選", "error");
    return;
  }
  state.selected = next;
  $("#selected-count").textContent = `${state.selected.length} / 3 已選`;
  renderFunnel();
  updateBoard();
}

function renderFunnel() {
  const items = [
    ["Scan 候選", state.s1?.candidates?.length || 0],
    ["Compare 卡片", state.s2?.candidates?.length || 0],
    ["Region 已證實", (state.s2?.candidates || []).filter((item) => item.comparison_dimensions?.target_region_eligibility?.status === "available_ap_southeast_1").length],
    ["已 shortlist", state.selected.length],
    ["已驗證", state.s4?.validated_candidates?.length || 0],
  ];
  $("#funnel").innerHTML = items.map(([label, value]) => `<div><b>${value}</b><small>${label}</small></div>`).join("");
}

async function evaluate(event) {
  event.preventDefault();
  if (!state.selected.length) {
    setConnection("請先在 Compare 選擇至少一個候選", "error");
    scrollToStage("s2");
    return;
  }
  const payload = Object.fromEntries(new FormData(event.currentTarget).entries());
  payload.selected_candidate_ids = state.selected;
  payload.selected_by = "GUI human reviewer";
  setConnection("正在套用固定 Skill 3 rubric", "neutral");
  try {
    state.s3 = await api(`/runs/${state.runId}/shortlist`, { method: "POST", body: JSON.stringify(payload) });
    renderEvaluation();
    $("#validate-panel").classList.remove("hidden");
    setConnection("Skill 3 已完成，等待確認驗證路徑", "ready");
    setActiveStage("s3");
    scrollToStage("s3");
    updateBoard();
  } catch (error) {
    setConnection(error.message, "error");
  }
}

function renderEvaluation() {
  const candidates = state.s3?.evaluated_candidates || [];
  $("#evaluation-result").innerHTML = candidates.map((candidate) => {
    const score = candidate.dimension_scores || {};
    return `<article class="evaluation-card"><div class="evaluation-title"><div><p class="eyebrow">${escapeHtml(candidate.confidence || "unknown")} confidence</p><h3>${escapeHtml(candidate.title || "Candidate")}</h3></div><div class="score-badge"><b>${escapeHtml(String(candidate.weighted_score ?? "unknown"))}</b><span>/ 5</span></div></div><div class="rubric-grid">${Object.entries(score).map(([key, value]) => `<div><span>${rubricLabel(key)}</span><b>${escapeHtml(String(value))}</b></div>`).join("")}</div><div class="recommendation ${candidate.recommend_s4 ? "positive" : "caution"}"><i data-lucide="${candidate.recommend_s4 ? "circle-check" : "circle-alert"}"></i>${escapeHtml(candidate.recommendation_reason || "unknown")}</div></article>`;
  }).join("") || emptyState("Skill 3 尚未評估任何候選。");
  lucide.createIcons();
}

async function validate() {
  setConnection("正在建立低風險 Skill 4 validation artifact", "neutral");
  try {
    state.s4 = await api(`/runs/${state.runId}/validate`, { method: "POST", body: JSON.stringify({ validation_type: "low_risk_validation" }) });
    renderValidation();
    $("#report-panel").classList.remove("hidden");
    setConnection("Skill 4 artifact 已建立，尚未啟動完整 PoC", "ready");
    setActiveStage("s4");
    updateBoard();
  } catch (error) {
    setConnection(error.message, "error");
  }
}

function renderValidation() {
  const validation = state.s4?.validated_candidates?.[0] || {};
  const checks = [...(validation.evidence_checks || []), ...(validation.paid_poc_checks || [])];
  $("#validation-result").classList.remove("hidden");
  $("#validation-result").innerHTML = `<div class="validation-head"><div><p class="eyebrow">Validation status</p><h3>${escapeHtml(validation.validation_status || state.s4?.status || "unknown")}</h3></div><span class="status-tag ${validation.validation_status?.includes("ready") ? "good" : "warning"}">${escapeHtml(validation.validation_type || "low_risk_validation")}</span></div><div class="check-grid">${checks.map((check) => `<div class="validation-check ${check.passed ? "pass" : "fail"}"><i data-lucide="${check.passed ? "check" : "x"}"></i><div><b>${escapeHtml(check.name)}</b><span>${escapeHtml(check.detail)}</span></div></div>`).join("")}</div><div class="limits"><b>限制與下一步</b>${listItems([...(validation.limitations || []), ...(validation.downgrade_reasons || [])], "尚未取得完整 PoC 執行證據。")}</div>`;
  lucide.createIcons();
}

async function report() {
  setConnection("正在由 S1-S4 artifact 組成報告", "neutral");
  try {
    state.s5 = await api(`/runs/${state.runId}/report`, { method: "POST", body: "{}" });
    renderReport();
    setConnection("Skill 5 報告已建立", "ready");
    setActiveStage("s5");
    scrollToStage("s5");
    updateBoard();
  } catch (error) {
    setConnection(error.message, "error");
  }
}

function renderReport() {
  const model = state.s5?.gui_model || {};
  const score = model.score || {};
  $("#report").innerHTML = `<article class="report-summary"><p class="eyebrow">${escapeHtml(model.header?.report_type || "interim report")}</p><h3>${escapeHtml(model.header?.title || "Artifact report")}</h3><p class="conclusion">${escapeHtml(model.header?.conclusion?.text || "unknown")}</p><div class="report-score"><div><span>Skill 3 分數</span><b>${escapeHtml(String(score.weighted_score ?? "unknown"))}</b></div><div><span>Confidence</span><b>${escapeHtml(score.confidence || "unknown")}</b></div></div></article><article class="report-card"><h3>已驗證</h3>${listItems(model.verified_facts, "unknown")}</article><article class="report-card"><h3>待確認</h3>${listItems(model.unknown_or_not_verified, "unknown")}</article><article class="report-card evidence-ledger"><h3>Evidence ledger</h3>${(model.evidence_ledger || []).map((item) => `<div><b>${escapeHtml(item.claim)}</b><span>${escapeHtml(item.type)} · ${escapeHtml(item.status)}</span><a href="${escapeAttr(item.source || "#")}" target="_blank" rel="noreferrer">${escapeHtml(item.source || "unknown")}</a></div>`).join("") || "unknown"}</article>`;
}

function updateBoard() {
  const current = state.s5 ? "s5" : state.s4 ? "s4" : state.s3 ? "s3" : state.s2 ? "s2" : "s1";
  const meta = stageMeta[current];
  $("#current-stage-number").textContent = meta.number;
  $("#current-stage-title").textContent = meta.title;
  $("#current-stage-description").textContent = meta.description;
  $("#board-state").textContent = state.runId ? `Run ${state.runId.slice(-8)}` : "尚未開始";
  const lineage = [["S1", state.s1], ["S2", state.s2], ["S3", state.s3], ["S4", state.s4], ["S5", state.s5]];
  $("#lineage").innerHTML = lineage.map(([label, artifact]) => `<li class="${artifact ? "done" : "pending"}"><span>${artifact ? "✓" : "·"}</span><b>${label}</b><small>${artifact ? escapeHtml(artifact.status || "recorded") : "not created"}</small></li>`).join("");
  const gates = [
    ["人工 shortlist", state.selected.length ? `${state.selected.length} 項已選` : "尚未選擇", Boolean(state.selected.length)],
    ["Skill 3 context", state.s3?.human_shortlist_gate?.status || "待填寫", Boolean(state.s3)],
    ["完整 PoC 核准", state.s4?.approval_gate?.status || "尚未請求", false],
    ["Console review / cleanup", state.s5 ? "依報告確認" : "尚未進入", false],
  ];
  $("#gates").innerHTML = gates.map(([label, value, complete]) => `<div class="gate-row"><span class="gate-dot ${complete ? "complete" : ""}"></span><div><b>${label}</b><small>${escapeHtml(value)}</small></div></div>`).join("");
  const notes = [];
  if (!state.runId) notes.push("Artifact 尚未建立。", "沒有任何 AWS 資源會由此頁面自動建立。");
  if (state.s2 && !state.selected.length) notes.push("Skill 3 需要真人最多挑選 3 項候選。");
  if (state.s3) notes.push("固定 rubric 已完成；成本不納入技術分數。");
  if (state.s4) notes.push("完整 PoC 仍需具名核准、成本上限、Console review 與 cleanup。");
  if (state.s5?.gui_model?.next_reminders?.length) notes.push(...state.s5.gui_model.next_reminders.slice(0, 2));
  $("#board-notes").innerHTML = notes.map((note) => `<li>${escapeHtml(note)}</li>`).join("");
}

function setActiveStage(stage) {
  document.querySelectorAll(".stage").forEach((button) => button.classList.toggle("active", button.dataset.stage === stage));
  updateBoard();
}

function scrollToStage(stage) {
  const target = { s1: "#start-panel", s2: "#run-panel", s3: "#evaluate-panel", s4: "#validate-panel", s5: "#report-panel" }[stage];
  const panel = $(target);
  if (panel && !panel.classList.contains("hidden")) panel.scrollIntoView({ behavior: "smooth", block: "start" });
}

function setConnection(text, stateClass) {
  const node = $("#connection");
  node.innerHTML = `<i data-lucide="${stateClass === "error" ? "circle-x" : stateClass === "ready" ? "circle-check" : "loader-circle"}"></i>${escapeHtml(text)}`;
  node.className = `status ${stateClass}`;
  lucide.createIcons();
}

function regionTag(status) { return status === "available_ap_southeast_1" ? "good" : status === "region_unknown" ? "warning" : "blocked"; }
function rubricLabel(key) { return { technical_value: "技術價值", adoption_prerequisites: "導入前提", verifiability: "可驗證性", risk_and_stop_conditions: "風險與停損" }[key] || key; }
function listItems(items, fallback) { const values = items?.length ? items : [fallback]; return `<ul>${values.map((item) => `<li>${escapeHtml(typeof item === "string" ? item : JSON.stringify(item))}</li>`).join("")}</ul>`; }
function emptyState(text) { return `<div class="empty-state"><i data-lucide="circle-dashed"></i><p>${escapeHtml(text)}</p></div>`; }
function escapeHtml(value) { return String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[char]); }
function escapeAttr(value) { return escapeHtml(value); }
