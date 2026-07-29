const config = window.RADAR_CONFIG || { apiBaseUrl: "http://localhost:3000/" };
const state = { runId: null, s1: null, s2: null, s3: null, s4: null, s5: null, selected: null };
const $ = (selector) => document.querySelector(selector);

document.addEventListener("DOMContentLoaded", () => {
  lucide.createIcons();
  $("#url-form").addEventListener("submit", startUrlRun);
  $("#evaluate-form").addEventListener("submit", evaluate);
  $("#validate-button").addEventListener("click", validate);
  $("#report-button").addEventListener("click", report);
  $("#connection").textContent = "API ready";
  $("#connection").className = "status ready";
});

async function api(path, options = {}) {
  const response = await fetch(`${config.apiBaseUrl.replace(/\/$/, "")}${path}`, { headers: { "Content-Type": "application/json" }, ...options });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.message || "API request failed");
  return payload;
}

async function startUrlRun(event) {
  event.preventDefault(); setConnection("Working", "neutral");
  try {
    const result = await api("/runs/url", { method: "POST", body: JSON.stringify({ url: $("#url").value }) });
    Object.assign(state, result, { runId: result.run_id, selected: null });
    renderRun(); $("#evaluate-panel").classList.remove("hidden"); setConnection("S1 and S2 complete", "ready");
  } catch (error) { setConnection(error.message, "error"); }
}

function renderRun() {
  const candidates = state.s2.candidates || [];
  $("#run-panel").classList.remove("hidden"); $("#run-id").textContent = state.runId;
  $("#run-title").textContent = candidates.length ? "候選比較" : "沒有可比較候選";
  const first = candidates[0] || {}; $("#source-link").href = first.source_url || "#";
  $("#source-link").style.visibility = first.source_url ? "visible" : "hidden";
  const funnel = { "S1 candidates": (state.s1.candidates || []).length, "S2 candidates": candidates.length, "S3 evaluated": 0, "S4 validated": 0, "S5 report": 0 };
  $("#funnel").innerHTML = Object.entries(funnel).map(([key, value]) => `<div><b>${value}</b><small>${key}</small></div>`).join("");
  $("#candidates").innerHTML = `<table><thead><tr><th>選擇</th><th>候選</th><th>Region</th><th>官方文件</th><th>資料缺口</th></tr></thead><tbody>${candidates.map((candidate, index) => `<tr><td><input type="radio" name="candidate" value="${candidate.candidate_id}" ${index === 0 ? "checked" : ""}></td><td><a href="${candidate.source_url}" target="_blank" rel="noreferrer">${escapeHtml(candidate.title)}</a></td><td><span class="tag ${regionClass(candidate)}">${escapeHtml(candidate.comparison_dimensions?.target_region_eligibility?.status || "unknown")}</span></td><td>${candidate.evidence_coverage?.official_docs_linked ? "已連結" : "unknown"}</td><td>${escapeHtml((candidate.evidence_limits || []).slice(0, 1).join(" ") || "無")}</td></tr>`).join("")}</tbody></table>`;
}

async function evaluate(event) {
  event.preventDefault(); const selected = document.querySelector("input[name=candidate]:checked"); if (!selected) return;
  state.selected = selected.value; const form = new FormData(event.currentTarget); const payload = Object.fromEntries(form.entries());
  payload.selected_candidate_ids = [state.selected]; payload.selected_by = "GUI human reviewer";
  try { state.s3 = await api(`/runs/${state.runId}/shortlist`, { method: "POST", body: JSON.stringify(payload) }); renderEvaluation(); $("#validate-panel").classList.remove("hidden"); setConnection("Skill 3 complete", "ready"); } catch (error) { setConnection(error.message, "error"); }
}

function renderEvaluation() {
  const candidate = (state.s3.evaluated_candidates || [])[0] || {}; const cells = [["Weighted score", candidate.weighted_score ?? "unknown"], ["Confidence", candidate.confidence || "unknown"], ["Region", candidate.region_status?.status || "unknown"], ["Recommend Skill 4", candidate.recommend_s4 ? "Yes" : "No"]];
  $("#evaluation-result").innerHTML = cells.map(([label, value]) => `<div><span>${label}</span><b>${escapeHtml(String(value))}</b></div>`).join("");
}

async function validate() { try { state.s4 = await api(`/runs/${state.runId}/validate`, { method: "POST", body: JSON.stringify({ validation_type: "low_risk_validation" }) }); $("#report-panel").classList.remove("hidden"); setConnection("Skill 4 artifact ready", "ready"); } catch (error) { setConnection(error.message, "error"); } }
async function report() { try { state.s5 = await api(`/runs/${state.runId}/report`, { method: "POST", body: "{}" }); renderReport(); setConnection("Skill 5 report ready", "ready"); } catch (error) { setConnection(error.message, "error"); } }

function renderReport() { const model = state.s5.gui_model; const checks = model.validation_checks.map((item) => `<div class="check"><span>${escapeHtml(item.label)}</span><b>${escapeHtml(String(item.status))}</b></div>`).join(""); const verified = model.verified_facts.map((item) => `<li>${escapeHtml(item)}</li>`).join(""); const unknown = model.unknown_or_not_verified.map((item) => `<li>${escapeHtml(item)}</li>`).join(""); $("#report").innerHTML = `<div><p class="conclusion">${escapeHtml(model.header.conclusion.text)}</p><h3>已證實的事實</h3><ul>${verified || "<li>unknown</li>"}</ul></div><div><h3>驗證狀態</h3>${checks}<h3>尚未驗證</h3><ul>${unknown || "<li>無</li>"}</ul></div>`; }
function setConnection(text, stateClass) { const node = $("#connection"); node.textContent = text; node.className = `status ${stateClass}`; }
function regionClass(candidate) { return candidate.comparison_dimensions?.target_region_eligibility?.status === "available_ap_southeast_1" ? "good" : ""; }
function escapeHtml(value) { return value.replace(/[&<>'"]/g, (char) => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", "'":"&#39;", '"':"&quot;" })[char]); }
