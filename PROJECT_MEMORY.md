# 實習專案記憶

## Terminology Rule

## Daily Log Preference (2026-08-26)

- Cleo no longer needs the `主管評分表自評` section in formal daily internship logs. Omit it from all future logs and the daily-log template. Existing historical logs retain their original content; do not revise them unless Cleo asks for a historical correction.

- To avoid ambiguity, refer to the project stage as `Skill 3` or `S3 Evaluate`, never bare `S3`. Refer to the AWS service as `Amazon S3` or `S3 bucket`. Use `Skill 3 evaluation artifact` rather than `S3 artifact` in user-facing explanations. CLI command and code identifiers remain unchanged.

## GUI Interaction Preference

- The web demo title is `AI Agentic 雲端技術雷達與評估系統`.
- Preserve the original cute game scene and its block-eating, score, and platform-jump feedback. The side panel should be a larger, designed task-control panel showing stage progress, current goal, completion criteria, status metrics, and the human action required, rather than a sparse terminal log.
- In the GUI, Skill 3 only asks the human to select one candidate for single-item evaluation. Do not show or require `problem_to_solve`, `available_environment`, or `forbidden_data_and_permissions`; public-evidence limits are recorded by the system as review notes.

## Web Delivery Decision

- The current S1-S5 core must remain portable and deployable with an AWS-hosted web demo. The GUI consumes artifact-first API responses and must not bypass the S4 named-human approval, cost ceiling, Console review, or cleanup gates. A self-contained Claude GUI handoff package is maintained under `radar-redesign/claude-gui-handoff/`.

## 2026-07-30 Five Skill Packaging Decision

- The reusable project deliverable is now maintained as five repository-backed Skill packages under `radar-redesign/skills/`: `scan-cloud-technologies`, `compare-cloud-candidates`, `evaluate-cloud-candidate`, `validate-cloud-poc`, and `report-cloud-evidence`.
- Each Skill has its own `SKILL.md` and `agents/openai.yaml`, but all five must reuse the tested `agentic_cloud_radar/` core rather than copying business logic into Skill folders.
- The repository version is the source of truth for Mentor review and cross-computer continuity. Personal installation under `$CODEX_HOME/skills` is optional and must not replace the Git copy.
- For presentation and handoff, every Skill must show its GitHub-relative file location, especially `radar-redesign/skills/<skill-name>/SKILL.md` and `radar-redesign/skills/<skill-name>/agents/openai.yaml`, so another Codex or teammate can discover the instruction file and execution prompt reliably. When explaining non-local Skill discovery, say that Codex first reads the available Skill list, then uses tool/plugin search for deferred external capabilities, and always reads the selected `SKILL.md` before acting.

## 2026-07-30 Skill 3 / Skill 4 Decision Model Gap

- Historical problem: the former single `recommend_s4` field conflated low-risk validation with AWS PoC review.
- This caused the same Lambda self-managed S3 code storage technology to appear contradictory across runs: a context-rich run recommended the lowest-risk Skill 4 path, while a context-free run rejected Skill 4 because deployment governance boundaries were missing.
- Resolution superseding the v2 design: S3 schema `s3.evaluation.v3` uses public official evidence by default and emits `recommend_low_risk_validation` plus `eligible_for_poc_review`. Missing company context, custom environment, feature-level Region confirmation, or an official pricing link is a review note, not a technical rejection or configuration gate.
- Legacy `recommend_s4` and `eligible_for_paid_poc_review` remain compatibility aliases only. New user-facing output and decisions use the generic PoC terminology.
- Deployment authorization remains separate from technical eligibility: a real resource-creating run still requires the selected candidate, named human approval, a fixed small cost ceiling, a registered recipe, explicit `--execute`, Console review, and controlled cleanup.

## 2026-07-31 Skill 3 / Skill 4 Single-PoC Decision

- Cleo 定義的 Skill 4 是唯一會建立受控 AWS 資源、可能產生費用的 PoC 階段；不得再把文件、本機或 schema 檢查稱為「低風險 Skill 4 驗證」。
- 後續正式流程採單項評估：Skill 1 / Skill 2 可以掃描與比較多個候選，但 Skill 3 起一次只接受一個由人類選定的候選，不再追求「所有候選跑完五步再取 top 3」或一次挑三項。
- Skill 3 必須在候選進入 Skill 4 前產出整套可稽核的 PoC 預估報價單（low/expected/high、品項、費率、假設、排除項、來源與核准上限）。沒有已登錄費率模型時，Skill 3 必須標示 `needs_registered_cost_model`，Skill 4 不可開始。
- S3 v4 的新決策僅使用 `recommend_poc`；舊 `recommend_s4`、`recommend_low_risk_validation`、`eligible_for_poc_review` 只可作舊 artifact 的讀取相容，不得出現在新報告或 UI 作為第二套標準。
- Lambda self-managed S3 code storage 的 2026-07-29 runtime 已由 Cleo 確認 AWS Console review 成功，狀態為 `ready_for_cleanup`；cleanup 尚未執行。

## 2026-07-31 Screenshot-Backed Console Cleanup Decision

- 後續新建的 Skill 4 runtime 一律使用 `s4.runtime-evidence.v3`：Codex 必須在已登入 AWS Console 檢視 CloudFormation Infrastructure Composer、截取圖片並上傳到具驗證的 GUI 或目前對話，讓具名人類確認後才可 cleanup。
- 截圖證據 JSON 必須包含 run ID、Infrastructure Composer 圖片參照、SHA-256、截圖時間與 `gui` 或 `conversation` 的分享管道。圖片本體及未遮蔽 Console URL 不可提交 Git。
- 人類明確確認後使用 `s4-close --execute` 自動執行 run-scoped AWS API / CloudFormation cleanup 與回查；不得用廣泛 Console 刪除動作，也不得跨 run 清除資源。
- Skill 5 只有讀到 `cleanup_verified` 的 runtime 才可輸出 actual-PoC final；新版 runtime 的 final 結論需呈現 Infrastructure Composer 截圖人工確認與 cleanup 回查。此規則不追溯阻擋已存在的 v2 runtime。

## 2026-07-31 Claude Review Flow Hardening Decision

- `s4-approval.json` 必須由正式 `s4-approval-template` 指令產生或符合其 schema，不再只靠人工手刻範例；approval 可明確帶 `run_id`、候選 ID、具名核准人、成本上限、Region acknowledgment、lineage 與 deployment 預設。
- Skill 4 的 Console review close 必須同時讀 runtime、review packet 與 review evidence；packet 不再只是死路清單。程式只驗 metadata、run ID、stack name、Region、必要 view、redact-before-hash 契約與分享管道，不自動判讀圖片內容；圖片內容由具名人類眼睛確認。
- Console 截圖流程固定為「隱藏／遮蔽 Console chrome → 截取中間 canvas → 對遮蔽後 PNG 算 SHA-256 → 顯示遮蔽後 PNG 給人類確認」。截圖檔、未遮蔽 Console URL、帳號資訊不可提交 Git。
- S4 付費部署的 Region gate 恢復為硬檢查：`available_ap_southeast_1` 可直接通過；`region_unknown` 只有在 approval 明確寫入 `region_warning_acknowledged=true` 才能部署。這不影響 S2/S3 的探索評估。
- 成本上限規則固定為取最小值：Skill 3 建議核准上限、人類核准上限、內建 sandbox ceiling。Skill 3 報價是靜態公開牌價 rate card 估算，不是即時 AWS Pricing API 或正式採購報價。
- 若 Console review 逾時、deployment 失敗或 cleanup 失敗，優先避免付費資源失控，可使用 `s4-abort --execute` 在具名成本控制確認與原因記錄下進行 run-scoped cleanup；此路徑不可被 Skill 5 寫成正常截圖確認 final。
- 新版 `s4.runtime-evidence.v3` 若缺 Infrastructure Composer 截圖 metadata，即使 cleanup 顯示 verified，Skill 5 也不得標成 final。報告文字需把 `recommend_poc` 解釋為「技術上具備受控 PoC 資格」，不是工作負載適配性或採用建議。
- 目前五個 Skill 是可重做的雷達流程包與 PoC 證據鏈，不是完整 production AWS 系統；Cognito/API Gateway/EventBridge/Step Functions/CloudWatch alarms/正式 CI/CD 等屬下一階段產品化範圍。

## 2026-07-31 Console Review Close Contract

- Console review packet now carries an explicit `review_deadline` (default 60 minutes). A timeout-based `s4-abort` must receive that packet and is rejected before the deadline; deployment or normal-close failures may use the cost-control abort path without a packet.
- The Playwright capture's `shared_via` is only the declared capture channel. `s4-close` and `s4-console-review` require `--shared-via` after human confirmation and store it as the authoritative `display_channel_confirmed` field.
- A new v3 runtime becomes Skill 5 `final` only after cleanup, screenshot metadata, and `display_channel_confirmed`. Forced cleanup becomes `final_without_console_review` / `closed_without_console_review`, never an actual-PoC final conclusion.
- Claude's proposed multi-Region `region_scope` and automatic fallback deployment were not adopted as current behavior because the core implements one target Region only. Keep that as a future enhancement, not an implemented claim in Skill documents.

## 2026-07-31 Self-Contained GUI Handoff Synchronization

- `radar-redesign/claude-gui-handoff` is a portable handoff package and must stay synchronized with the current five-Skill core, including `agentic_cloud_radar`, Skills, samples, tests, and the Infrastructure Composer capture script.
- The package is rebuilt through `radar-redesign/scripts/build-claude-gui-handoff.ps1`; the builder must preserve the current single-candidate Skill 3-5 workflow, complete Skill 3 cost estimate, Skill 4 Console review/cleanup contract, and Skill 5 final outcome rules.
- The GUI layer is intentionally retained during core synchronization; only its runtime contracts and portable package assets are refreshed.
- The portable package passed its standalone 39-test suite on 2026-07-31. Its architecture scan reports known productionization gaps (for example Bedrock/RAG/CloudWatch), which are outside the current five-Skill workflow scope.
- The architecture scanner contains an obsolete "top 3" matcher. The project decision remains one human-selected candidate evaluated through Skill 3, Skill 4, and Skill 5.

## 2026-07-31 Amazon Connect Customer Data Lake Article Run

- A single-item S1-S5 run was completed for AWS's 2026-07-17 article, `Build an Amazon Connect Customer Data Lake with a Reusable CDK Construct`, under run ID `direct-url-20260731-766826d4`.
- Skill 3 gave the candidate a 3.75 technical score but did not recommend deployment because its Amazon Connect / RAM / Lake Formation / Glue workflow has no registered PoC recipe and rate card. Singapore availability and candidate-specific pricing evidence also remain unverified.
- Skill 4 created no AWS resources and recorded `not_recommended_for_poc`; Skill 5 is an `interim` report. A future real PoC needs a reviewed recipe, a complete pre-deployment quote, an existing suitable Amazon Connect Customer instance, and explicit named approval.

## 2026-07-30 Default Context-Free Usage

- 不特別製作或標示「實習版本」。一般使用流程就是：Skill 1 蒐集、Skill 2 比較、真人選候選、Skill 3 依公開證據評估、Skill 4 驗證、Skill 5 報告。
- 不要求使用者提供公司問題、公司內部資料、自訂環境或禁止資料／權限表單。工作負載適配、Region 與價格尚未確認時，系統寫入 review notes，不要求使用者先完成複雜設定。
- Skill 3 的技術評估依固定 rubric、公開官方證據、hard blocker 與完整報價決定；不再使用信心指標。
- 真的要建立 AWS 資源時，才保留最小且必要的安全閘門：選定候選、具名核准、固定小額成本上限、已登錄 recipe、明確 `--execute`、Console review 與受限 cleanup。Region、測試資料、成功條件與 cleanup 範圍使用專案安全預設值。
- 程式內可保留既有 AWS profile 名稱作為實作設定，但文件與 GUI 只描述為隔離測試／sandbox，不以「intern」作為產品版本或使用限制。

## 2026-07-30 Mandatory PoC Quotation Decision

- Cleo 明確要求五個 Skill 流程必須想辦法產出報價單；成本不能只顯示 `unknown` 或拿固定 USD 3 policy ceiling 代替。
- Skill 3 對已登錄費率模型產出 `PoC 成本估算報價單`：Quote ID、Region、幣別、價格快照、有效期限、低／預期／高情境、逐項費率與公式、官方來源、排除項與建議核准上限。沒有模型時也要留下 `needs_registered_cost_model` 報價 artifact，不得填造數字。
- Skill 4 獨立檢查報價狀態與成本上限；Skill 5 必須在 JSON、Markdown 與 GUI model 呈現報價。成本仍不納入 Skill 3 技術分數。
- 報價一律標示為依 AWS 公開牌價與明列用量假設產生的非約束性估算，不是 AWS 帳單、發票或正式 AWS 銷售報價；實際費用須在部署後以 AWS 帳務資料核對。
- S3 Files 第一版費率模型使用 `ap-southeast-1` 公開牌價，預期情境為 2 小時／0.10 GB，高情境為 4 小時／0.50 GB；建議核准上限取高情境向上進位，不以 USD 3 固定 ceiling 冒充估價。

## 2026-07-30 Estimated vs Actual Cost Decision（Superseded 2026-08-03）

- Historical plan: Skill 5 originally planned to compare pre-deployment estimates with attributable AWS Billing / Cost Explorer / CUR evidence.
- Superseded by the 2026-08-03 merged PoC decision update: current Skill 5 no longer accepts billing artifacts and no longer performs estimated-vs-actual billing reconciliation. It only renders the pre-deployment public-rate-card estimate, runtime evidence, and limitations.

## 2026-07-30 Active S3 Files S4 PoC

- Fresh run=`direct-url-20260730-7339a0b8`，stack=`AgenticRadarS44D39751A`，Region=`ap-southeast-1`。
- 已驗證：CloudFormation `CREATE_COMPLETE`、S3 Files 掛載、S3→mount、mount→S3 與 SSM `Success`。首次立即回讀遇到同步延遲，驗證器已加入有限重試與同 stack 續驗。
- Cleo 已完成新 stack 的 Console review；run-scoped cleanup 與獨立回查完成。CloudFormation stack 不存在、S3 Files file system 0、run-prefix bucket／IAM role 0、測試 EC2 terminated，Skill 5 status=`final`、conclusion=`validated_and_cleaned`。

## Presentation Schedule

- The AI PM sharing session is scheduled for the afternoon of 2026-08-19. It is not a section meeting / 科會: Cleo and mentor will co-host the session, and Cleo has 15 minutes to share her actual AI PM usage experience. Do not keep or recreate the obsolete 2026-08-11 15:30 AI PM report task in README.
- The final cloud technology radar internship presentation date is changed from 2026-08-17 to 2026-08-14. Current title: `《預言者雷達：看見技術的下一步》`. The talk should be planned as a 30-minute presentation excluding Q&A, using the elevator-pitch structure: one clear core claim, then layered evidence, process, deliverables, validation, constraints, and next steps.
- 2026-08-14 update: Cleo reported that the final `預言者雷達`成果發表 has been completed and received generally positive on-site feedback. Treat this as user-reported presentation feedback unless a formal written or named evaluation is later provided.
- 2026-08-17 assistant-manager transcript feedback: Cleo provided an excerpt from the meeting transcript of the assistant manager's feedback on the 2026-08-14 `預言者雷達`成果分享. Treat it as feedback for the AI technology radar / five-Skill `預言者` project, not as AI PM feedback. Main points: the direction is valuable because it turns GPT-style ad hoc questioning into a structured workflow from information organization and evaluation through controlled PoC validation; running PoCs in an authorized, risk-controlled environment is valuable; future value depends on moving the current external/sandbox approach into an internal company environment where colleagues can use their own accounts, and then extending it within the department or IT. Career note: Cleo can continue exploring research interests and keep contact with the company; this is not a formal hiring or performance decision.
- 2026-08-17 mentor-skill review note: Cleo provided a mentor-style quality evaluation based on the 2026-08-14 presentation VTT. Treat it as mentor-perspective feedback, not independent verification of AWS deployment, cleanup, cost, tests, or formal performance scoring. The review's main judgment is that Cleo has shown stronger process governance, evidence/risk awareness, stop-decision maturity, and non-technical communication; the next capability gap is not more PoCs, but turning the workflow into a measurable service proposal with scope, cost/benefit, safety/environment boundaries, decision gates, and reproducibility evidence.
- The next suggested mentor review gate is a one-page `預言者雷達服務化提案` that Cleo should personally own the conclusion for. AI may help structure or check it, but must not replace Cleo's judgment. Required content: source scope and exclusion rules, one-run AI token/cloud cost and cost ceiling, measurable benefit such as saved screening time or usable candidate count, internal account/permission/data/PoC environment boundaries, Skill 3 stop conditions, PoC approval and cleanup evidence, Git commit/startup steps, at least one rerunnable case, and failure-reporting path.
- 2026-08-11 update: Cleo reported that the initial 2026-08-14 final presentation deck has been produced. Treat it as draft-complete and awaiting review/polish; do not claim AI has inspected the actual deck file until the file is provided or explicitly located and reviewed.
- 2026-08-05 correction: a Claude-produced AI PM deck is draft material only, not a completed deliverable or verified presentation result. Cleo will substantially revise it; do not state that the AI PM presentation, its slide count, speaker notes, or final narrative is complete until Cleo explicitly confirms completion.
- 既有 AI PM 簡報與 10 分鐘講稿僅為草稿素材；8/11 前須由 Cleo 大幅調整並明確確認可用版本，不能直接宣稱沿用或已完成。
- Cleo will attend the 2026-08-03, 10:30 department meeting as a listener only; no presentation is required.

## 2026-07-29 Active S4 PoC

- Lambda self-managed S3 code storage 的 live S4 PoC，lineage 為官方 direct URL run `direct-url-20260729-9d2a3d3c`。Cleo 已確認 AWS Console review 成功，runtime 現為 `ready_for_cleanup`；尚未執行 cleanup。
- 已驗證：CloudFormation `CREATE_COMPLETE`、Lambda 為 `S3ObjectStorageMode=REFERENCE`、invoke 成功。這是 intern 非 production 帳號證據，不是公司環境驗證。
- 不可自動 cleanup；Cleo 確認 Console review 後，使用 reviewed runtime artifact 與明確 `s4-cleanup --execute`。cleanup 僅限 run-derived stack 與其 versioned test bucket。

## 2026-07-29 Repository Cleanup Decision

- 新版唯一可部署主線為 `radar-redesign/` 與其目前維護的 S3 Files、Lambda self-managed code storage PoC recipe。
- 舊 `cathay-techintel-v3` AWS pipeline、其本機原始碼、舊 CloudFormation、S0 入口草案、舊 GUI 與已暫停的線上投保 PoC 不再是可部署或可展示成果；清理時可移除。正式日誌與 AI 執行軌跡僅作為歷史記錄保留。

更新日期：2026-07-29

這份檔案記錄會跨工作階段持續沿用的偏好、目標與決策。開始工作前先讀取；使用者提出新的長期規則時再更新。不得把密碼、Token、AWS 金鑰或其他敏感資訊寫入此檔。

## 長期目標

- 完成 Cathay Tech Intel / AWS 技術雷達 PoC、部署與成果整理；後續新版本不要再用 `v3` 這類內部版本詞當專案名稱或對外品牌。
- S1~S5 的原始專案設定不是只有「流程階段」或「日誌評分欄位」，而是要逐步做成五個可重用的專案 Skill：Skill 1 Scan、Skill 2 Compare、Skill 3 Evaluate、Skill 4 Validate、Skill 5 Report。後續 dashboard、GUI、final proposal 與實作待辦都要能回扣到這個 Skill 化目標。
- 2026-07-24 使用者決定：整套技術雷達可以重新定位、重做與重新部署，時間上不需要慌。新版本要先慢慢討論架構、資料來源、評分邏輯、程式設計、部署方式與後續維運，再進入實作；不得在舊系統上快速修補表面問題。
- 使用者判斷：GUI 主要用於展示、說明流程與讓主管快速理解；真正能讓同事在工作上反覆使用的交付物應優先是完整且好用的 Skill。後續規劃應把「Skill 產品化」視為核心難題，GUI 作為 demo / presentation layer。
- 使用者選擇「咬西瓜的博美」作為 Codex 對話中的固定小寵物形象。此為對話陪伴偏好，不是技術雷達的產品功能、正式交付物或實習日誌素材。
- 逐步製作 final proposal 簡報，而不是等到最後一次才彙整。
- Final proposal 的主軸是完整專案成果：解決的問題、執行方法、交付成果、成效、成功案例與可落地性。
- 簡報必須包含一張「專案執行軌跡圖」，呈現專案如何從問題定義、方案演進、PoC、評估到公司帳戶落地準備，而不是只有最後成果。
- Final proposal 後續需思考如何呈現「AI 使用軌跡」：不要做成聊天紀錄流水帳，而要呈現 Cleo 如何逐步把 AI 從問答工具用成 AI PM／工程協作者。可用軌跡圖或案例組呈現：原始白話指令、AI 轉譯成可執行工作、Cleo 修正 AI 的判斷、規則被寫入記憶、下一次工作方式因此改變，以及哪些輸出最後成為日誌、程式、簡報或驗證證據。
- 「目前專案框架圖」與「執行軌跡圖」必須分開：框架圖呈現現有系統模組、資料流與目前進度；軌跡圖只呈現專案如何一路演進，可在簡報中並排作為輔助。
- 「公司如何幫助我成長」是 final proposal 的必要一頁，但不是整份簡報主軸；需用具體前後差異與證據支撐。
- 2026-08-19 下午是 AI PM 使用分享，不是科會。Cleo 與 mentor 一起主持，Cleo 有 15 分鐘分享 AI PM 的實際使用方式。內容需展示：使用者 input 指令與 AI output 的差異（含過去紀錄白話化）、跨事件記憶／串聯、AI 對人類工作的實際幫助、主動反問與待辦機制，以及 spec-driven 邊界設定。不能只展示功能，要有實際前後差異和限制；不要直接沿用舊版草稿。
- 此 AI PM 使用分享簡報可參考既有國泰實習匯報的企業感、高留白、卡片與流程視覺節奏，但必須重新設計內容與封面；封面不放使用者照片，不把原本的 AI 雲端技術雷達簡報直接改題使用。
- 2026-07-24 Mentor 討論後修正 AI PM README 管理規則：待辦事項只放需要被解決且有時間要求的事情，依截止日排列，需寫出對應目標、完成條件與狀態；完成後移除或歸檔，不能長期掛著。無明確期限的想法放入研究文件或 inbox，不放在主 README 待辦。
- 主 README 的「重要交付物」只放真正要提交、展示、匯出或供主管評核使用的成果；AI 執行軌跡、一般 README、內部流程文件、草稿素材不放在第一層重要交付物，除非當下正要交給主管或作為正式附件。
- 近期固定時程：2026-08-03 10:30 部會出席聆聽，不需報告；2026-07-30（四）上午人壽高管交流活動（總公司）；2026-08-06 至 2026-08-07 到信義區參加集團 AI 競賽，當日不進內湖辦公室；2026-08-10（一）人壽 1st 共融活動（六度空間）；2026-08-14（五）部會展示最終實習成果報告《預言者雷達：看見技術的下一步》；2026-08-19（三）下午 AI PM 使用分享（Cleo 與 mentor 一起主持，Cleo 分享 15 分鐘）；2026-08-20（四）人壽 2nd 共融活動（總公司）；2026-08-28（五）13:30 國立臺灣海洋大學教授到公司訪視評分；2026-08-31（一）集團結訓典禮（國泰金融會議中心）。已過日期不可留在 README 待辦，活動後再補進當日 inbox / 正式日誌。
- 2026-09-02 Cleo 更新近期 AI PM 待辦：2026-09-08（二）12:00 到延平大樓 712 和高教授討論專題；2026-09-08（二）19:00-21:00 線上參加 `AWS Educate 9th 雲端校園大使招募說明會`；2026-09-09（三）上午投遞 AWS 校園大使履歷；2026-09-09（三）19:00 射箭，可穿薄長袖。AWS 校園大使投遞前仍需確認履歷與作品集主軸凸顯國泰人壽雲端技術發展部雲端應用開發科、AI 驅動的 AWS PoC 雷達、AI PM、雲端 / AI / 技術推廣經驗。舊的 2026-08-21 投遞期限不再作 active deadline。
- 2026-08-28 Cleo 回報上午已完成 mentor 離職 / 交接事項盤點；`README.md` 近期待辦已移除此項，正式日誌待 17:00 後統整。
- 2026-08-28 Cleo 回報 FinTech 國際校園大使推薦信用印審查已完成；`README.md` 近期待辦已移除此項。
- 2026-08-30 Cleo 補記：2026-08-29 已完成 ASML 校園大使投遞；目前只可記為已投遞，不宣稱錄取、面試或主辦單位回饋。
- 2026-08-31 Cleo 回報已完成 CIP 集團結訓典禮與國泰黑客松「步步公億走」提案報告；組別獲得第一名與 4,000 元禮券，Cleo 是主講者之一，主講 AI 在個人化推播系統中的角色、程式化節省 token、動態滾動更新、測試相容性、ESG 城市足跡與「起來嗨!」提醒功能。此為 Cleo 回報與同儕回饋素材；正式書面評審評語尚未取得。
- 2026-08-31 final proposal 成長素材：mentor 古永忠曾分享將重複步驟程式化以減少 AI token 消耗，啟發 Cleo 用在黑客松提案；mentor 也提醒 AI 時代創意與快速執行的重要性。這可作為「公司 / mentor 如何幫助 Cleo 成長」的具體前後差異證據。
- 2026-08-31 實習收尾情感素材：Cleo 中午與五位實習生吃緬泰料理，晚上與「腳踏車小隊」從金控附近走到河濱公園散步拍照、在橋下溜冰場玩比手畫腳、逛饒河街夜市並約寒假再見。Cleo 覺得能在職場交到一群愛運動、好笑且願意保持聯絡的朋友很難得，也會想念 mentor 與雲端部門；這可作為 CIP 帶來組織融入、同儕連結與被照顧感的結訓素材。
- 2026-09-01 Cleo 要求保留 2026-08-31 原正式日誌，另外新增長版實習總結；檔案為 `logs/daily/work-log-2026-08-31.md` 與 `logs/daily/work-log-2026-08-31-internship-summary.md`，兩份都需推送到 GitHub。
- 實習文件固定期限：CIP 雙週工作進度（7/20-7/31）於 2026-07-31 整理 / 匯出；CIP 雙週工作進度（8/3-8/14）於 2026-08-14 整理 / 匯出。Cleo 於 2026-08-21 確認 2026-08-28 不用繳交 8/17-8/28 雙週誌，不再列為待辦或固定交付。四張評分表也已完成評分並印出簽核或送繳，不再列為待辦。
- 2026-08-28 Cleo 回報 13:30 海大教授公司訪視評分已完成；訪視時不另外準備專案簡報重點或成果證據包，直接拿 2026-08-14 部會成果簡報／剪報給教授看。
- 2026-09-02 Cleo 回報已將實習抵免學分文件交給系辦，實習抵免 4 學分行政事項已處理完成；若系辦後續要求補件，再另開待辦。Cleo 也新增 2026-09-14（一）當週普通物理（上）3 學分人工加簽待辦，需找光電系教授簽名並確認後續送件 / 系統登錄流程。
- 2026-08-21 mentor 後續學習建議：Cleo 可補強如何閱讀資產負債表，以及理解國泰金控旗下子公司各自的收益與投資成效。這是金融 / 商業理解的長期補強方向，不可寫成已完成學習。
- 2026-08-24 Cleo 開始補會計基礎；目前看到第 5 支影片，內容進到綜合損益表。這只能記為進行中學習進度，不可寫成已完成財報分析或已能分析金控子公司收益。
- 2026-08-21 剩餘實習日程學習計畫：Cleo 打算看完 Udemy `Ultimate AWS Certified Solutions Architect Associate 2025` Part 1；該部分約 100 部 3-5 分鐘短片，目前看到第 12 部，仍在 IAM 單元。
- 2026-08-21 Cleo 確認四張評分表都已完成評分並印出簽核或送繳；README 不再保留評分表快速入口、重要交付物列或評分表待辦。評分表檔案可保留作歷史紀錄，但不再作 active todo。
- 2026-07-27 使用者新增硬截止：本週五 2026-07-31 要完成專案第一版完整交付，重點不是只整理雙週進度，而是要交出可給 Mentor 確認的完整 Skills 版本。完成條件包含：S1-S5 五個 Skill 的 `SKILL.md` 或等價規格文件完整、S0 需求輸入層可銜接流程、至少一條新聞 / 需求案例可完整跑過 S0-S5、本機檢測與輸出證據可重現、限制與未完成項目清楚標示，並整理 Mentor review package。
- 2026-07-29 交付計畫重整：7/31 前不再擴充新功能，改以證據收斂為主。最低交付為一條公開 AWS URL 完整走過 S1-S5、五個 Skills 的可讀跑法與限制、檢測清單、Mentor review package 與 CIP 雙週工作進度。已知基線為 S3 Files 真實 PoC 已部署、回驗、cleanup；Lambda self-managed code storage 已部署與 invoke，待 Cleo 完成 AWS Console review 與 cleanup 決策。對外一律標示為 intern 非 production 環境證據。
- 2026-07-24 容量校正：扣掉 2026-07-28 科會上午、2026-07-30 活動、2026-08-06 至 2026-08-07 集團 AI 競賽、2026-08-10 活動、週末與 2026-08-14 發表日，最終部會成果展示前可用工作日已明顯壓縮；2026-08-11、2026-08-12、2026-08-13 必須優先收斂 final deliverable，不再任意展開大型新功能。
- 剩餘工作日策略於 2026-07-27 再校正：2026-07-31 是第一版完整交付硬截止。2026-07-27 收斂科會報告並完成 S0/S1 最小可跑切片；2026-07-28 科會後推進 S2/S3；2026-07-29 完成 S4/S5 與端到端重跑；2026-07-30 上午公司活動，下午只做修補、文件與風險整理；2026-07-31 完成全流程檢測、Skills 文件、Mentor review package 與 CIP 雙週進度匯出。若新需求無法支援「7/31 Mentor 可確認版本、最終成果發表、可驗證證據」三件事，預設延後或移出主線。
- 階段性指標要切成可慢慢消掉的小目標：例如科會報告證據收斂、雙週進度表匯出、final proposal 主線、評分表匯出、最終展示演練。每個目標都要能回扣到專案核心成果或正式實習要求，避免因零碎紀錄而發散。

## AI 協作與工程審查規則

- 使用者明確要求 Codex 對專案保持嚴格，不做 vibe coding 式的成果美化。後續回報必須主動區分 `已驗證`、`部分驗證`、`使用者回報但待核對`、`未驗證／推測`，不能把順利片段寫成完整成功。
- 程式與部署工作不得只針對 happy path 通過測試；若存在 timeout、權限不足、網路中斷、成本、cleanup、資料格式、權限驗證或安全輸入風險，需在交付時明列風險與下一步。
- 不得為了讓專案看起來容易通過而降低標準，例如把 `validate-template` 說成已部署、把單點 CLI 成功說成端到端驗證、把 fallback/rubric 結果說成正式 LLM/API 成果、或把主管／mentor 未確認的內容寫成已確認。
- 對外文件和 final proposal 必須保留工程限制與修正歷程；可以用白話寫，但不能刪掉會影響判斷的失敗、回退、未完成驗證與資安限制。
- 使用者希望 AI PM 主動提出必要的反問、把可執行事項列成待辦並追蹤完成條件；但反問必須有助於消除重要範圍、風險或驗證歧義，不能為了形式增加中斷。較大工作採 spec-driven：先寫清目標、授權邊界、非目標、驗證方式、成本／cleanup 與交付物，再執行。
- 2026-07-28 使用者要求：之後完成檔案修改後，除非使用者另有指示或工作區狀態不適合，預設要直接 commit 並 push 到 GitHub；若工作區有大量既有未提交變更，僅提交本次相關檔案並明確說明未處理的其他變更。
- 使用者想學 Codex 寫的程式碼細節；後續較大的程式修改要提供可閱讀路線，包含主要檔案、核心函式、資料流、測試方式與建議閱讀順序，讓使用者能在 VS Code 或其他編輯器一邊看 code 一邊理解部署。
- 新版重做時，Codex 必須逐段解釋每段程式碼的意義、資料從哪裡來、可能疏漏、以及哪些因素會讓驗證結果不可靠；不能只交付能跑的程式。每個階段都要和 Cleo 對齊後再往下做。
- PoC 的執行過程和原理必須讓使用者自己理解，不能只由 AI 代跑完成；每次 PoC 後都要整理「我如何能再做一次」的重點，例如資源建立順序、控制線／資料線、關鍵指令或 Console 位置、成功與失敗判斷、cleanup 順序。
- AWS PoC 的驗證不能只靠 CLI 輸出；需要安排使用者手動進 AWS Console 確認關鍵資源與結果，例如檔案是否真的上傳／同步、通道或 mount target 是否建立成功、EC2 或 Step Functions 狀態是否合理。AI 可協助給檢查路徑與判讀方式，但正式記錄要區分「Console 已人工確認」和「CLI 查詢確認」。
- 下一次重做 S3 Files + EC2 掛載 PoC 時，優先採 CDK 專案產生 CloudFormation stack，再用 CLI 部署；目的不是只讓 AI 跑成功，而是讓使用者能在 CloudFormation console 的 stack resources / template / Infrastructure Composer 視覺化介面看到資源關係，理解 bucket、S3 Files file system、mount target、access point、VPC、security group、EC2、IAM role 之間怎麼串起來。

## 技術選題限制

- 2026-07-20 mentor 討論後，當前主線暫停「線上投保系統穩定性測試」與 S0 需求輸入建置；近期優先深化既有 S1~S5 技術雷達核心能力。新測試目標是：給 AI 一小段 AWS 新聞或遮蔽／截斷過的資訊，觀察它能否自行抓重點、去除廣告詞、查找相關資料、推論實作步驟、用 CLI 或最小 PoC 驗證，並產出可信的 S1~S5 評估報告。除非使用者重新指定，後續 AWS 新聞評估不要硬套回保單系統情境。
- 日後新技術選題、範例報導與實作驗證，不主動選 Amazon Bedrock 或 Bedrock AgentCore 系列，因公司目前無法使用。若資料蒐集時遇到 Bedrock 內容，只能作為「不採用／限制說明」或概念對照，不能列為推薦實作路線，除非使用者明確要求。
- AI 自主執行 AWS 新聞 PoC 的預設規則：可在 `ap-southeast-1` 新加坡區域使用 `intern` profile 建立必要資源並產生 AWS 成本，但仍排除 Bedrock；若 AWS login / MFA / session 過期，需請使用者協助重新登入；遇到 IAM `AccessDenied` 時，先自行評估替代做法或降權路線，不立刻要求 mentor 放權限；建立 EC2、VPC、IAM 等資源前，需用白話說明會建立什麼、為什麼需要、可能產生成本與 cleanup 方向；刪除資源前後需確認 cleanup 範圍與結果。不得把 AWS 憑證、私鑰、完整帳號 ID、完整 ARN、IP 或敏感資源細節寫入 repo、日誌或報告。
- 線上投保系統穩定性題目必須建立在既有雲端技術雷達流程之上：先由雷達掃描與比較可用雲端技術，評估是否適合線上投保情境，產出成本／使用報價，再挑選候選方案做 PoC 測試與報告；不是另開一套脫離雷達的監測工具。
- 技術雷達後續第一層級應為「應用端需求輸入」：使用者先在 GUI 或需求表單輸入目前遇到的業務／系統問題、舊有方法為何無法解決、限制條件與成功標準；系統再依此啟動 S1-S5，搜尋新技術、比較適配性、報價、驗證並產出給人類審核的改良報告。
- 若使用者不知道公司實際遇到哪些問題，雷達前面需增加「S-1 問題發現／問題候選蒐集」：用低侵入、非敏感來源整理可能痛點，例如訪談問題清單、公開或內部非敏感文件、常見金融雲端場景、既有日誌中的阻礙、主管指定方向，再由人類確認後進入 S0 需求卡。
- S0 需求輸入層不應直接負責對外搜尋。S0 可選擇性使用 LLM 協助把使用者描述整理成需求卡、追問缺漏欄位與檢查敏感資訊；真正的外部資料搜尋與技術蒐集應在 S1 Scan，且需等 S0 需求卡經人類確認後才啟動。任何 LLM/API key 都必須放在後端或 Secrets Manager，不可出現在 GUI、repo、日誌或報告中。
- 舊版技術雷達曾使用受控 `seed_article` 重跑歷史新聞；此設計已不適用新版 `radar-redesign`。新版正式 S1 僅保留 2026-07-28 定義的 `url`／`rss` 真實官方資料入口。
- 所有新版 RSS 或 URL 候選都必須先完整通過 S1-S3 決策報告才可申請 PoC。PoC 技術資格要求 Skill 3 加權分至少 3.75 / 5、沒有 PoC blocker、報價狀態為 `estimated`，且 Skill 4 有可部署 recipe；即使符合也只代表可交由 Cleo 人工決定，`automatic_poc_start` 固定為 false。真人仍需核准範圍、成本、成功標準與 cleanup，雷達不得自行建立付費 PoC 資源。
- 2026-07-24 釐清：若使用者尚未在 human review gate 核准，對外與日誌口徑應說「自動流程完成到 S3 評估／PoC 候選資格判斷」，而不是說「已啟動或完成正式 PoC」。S4 若只產生低風險 validator artifact、rubric fallback 或重用既有驗證證據，需明確標示為非核准 PoC；任何會新建或變更 AWS 付費資源的 S4 PoC 必須等 Cleo 明確同意後才可開始。
- 2026-07-24 AWS 回查修正：2026-07-23 16:26:33 Asia/Taipei，Cleo 已在 DynamoDB human pick log 對 `s3files-news-20260723-gate` 寫入 `decision=approve`，候選 `M-2E486BFB`，同意最小範圍 S3 Files PoC。此 approval 是正確 run 的人類核准紀錄，但仍不代表 record-human-pick Lambda 會自動建立 PoC 資源；後續 S4 執行仍需依核准範圍、成本、成功標準與 cleanup 做。
- 2026-07-24 使用者更正：不可在正式日誌或主管可讀文件中寫成「S4 雙向資料驗證與 cleanup 回驗已於今日完成」。若 AI 背景曾做過 AWS 查詢或整理，仍需先和 Cleo 的實際操作、理解程度與可展示證據對齊，才能計入 Cleo 個人日誌或 Skill 分數。
- 2026-07-24 重要品質修正：現行 S5 報告中的「企業案例比較」來自程式內建靜態 case study，不是 runtime 上網查詢；案例匹配只靠 tag 重疊，例如 `s3` / `lambda`，因此不可宣稱為外部企業比較或即時產業查證，也不應直接作為評分加分依據。後續 S5 必須改成：沒有 live search 或人工提供可引用來源時，只能標示「未查證外部案例」；若使用靜態案例庫，必須明確標示為「內建參考案例」，不可寫成新查到的企業證據。

## 日誌原則

- 週一至週五的正式日誌固定在 Asia/Taipei 17:00 統整；17:00 前不先寫當日 `work-log`，只把可驗證進度暫存在 `AI_PM_INBOX.md`。
- 2026-08-18 Cleo 更新：`預言者雷達` 專案已完成暑假初期設定的目標，也已於 2026-08-14 完成成果發表；2026-08-17 的收尾工作也不再保留 Skill 進度評分。既有 2026-08-14 以前的 Skill 分數、dashboard 與 `SKILL_PROGRESS.md` 只作為歷史追蹤保留，不再要求每日更新、累加或同步 Notion Skill score，除非 Cleo 明確要求做歷史校正。
- 2026-08-18 Cleo 更新：從今天開始，日誌不用再刻意繞著實習專案、專案價值或 Skill 框架寫；輕鬆、簡短說明今天做了什麼即可。除非正在寫正式雙週誌、評分表或主管可讀成果，不要固定放主管評分表、自評矩陣、長篇證據段或過度專案化的收尾分析。
- 2026-08-17 起，正式日誌仍可描述工作對 `預言者雷達`、AI PM、評分表、分享、服務化提案或實習收尾的幫助，但改用成果、證據、目標對齊與下一步說明，不再使用「掃描／比較／評估／驗證／報告」五項整數積分表作為日誌固定欄位。
- 正式每日實習日誌是由 Codex 代 Cleo 書寫，語氣要像 Cleo 本人的實習紀錄：白話、少廢話、直接、自然、具體。每篇第一段必須讓主管一眼看懂「今天到底在做什麼、為什麼對專案有用」。可以用「我」，但不要每句都硬塞主詞；以成果、證據、問題、下一步為主，不寫過多感想、鋪陳或報告腔。不要用一堆專有名詞、檔名或 AWS 資源名稱假裝專業；檔名只留真正能幫主管追證據的少數項目。不要寫成第三人稱專案紀錄，也不要把 Codex 操作寫成敘事主體。若需要提到 AI，應寫成「我使用 AI PM 協助整理／驗證／追蹤」。
- 第一次討論關鍵字：個人工作日誌是讓 AI 代表 Cleo，用 Cleo 的角度書寫 Cleo 做的事；AI 做了什麼、Cleo 給了什麼指令，放到 AI 執行軌跡。
- 和 mentor 第二次討論關鍵字：PoC 的執行過程原理需要 Cleo 自己了解，不能只叫 AI 跑；Cleo 要具備再做一次的能力，並用 AWS Console 手動確認檔案上傳、通道建立等成功證據。
- 每日的「執行驗證」要改寫成「怎麼確認有做出來」：用白話說明結果，例如流程有沒有跑完、報告能不能打開、資料是否能讀回、哪裡仍待確認；不要堆長指令、長檔名、resource id 或專有名詞。
- AI 執行軌跡才記錄使用者給 Codex 的指令、使用者更正、Codex 的判斷、實際動作、工具驗證與流程問題；此檔可用 AI PM 視角，但不能取代正式實習日誌。
- 日常紀錄可以保留技術細節、決策理由、檔案位置、測試結果與未解問題，作為可追溯素材。
- 對外呈現的日誌使用簡單語言，合併相近事項並突出主線；避免把每個檔案、服務與數字都拆成零碎條目。
- 每日日誌不需要刻意寫很多；做到哪寫到哪，以實際進度為準，避免為了完整感把內容越寫越多。
- 個人每日實習日誌只放對 Cleo 本人專案進度有意義的主線、公司活動或可被主管理解的成果；AI 背景代跑、既有 PoC 重驗、展示型 GUI、截圖補證據等若不是 Cleo 當天核心推進，不要硬放進個人日誌或拿來灌分，應移到 AI 執行軌跡或證據資料夾。
- 雙週誌不要流水帳，不依日期逐項重述；改按「核心成果與影響、關鍵問題與解法、學習與成長、下期重點」統整。
- 只把有意義的內容升級到雙週誌：可交付成果、重要決策、解決的問題、能力成長、風險與明確下一步。
- 不虛構部署、測試、GitHub、Notion 或主管回饋；沒有驗證就明確標示。
- 對外週誌、雙週誌與主管可讀文件的措辭不要說得太滿；優先使用「已初步完成」、「已整理」、「使用者回報完成」、「仍待核對／驗證」等可被證據支撐的表述。
- 2026-08-14 以前的歷史日誌需指出工作推進了掃描、比較、評估、驗證、報告中的哪個 Skill，依證據給予整數積分，並判斷能否扣回該 Skill 的原始目標；五個 Skill 的每日加總最高為 10 分。此規則已由 2026-08-18 的「成果發表後不再計分」規則取代，僅適用歷史回查。
- 平日 17:00 的正式日誌仍以 Git 版本為主要紀錄；2026-08-11 起不自動做 Notion 同步，2026-08-18 起也不再要求同步 Skill 分數或積分儀表板，除非 Cleo 明確指定。
- 2026-07-21 已建立 Codex cron automation `17-00-skill`，目前用途是平日 17:00 Asia/Taipei 自動執行正式日誌統整；2026-08-18 起不再做 Skill 分數同步。若 17:00 未準時啟動，先檢查此 automation 狀態與專案路徑是否仍指向 `C:\Users\youhs\Documents\實習專案`。
- AI PM 評分與紀錄必須嚴格：做事前先定義本次工作屬於哪個 Skill 或動作、完成條件、checkpoint 與驗證方式；做完每一步都要有可檢查的證據，不能只用「感覺完成」計分。
- 對於較大的工作，先整理計畫型態與時間軸；若目標、驗證方式或主管期待不清楚，AI PM 可以主動反問再繼續。
- Git 內的正式每日實習日誌放在 `logs/daily/work-log-YYYY-MM-DD.md`；根目錄保留 `AI_PM_INBOX.md` 作為 17:00 前暫存。
- 2026-07-21 起，日誌增加「主管評分表自評」功能：四大項目為組織認同／組織承諾、盡責、團隊合作、創新求變；另追蹤 Mentor 表單 15 項行為觀察。15 項若缺少實際觀察或使用者補充，必須留白或標示 `暫不評分`，不可為了完整而推論分數；若使用者明確要求「假設 AI 是 mentor 來評分」，可提供 `AI 模擬 mentor 評分`，但必須清楚標示非正式 mentor 分數並附補強方向。累計檔為 `MENTOR_EVALUATION_PROGRESS.md`，主管可讀細則頁為 `dashboard/mentor-evaluation-details.md`。此分數是實習生自評與補強提醒，正式成績仍以主管評分為準。Notion 摘要頁為 `Cleo｜主管評分自評儀表板`：`https://app.notion.com/p/3a49d9fba316816c8f95d2a2ff997350`；Notion 細則頁為 `Cleo｜主管評分表細則與回覆`：`https://app.notion.com/p/3a49d9fba316814e923ad82718952a71`。
- 評估團隊合作、溝通及協調能力時，要考慮組織情境。若單位本來只有一個實習職缺或工作安排以個人專案為主，不能把「跨同事／跨團隊互動少」當成主要扣分理由；應改看 mentor 溝通、需求對齊、主動回報、文件同步與依回饋調整方向。
- 團隊合作亦應採計實際的實習生社群互動：2026-07-23 共融活動時與 11 位實習生共進午餐、建立交流，且平日中午持續與其他 IT 部門實習生一起用餐。後續可將此類融入、交流與合作證據寫入評分自評，但不混入技術 Skill 積分。
- 2026-07-21 起，建立 GitHub 評分表集合 `evaluation-forms/`。目前包含兩張國泰表單：`國泰｜實習生評鑑表單`、`國泰｜Mentor實習生狀況觀察表`，以及兩張國立臺灣海洋大學表單：`學生校外實習成效問卷（實習機構）`、`學生校外實習成績考核表（實習機構主管用）`。日後使用者問「評分表／評鑑表」時，先讀 `evaluation-forms/README.md` 再判斷要使用哪張表單，不要把不同表單混在一起。
- 2026-08-21 起，主 `README.md` 不再保留評分表快速入口；`evaluation-forms/`、`MENTOR_EVALUATION_PROGRESS.md` 與 dashboard 評分細則只作歷史紀錄和必要時查詢，不作首頁 active entry。
- 清理本機檔案時，只能刪 Codex 自己產出且已確認用不到的檔案；使用者提供、下載、或用途不明的檔案先保留並詢問。
- 自 2026-07-17 起，AI 也要維護自己的每日執行軌跡 Markdown，位置為 `ai-execution-trace/daily/YYYY-MM-DD.md`；每小時追加一次，記錄使用者當時給的指令或更正、AI PM 的判斷、實際處理、驗證證據與待接續事項，不寫專案前情提要，也不可寫成流水帳。

## 五個 Skill 儀表板

- 五個 Skill 依使用者提供的專案圖定義：🔵 Skill 1 掃描 Scan、🟢 Skill 2 比較 Compare、🟠 Skill 3 評估 Evaluate、🟣 Skill 4 驗證 Validate、🔴 Skill 5 報告 Report。
- 目前的五個 Skill 積分與 dashboard 是追蹤「專案是否朝五個 Skill 化前進」的管理層，不等同於已完成五個可安裝／可重用 Skill；記錄與簡報需避免把追蹤欄位誤寫成 Skill 已產品化完成。
- 積分只使用整數，且以「每日總分」而不是「每個 Skill 各自堆分」為主：研究、文件整理、模板驗證、單點 CLI 查證通常每日 1～3 分；本機 PoC 或離線驗證通常每日 3～5 分；公司帳戶端到端成功但仍有 fallback、未回驗或品質限制時通常每日 6～8 分；每日 9～10 分只保留給可重現、可展示、品質已回驗且對專案核心有明確里程碑意義的成果。
- 積分採嚴格標準：單純 Console 點按、照手冊建立資源、或只有使用者回報但尚未獨立回驗的部署進度，只能算低分；端到端跑通也要看是否有正式 API、cleanup、成本、安全、輸出回驗與主管可讀證據，不能因成果數量多就灌分。
- 2026-08-11 更嚴格評分修正：不得把同一份報告、簡報、時間表、HTML 集中整理、關聯圖或交接素材同時灌進多個 Skill 分數。素材整理通常只計入 Report；若其中產生新的決策規則或可驗證量測，最多再給一個相關 Skill 的支援分。Validate 只有在當日有新測試、live PoC、AWS 操作、cleanup 回查、可重跑驗證命令或新的驗證 artifact 時才計分；單純回查既有 artifact 不給 Validate 分。
- 2026-08-11 Cleo 更新同步規則：今後不要自動做 Notion 同步；除非 Cleo 明確要求，專案收尾以 Git / GitHub、README、正式日誌、dashboard JSON / HTML 與可提交檔案為主。
- 2026-07-22 使用者要求重算過去紀錄：每日五個 Skill 加總最高 10 分，做得不夠可更低。已採新口徑重評 2026-07-13 至 2026-07-21，累積總分從 107 下修為 53。
- 工作與目標的關係分成：`直接扣回目標`、`間接支援`、`偏離目標`。偏離目標可保留紀錄，但不計入 Skill 積分。
- `SKILL_PROGRESS.md` 保存 Git 版每日與累積分數；`dashboard/README.md` 是主管可在 Private GitHub 直接開啟的儀表板入口。
- Notion 的五項積分已直接加入 `Cleo的暑期實習日誌(2026CIP)` 每日紀錄，並以 `每日總分` 公式加總；2026-07-13 至 2026-07-21 已依每日總分最高 10 分的新口徑完成回填。
- Notion 儀表板頁已移入 `Cleo的暑期實習日誌(2026CIP)` 資料庫，從 `📊 儀表板入口` 檢視開啟，不再是工作區外層的獨立專案。頁面網址：`https://app.notion.com/p/39e9d9fba316813c8e68fa80f8f33d08`。
- 原始積分 data source `collection://ed56335a-cd24-4b70-8bf1-6fa25f87d1f0` 保留為證據明細；日誌 data source 為 `collection://cd79d9fb-a316-8208-9d99-073d0ac114e1`。

## 成長素材的蒐集方式

每次遇到下列情況，日誌增加「成長證據」：

- Mentor 或主管的回饋改變了做法或判斷。
- 公司提供的工具、帳號、流程或實務規範，讓工作從概念走向可落地。
- 從「需要指示」進步到「能自行拆解、驗證、交付或說明取捨」。
- 對真實專案限制（權限、成本、安全、部署、協作）的理解變得更完整。

## Final proposal 敘事原則

主線：從問題出發，說明一路如何做出選擇、修正方案、完成成果並驗證成效。

Mentor 於 2026-07-24 補充：最終部會實習成果簡報可用電梯簡報法，由一句核心主張一層層往下展開，並嚴格控制時間。前段要說明「為什麼這個專案值得做」，可用剪報／產業趨勢／公司情境作為引子；研究方法需交代參考資料來源、質化判斷與量化指標。敘事可接近論文形式，明確回答新穎性（以前沒有人或很少有人這樣做）與進步性（相較相近做法，本專案在哪些面向更進步）。

建議結構：

1. 專案背景與要解決的問題。
2. 專案目標與成功標準。
3. 執行軌跡圖。
4. 最終方案與核心流程。
5. 主要成果與交付物。
6. 成效與可驗證數據。
7. 成功案例：專案內的成功驗證，以及外部產業案例證據。
8. 過程中的關鍵取捨與修正。
9. 公司如何幫助我成長。
10. 結論、限制與下一步。

成效必須區分：已驗證、已實作但待公司環境驗證、估算或預期效果，避免把部署準備完成寫成已正式上線。

## Final proposal 成長頁核心敘事

建議主軸：公司不只提供一個題目，而是透過真實情境、回饋與工程規範，讓我從「完成任務」成長為「能定義問題、做出取捨並交付可驗證成果」。

## Git 同步狀態

- 2026-07-14：建立本機 Git repository。
- 2026-07-15：建立 private GitHub repository `gt52bts-dotcom/internship-tech-radar`，並設定為本機 `origin`。
- 專案以 Git 作為公司相容的主要延續機制；`AGENTS.md`、`AI_PM_WORKFLOW.md`、本檔與每日工作日誌共同構成 AI PM context。
- 遠端網址：`https://github.com/gt52bts-dotcom/internship-tech-radar`。
- AI PM 的每日日誌模板以 Notion 資料庫 `Cleo的暑期實習日誌(2026CIP)` 為準；Git 內保存相同的欄位規則與頁面章節，讓公司環境不連 Notion也能延續。
- 2026-07-15：主管閱讀方式決定維持 private repository，邀請主管為 Read collaborator；不使用會公開公司日誌內容的個人 GitHub Pages。
- 2026-07-15：新增 `dashboard/README.md` 作為 Private GitHub 內可直接閱讀、可展開日期的 Skill 儀表板；完整 HTML 互動版保留在 repository，但未公開託管。
- 2026-07-16：使用者指出 2026-07-15 分數偏鬆；2026-07-22 再次重評後，7/15 修正為掃描 +1、比較 +1、評估 +1、驗證 +1、報告 +1，合計 5 分。理由是公司 AWS Console 第 1 至第 4 章部署多屬必要但簡單操作，且公司 AWS 資源狀態仍待權限允許後獨立核對。

## 公司帳戶部署決策

- 2026-07-14：因公司帳戶的 SCP／CloudFormation 權限限制，近期落地驗證改採 `雷達-v3-console手動部署包.zip`，完整 CDK／platform-upgrade 版保留為長期主版本。
- 使用者回報已在 `ap-southeast-1` 完成 S3、DynamoDB 與 Secrets Manager 的手動建立；實際資源名稱、DynamoDB key schema 與 SecretString 格式仍待公司帳戶頁面核對。
- Anthropic API 採 Claude Console 預付 usage credits；API key 僅存 AWS Secrets Manager，不寫入專案檔案、工作日誌或聊天內容。
- 2026-07-15：以有效的公司帳戶 CLI 身分實查時，Lambda、Step Functions、IAM、DynamoDB、Secrets Manager 與 S3 列舉／讀取動作皆遭 Organizations SCP `explicit deny`；因此 Console 手動部署也無法靠自行新增 IAM policy 繞過，需由公司 AWS 管理者調整 SCP／提供允許的部署角色或代為部署。
- 2026-07-15：手動包預期名稱的 S3 bucket 查詢結果為不存在；先前回報的 S3、DynamoDB 與 Secret 尚不能視為已驗證，需待有權限後依 Console 畫面核對實際名稱、Region 與 schema。
- 2026-07-15：使用者回報已依手動部署第 1 至第 4 章完成 Lambda 用 IAM policy、Lambda execution role、S3 bucket 與 lifecycle rule、DynamoDB table `cathay-techintel-v3-picks-log`；DynamoDB key schema 為 `run_id` (String) + `pick_time` (String)，Capacity mode 為 On-demand，Encryption 使用 DynamoDB owned key。此狀態待公司帳戶權限允許後再驗證。
## 2026-07-24 新版雷達交付形式補充

- 新版雷達完整後，除了展示用 GUI，也必須能拆解成五個可重複套用的 Skill：S1 Scan、S2 Compare、S3 Evaluate、S4 Validate、S5 Report。
- GUI 不是純展示圖，也必須是可實際使用的操作前端；後續預期部署到 S3 靜態網站或搭配 CloudFront。GUI 負責輸入文章、查看 S1-S5 狀態、檢視證據與分數、處理 human gate、開啟報告。長期可交接價值仍在五個 Skill 的規格、輸入輸出、評分邏輯、驗證限制和維運方式。
- 後續公司人員應可單獨使用任一 Skill，也可把五個 Skill 串成完整雷達流程。
- 2026-07-24 已開始新版重做的設計基準草案，先定義 evidence-first、human-gated、Skill-first 的新版定位，再開始後續程式與部署；舊系統只作為可沿用積木與品質反例，不作為直接改名沿用的主版本。
- 新版正式名稱定為「AI Agentic 雲端技術雷達與評估系統」。建議 AWS resource prefix 使用 `agentic-cloud-radar`，不使用中文、空白或版本詞；環境可加 suffix，例如 `agentic-cloud-radar-dev`。
- 新版第一版先做後端流程與清晰完整架構，GUI 可用但不先追求完整視覺包裝；S0 需求卡要放在 S1 前面；允許 runtime web search，但所有外部證據必須可追溯來源；S3 評分指標與門檻需另行討論後再定案。
- 使用者補充：公司沒有非常限制成本，成本不應是 S3 技術價值評分的主要因素；但本專案的 S4 PoC 定位是小型最小驗證，不是正式試點或大規模架構測試。因此 S4 PoC 單次預估成本不得超過 USD 3；若超過 USD 3，應拆小、先做本機程式測試或文件驗證作為開發證據，或另案說明並重新取得更高層級核准。USD 1 可視為低風險提醒線，不是技術是否值得研究的主分數。
- S0 可使用 LLM 作為 demand-card assistant，協助整理使用者輸入、判斷模糊處、產生追問與草擬需求卡；但 S0 不做外部搜尋、不抓 URL、不自行放行，最後仍需固定規則檢查與人工確認後才可進 S1。
- 新版開發仍在 S0 研究與切片理解階段。若 repo 中已有 AI 草擬或背景產出的 S0 程式、CLI 或測試，不能直接寫成 Cleo 今日已讀完、已驗證或已完成；需等使用者實際理解並完成可追溯測試後，才能列入正式日誌與 Skill Validate 分數。
- 2026-07-27 使用者回報已看完 S0 程式碼，主觀判斷「可以」，可作為後續銜接 S1/S2 的基準；但除非另有 CLI、unittest、compileall 或端到端輸入輸出證據，對外仍應寫成「S0 程式碼已由 Cleo 初步閱讀並認可」，不要直接寫成 S0 已完整驗證完成。
- 正式交付模式只保留兩種：Agent mode（在 Codex/LLM agent 中以 Skills 使用）與 Deployed mode（GUI + AWS backend）。不建立 mock/offline/假資料模式作為產品分支；固定範例與本機測試只作為開發驗證，不作為展示主線、評分證據或交付模式。
- 2026-07-27 新版 S1 本機切片已改為真實 URL 驗證：只有 S0 demand card 為 `confirmed` 才能跑；URL mode 會實際 fetch 人工確認的官方 URL、解析 title / meta description / 文章前段、標示 `external_fetch_performed`、`official_source`、`seed_article` 與 `rss_discovered=false`。已用 AWS News Blog S3 Files 官方文章真跑 S0→S1 CLI，`s1-scan.json` 狀態為 `scanned`，但這仍是本機 URL-fetch 切片，不代表 RSS/search discovery、LLM 評分或 AWS 部署完成。
- 2026-07-27 新增 Skill 化設計規則：S1-S5 後續都要設計成 LLM-ready，可由 Agent mode 或 Deployed mode 隨時注入 LLM 摘要、推論或候選 hints；但 LLM 輸出只能作為 hint layer，不可直接當作外部證據、官方 metadata 或評分結論。每個 Skill artifact 都應保留 `llm_*_used`、`trusted_as_evidence=false` 或等價欄位，並由官方 metadata、多來源證據、固定規則或人工確認校正。
- 2026-07-27 使用者再次強調「不要假資料」。S1 code 與測試已移除測試用 fetcher / `_aws_fetcher` 注入點；URL mode 的 CLI 與 unittest 都必須走 `_fetch_url()` 真抓官方 URL。若網路、URL 或 content type 失敗，應讓測試或 CLI 暴露失敗，不用替身資料讓流程通過。
- 2026-07-28 新版 S1 的正式資料入口固定為兩種，且都只能使用真實 AWS 官方資料：`url` 模式由 S0 human-confirmed 後實抓一個 `aws.amazon.com` / `docs.aws.amazon.com` 頁面；`rss` 模式由 S1 掃描程式內固定的 AWS 官方 RSS feeds、依 S0 問題與排除服務排序最新項目，再抓入選文章原文。不得再把 paste、service hint、seed article、fixture、手動 service metadata 或 LLM hint 放進正式 S1 artifact；RSS 單一 feed/文章失敗可記 warning 與 data gap，但不得用舊快取或假資料補上。`official_source` 加上 `external_fetch_performed` 只表示當次抓到單一官方頁面，仍不是跨來源驗證或最終推薦。
- 2026-07-28 規則更新：S1 不得侷限 AWS 官方部落格。`rss` 探索模式必須同時納入可追溯的公開開源專案來源；目前實作為 AWS RSS 加 GitHub Public Repository Search。每個 GitHub 候選需保留 query、repository URL、更新／push 時間、stars、forks、license、topics 與 archived 狀態。`url` 模式可接受 S0 人工確認的 AWS、GitHub、GitLab 或 Codeberg 公開 HTTPS 頁面；不接受任意網域、私有端點、貼文內容或假資料。官方文章與開源 repository 都只是 S1 初篩證據，不等於推薦或公司現況。
- 2026-07-28 使用者指出 AWS Blogs 下拉本身涵蓋大量分類與新文章；S1 不可把 AWS 情報視為單一 blog。`rss` 模式須依 S0 題目動態選取 AWS Blog／What's New 分類，並在 artifact 的 `source_catalog` 記錄選取分類、選源理由與抓取狀態。目前 catalog 包含 What's New、News、Architecture、Cloud Operations、Compute、Big Data、Artificial Intelligence、Security、Database；例如 CI/CD 題目必須看 Cloud Operations、Compute、Architecture，而非僅依最新公告排序。
- 2026-07-28 修正上述 catalog 範圍：AWS Blogs 目錄實際可解析 44 個分類，不是手寫的九個分類。S1 現在每次真實抓取 `https://aws.amazon.com/blogs/` 的分類選單，從動態目錄選取 S0 相關 feed；顯性 topic mapping 之外，也會以分類名稱和 S0 字詞比對，因此 Robotics、Open Source、Storage、Web3 等不需要重新硬編來源 URL 才能被選到。`source_catalog.aws_blog_directory` 要保留 directory fetch status 與 category_count，來源暫時不可用時才可退回少量 baseline feeds 並留下 warning。
- 2026-07-29 使用者再次確認：S1 過去架構的優勢必須保留，特別是能注意 AWS Blog 分類，並從每個分類往下找更細的新技術。後續不可把 S1 簡化成只看單一 blog feed 或只抓最新公告；AWS Blogs 動態分類、What's New 與可回查來源帳本是雷達的核心能力。
- 2026-07-28 使用者補充真正目標是先了解全方位的新技術，不限 CI/CD，近期至一年內皆可。S1 新增 `discovery_scope`：`focused` 用於一條明確問題；`landscape` 用於跨領域雷達盤點，會掃完整 AWS Blogs directory、What's New 與 GitHub public sources，再從每個 feed 的最新項目中選近期候選。S0 artifact 新增 `max_source_age_days`（預設 365）與 `max_candidates`（預設 20）。RSS 每個 feed 目前只讀最新 20 項，因此 365 天是候選時間上限，不可誤稱已讀完完整年度 archive。真跑 landscape：44 categories、45 feeds 都抓取成功，輸出 12 個跨領域 AWS 候選；此仍只是 S1 Scan，不是推薦或 S2-S5 完成。
- 2026-07-28 選題標準再校正：使用者真正優先的是「已正式可用（GA）」的 AWS 技術，不是最新文章。S0 的 `maturity_requirement=ga_evidence_required` 必須讓 S1 只保留本次抓到的 AWS 官方來源中有明確 `generally available`／`general availability` 字樣的候選，並在 artifact 留下原文摘錄。沒有字樣只能說本次來源未能證明 GA，不能猜成 preview 或非 GA；GitHub 開源 metadata 也不能證明 AWS GA，故該模式不納入 GitHub 候選。此為初篩證據門檻，不可稱完整 AWS GA／release archive 搜尋。
- GA 初篩需排除假陽性：文章若是 Preview／只提到未來才會 GA，即使出現 `generally available` 也不能納入；標題屬 monthly／weekly roundup、歷史熱門文章回顧或 recap 的來源，不可整篇當成一項技術候選。多項技術月報可作為發現線索，但後續比較需回到它引用的單一官方公告，不能以彙整文代替原子技術的證據。
- S2 Compare 的固定界線：只讀 S1 的可回查候選，整理技術路線、官方／GA 證據、導入前提與待確認問題；若 S0 只是全方位技術地圖、未指定公司痛點，S2 不得自動排名或推薦。成本、USD 3 PoC 可行性、公司環境可用性與業務適配性在沒有官方價格及人類脈絡前必須標示未確認；2026-07-31 起由人類只挑一項再進 Skill 3。
- 2026-07-28 使用者決定 S2 交由 Claude 協作設計。Codex 先產生的 `radar-redesign/agentic_cloud_radar/s2.py`、`tests/test_s2.py` 與 CLI `s2` 分支是未共同閱讀的草稿，不可算為 S2 完成，也可由 Claude 改寫；交接文件為 `radar-redesign/docs/S0-S1現況與S2-Claude交接.md`。
- 2026-07-28 Claude 無法繼續後，使用者要求 Codex 接手 S2。S2 現在為 evidence-first 本機實作：只讀 S1 artifact，重新抓 S1 官方來源，從文章實際連出的且 candidate-relevant AWS docs／pricing／Region URL 收集最多 3 筆補充證據；沒有連結就保留 `not_found` data gap，不可自行拼接官方 URL 或估價。S2 不自動排名、推薦、選 Top 3 或啟動 PoC；2026-07-31 起 S2 可保留多候選比較板，但 Skill 3 一次只接受 Cleo 選定的一項候選。
- 使用者希望每個新增 Skill 都有可逐段閱讀的超詳細說明；S2 已新增 `radar-redesign/docs/s2-極細註解版.md`，作為程式碼、真實 artifact、測試與限制的閱讀地圖。
- Windows PowerShell 相容規則：PowerShell 5.1 的 `Set-Content -Encoding utf8` 會寫 BOM；S0/S1 CLI input 必須用 `utf-8-sig` 讀取以同時接受 BOM／無 BOM JSON。CLI 產出的 UTF-8 無 BOM JSON 在 PowerShell 5.1 應以 `Get-Content -Encoding utf8 -Raw | ConvertFrom-Json` 讀取，否則中文可能被系統字碼誤解而使 JSON parser 失敗。

## 2026-07-28 Radar 架構決策

- S0 已從入口移除；使用者直接匯入公開 URL 時走 `S1 URL Import`，想探索技術時走 `S1 Discovery`。兩者都不需要 S0 confirmation。
- 原 S0 的問題定義、預期改善、成功條件與限制，改由 S2 對每個真實候選建立 `proposal_card`：來源支持的能力、待確認的問題與使用者、改善假設與程度、好處、規劃利弊、before/after 量測、stop conditions、下一步問題。
- 新加坡 `ap-southeast-1` 不再是 S2/S3 shortlist 硬門檻。S2 仍必須查 Region 證據，但只標 `available_ap_southeast_1`、`other_region_only` 或 `region_unknown`，缺證據時降級為 warning，不阻擋進 S3。S3 可把 `region_status` 放在導入前提扣分；正式付費 S4 PoC 才要求 `available_ap_southeast_1`、成本上限與人工核准三重檢查，否則降級為低風險驗證。
- S2 必須區分 source-backed fact、planning inference、unknown；不得用自動總分取代人類 shortlist。
- 2026-07-29 S2 已補上 `official_region_lookup`：AWS 公開搜尋索引只用於發現候選相關官方 URL，隨後必須重新抓取 `aws.amazon.com`／`docs.aws.amazon.com` 正文；搜尋 snippet、rank 與通用 endpoint 均不可作為 Region 證據。只有實抓同段同時出現候選功能詞與 `Singapore`／`ap-southeast-1` 才可把 Region 狀態提升為 `available_ap_southeast_1`；若查不到，只能說本次證據不足，不能寫成該功能必定不支援新加坡，也不能因此讓 S2 流程停止。
- 2026-07-29 S3/S4 本機切片已新增：S3 只吃 S2 artifact 與 human shortlist request，沒有 shortlist 就停在 `needs_human_shortlist`；固定 rubric 為 technical_value 0.35、adoption_prerequisites 0.25、verifiability 0.25、risk_and_stop_conditions 0.15，成本不列入技術分數。S4 只吃 S3 artifact，預設產生低風險 validation artifact，不建立 AWS resources；paid PoC 必須再通過 Region、USD 3、approved_by、automatic_poc_start=false 檢查。
- 2026-07-29 使用者修正 S4 交付定義：S4 的最終目標是可在已登入的 `intern` AWS 帳號完成完整、受控的 PoC 部署、功能回驗與 cleanup，而非只留低風險 validator artifact。每次正式 PoC 前，系統必須先通知 Cleo Skill 3 評估結果、候選、分數、Region 與風險、預計資源、成本上限、成功條件與 cleanup；必須等 Cleo 在通知後明確核准才可執行 `cdk deploy` 或建立任何付費資源。S4 後續仍不得自動啟動付費 PoC，也不得跳過 CloudFormation 與 AWS Console 的人工回驗。
- 2026-07-29 已完成一條新的實際 S1→S4 S3 Files PoC：Cleo 手動跑出的 S1/S2/S3 artifact 共用 run `direct-url-20260729-e330af79`，候選為官方 S3 Files 新聞、Skill 3 score `3.85/5`、`recommend_s4=true`。S4 deployment context 保留三個 artifact SHA-256，stack/resource prefix 衍生自該 run；CDK synth 後以同一份 CloudFormation 模板建立新 stack，因既有 CDK bootstrap role 不可 assume，未使用舊 bootstrap role。CloudFormation、CLI/SSM 與 Cleo 的 Infrastructure Composer 檢視共同證明 VPC/S3/S3 Files/mount target/access point/EC2 關聯，以及 S3→mount 與 mount→S3 均成功。Cleanup 時 versioned bucket 必須先清除所有物件版本與 delete markers；最終 stack、bucket、S3 Files 均不存在，EC2 只有 terminated 歷史、無 active 資源。這是可宣稱的實際 PoC，但只能代表這條 S3 Files 案例與 intern 環境，不能延伸成新版完整 S5 或公司生產環境已驗證。
- 2026-07-29 AI 協作定位釐清：S1-S4 的 runtime 行為目前主要由可重現的 deterministic code／AWS 服務執行（S1/S2 真實 HTTP fetch、S3 固定 rubric、CDK synth、CloudFormation resource creation、SSM 驗證），不是由 runtime LLM 自行操作帳號。Codex/LLM 的價值在於把 Cleo 的目標轉成可執行流程、設計與撰寫程式、解讀 artifact、在 CDK bootstrap role、PowerShell BOM JSON、versioned bucket cleanup 等真實錯誤出現時提出替代方案並維持證據與安全邊界；Cleo 則親自選候選、確認範圍、手動跑 S1-S3、核准 S4、在 Console 檢視與確認 cleanup。此「固定程式 + AI 協作判斷 + 人類核准」三層關係是 final proposal AI 使用軌跡的核心案例，不能寫成 AI 或 Cleo 單方獨立完成。
- 2026-07-29 使用者要求 S1-S4 持續提供可逐段對照程式碼的詳細註解；新增的總覽文件必須清楚區分 deterministic runtime、人工 shortlist／approval gate，以及由 artifact lineage 驅動的外掛式真實 PoC runner，不能把本機 S4 validator 說成會自行部署。
- 2026-07-29 S2 Region 規則補強：對 `ap-southeast-1`，官方候選相關句子若明示「all commercial AWS Regions」或「所有商業 AWS 區域」，且同句提到該候選已偵測到的服務，可視為功能級 Region 證據並標為 `available_ap_southeast_1`；一般泛稱 AWS Regions、無候選服務上下文或不相干的 Region 文字仍不可通過。這保留嚴謹證據界線，也避免明確全商業區公告被錯標為 `region_unknown`。
- 2026-07-29 S4 正式實作目標已落成控制流程：`s4` 保留 validator；`s4-deploy` 會由完整 S1/S2/S3 lineage（重新讀取 stage/run/candidate 並保存 SHA-256）建立 deployment context，且只有 `paid_poc`、成本、真人核准、`deployment_authorized=true`、`automatic_poc_start=false`、成功條件、cleanup 範圍與候選專用 recipe 都通過後，另加 CLI `--execute` 才可建立資源。部署後必經 `s4-console-review` 人工 Console 回驗，才可 `s4-cleanup --execute`；cleanup 驗證 stack/resource prefix 必須由同一 run 衍生，且只清除該 stack 的 versioned test bucket。現已註冊並有既有真實部署證據的 recipe 是 S3 Files；其他候選必須明示 `needs_poc_recipe`，不可套用 S3 Files 模板。
- Region 仍不應卡死 S4：若 S3 為 `region_unknown`，Cleo 可在完整 approval 加上 `region_warning_acknowledged=true` 後進行人工核准部署；此只接受已明示的 Region 證據缺口，不能略過成本、lineage、recipe、成功條件、cleanup 或人工核准。
- 2026-07-29 新增 `lambda_self_managed_s3_code_storage_cdk` S4 recipe：使用 run 衍生名稱的 versioned/encrypted/non-public S3 bucket、CloudFormation custom resource 上傳非敏感 zip、bucket policy 只允許 Lambda service principal 讀取該 object version，並以 `AWS::Lambda::Function.Code.S3ObjectStorageMode=REFERENCE` 建立測試函數。S4 驗證會檢查 CloudFormation output 的 reference mode 與 S3 version，再 invoke 函數。已通過 CDK synth/模板契約檢查，但尚未取得此 Lambda 候選的 paid-PoC 人工核准，不能宣稱已 live deployed 或 cleanup。
- 2026-07-29 S4 成本欄位語意修正：若官方來源未提供可用於本次 PoC 的數字，approval 使用 `approved_cost_ceiling_usd` 記錄 Cleo 明確授權的 spend cap（不得超過 policy 的 USD 3），而不是把它偽裝成 AWS 官方估價；有官方數字時才可使用 `estimated_usd`。兩者都要通過同一成本上限檢查。
## 2026-07-31 Skill 3 Quote Report Rule

- Skill 3 Evaluate must expose a human-readable PoC quote report for the single selected candidate, not only an embedded JSON quote object.
- If the selected candidate has no registered recipe/rate card, Skill 3 still emits a quote report with status `needs_registered_cost_model`, the quote id, missing inputs, and the reason no dollar amount can be produced.
- The Amazon Connect Customer Data Lake article run now has an added quote report at `radar-redesign/out/connect-customer-data-lake-20260731/s3-connect-data-lake-quote.md`; it correctly says no price can be estimated until a candidate-specific registered recipe and rate card are added.

## 2026-07-31 Human-Facing Report Language Rule

- Human-facing Skill reports, quote reports, Markdown output, and GUI display labels must show statuses in Traditional Chinese instead of raw machine codes such as `interim`, `needs_registered_cost_model`, `region_unknown`, `unknown`, or `not_available`.
- Machine-readable JSON status fields may remain stable English codes for tests and workflow logic, but every user-visible report layer should include or render a Chinese label.

## 2026-07-31 Reusable Skill 3 Cost Estimation Decision

- Skill 3 cost estimation is no longer a per-news special case. It uses a reusable pre-deployment / shift-left FinOps estimator with three levels: Level A registered recipe, Level B generic usage model from detected AWS services or IaC resource types, and Level C incomplete when service/resource scope is still too vague.
- Level B may produce an estimated quote, recommended approval ceiling, formulas, assumptions, and official pricing sources even when no candidate-specific cost recipe exists. This resolves the old `needs_registered_cost_model` blocker for candidates that have enough billable service evidence.
- Cost estimation and deployable Skill 4 recipe registration are separate gates. A Level B quote can support review, but real AWS resource creation still requires a matching Skill 4 deployable recipe; otherwise the deployment context must stop with `needs_poc_recipe`.
- The Amazon Connect Customer Data Lake run `direct-url-20260731-766826d4` now uses the generic estimator instead of a hand-written special case: detected services include CloudFormation, IAM, Lake Formation, Lambda, RAM, and S3; expected estimate is USD 0.003246 with a USD 0.05 approval ceiling. Skill 4 remains approval-gated and creates no resources automatically.

## 2026-07-31 Skill 4 Pre-Cleanup Usage Snapshot Decision

- Skill 4 cleanup must record `pre_cleanup_usage_snapshot` before deleting AWS resources. The CLI can also write the same artifact as `pre_cleanup_usage_snapshot.json` through `--usage-snapshot-output`.
- The snapshot is immediate runtime evidence only: deployment/capture timestamps, elapsed seconds, CloudFormation resource inventory, S3 object/version counts and bytes, Lambda configuration and CloudWatch metrics when available, and recipe-specific facts such as EC2 state.
- The snapshot is not an AWS bill. Skill 5 may use it to explain what ran before cleanup, but it must not convert runtime facts into actual cost.
- Cleanup should not be delayed while waiting for billing data; current Skill 5 does not perform Billing / Cost Explorer / CUR reconciliation.

## 2026-08-03 Merged PoC Decision Gate and S1 Explanation Layer

- New Skill 3 behavior supersedes the older mandatory shortlist gate: Skill 3 evaluates and quotes every S2 candidate, then emits one `poc_decision_gate` where the human chooses `selected_candidate_id`, `approved_by`, and `approved_ceiling_usd`. `--shortlist` remains only as an optional candidate filter, not as the approval gate.
- New Skill 5 behavior supersedes the 2026-07-30 estimated-vs-actual-cost plan: S5 no longer accepts a `--billing` artifact and does not reconcile pre-deployment estimates against AWS Billing / Cost Explorer / CUR. Reports must state that the quote is a public-rate-card pre-deployment estimate and is not verified against AWS billing.
- Skill 4 still records `pre_cleanup_usage_snapshot` before cleanup, but this is runtime evidence only and must not be converted into actual cost.
- Skill 1 now includes a deterministic explanation layer with `key_points`, `significance`, `implementation_architecture`, and `possible_application_contexts`. Only `source_verbatim` and `derived_summary` support verified facts; `inferred_architecture` and `hypothesis` stay in derived sections.
- Skill 3 PoC decision reports must begin by explaining what the article is about in human-readable Chinese: before/after/difference, source-backed key points, and inferred minimal architecture. Only after that should they show PoC threshold, score, cost quote, deployable recipe, blockers, review notes, and Cleo's approval choices.
- Skill 3 PoC decision reports must also render a human-facing PoC minimum architecture diagram before the score/cost decision. When a registered Skill 4 recipe exists, use a recipe-specific diagram that shows the resources Skill 4 will actually create or validate, such as S3 Files VPC/EC2/mount target/filesystem/S3 bucket or Lambda self-managed S3 code bucket/Lambda/IAM/CloudWatch. If no recipe exists, fall back to the S1 inferred architecture and clearly label it as a draft, not a production architecture.
- For human-facing Skill 3 reports, Cleo wants HTML as the primary review artifact, not Markdown. In Agent mode, Codex may use the built-in image generation tool to create a GPT-style raster architecture infographic similar to AWS solution diagrams before S4 approval; embed that PNG directly in the HTML report as a data URI, not merely as a link, and do not include the old Mermaid/text flowchart in the human-facing report. Markdown may remain only as an internal fallback. Generated diagrams require human QA for text accuracy and must not be treated as evidence of deployed resources.

## 2026-08-03 Mentor S5 Report Presentation Rule

- Human-facing Skill 5 reports must replace the old one-sentence conclusion with `新聞摘要：應用面優勢`, focused on what the new feature enables in real application scenarios and what advantages it claims or suggests.
- Human-facing and machine-readable Skill artifacts must not use a separate certainty score as a decision indicator. PoC eligibility is decided by score threshold, blockers, quote readiness, deployable recipe, and named human approval.
- S1-S5 evidence must be visible step by step: S1 source fetch, S2 comparison/linked evidence, S3 score and quote, S4 validation/runtime/cleanup, and S5 report status.
- Verified facts belong under the technical validation status, not as a vague standalone `已證實事實` section.
- The old human-facing `後續提醒` section is removed. S5 reports must include `Future work`, reviewer-style questions, and human-useful related reading keywords.
- The report should ask what else is worth doing for this news item in the PoC, and what a reviewer would challenge or ask Cleo to explain further.
- The evidence source table must not include a pending PoC billing row as if it were evidence. Current Skill 5 does not render an actual-cost reconciliation table; it only states that pre-deployment estimates are not verified against AWS billing.
- PoC quotation presentation must put expected scenario assumptions before line-item details, identify the resources a human must confirm, and call out the most expensive expected line item plus the usage condition that would increase it.
- PoC quotes usually rely on monthly or usage-based public price units; reports must state the conversion basis. Lambda must be described as charged only when invoked, based on request count and duration/GB-second, not as an always-on resource.
- Remove the human-facing `報價假設與限制` heading. Keep necessary cost nature and evidence boundaries in clearer quote/cost status language.
- Lifecycle language must make timing clear: S1-S3 are the human decision zone; S4 validates the selected PoC; S5 reports the evidence and should preserve cleanup evidence. Resource cleanup or completion marking must not erase evidence needed for S5 review.
- The remaining two weeks should prioritize convergence: polish final proposal/paper material, keep Future work explicit, and avoid expanding into new large features unless they directly support the final report story.

## 2026-08-03 Cross-Computer Migration Decision

- GitHub `main` is the source of truth for continuing work on another computer; read `MIGRATION_STATUS.md`, `PROJECT_MEMORY.md`, and the latest daily log after cloning.
- The active implementation is `radar-redesign/`; old company-account / `cathay-techintel-v3` local implementation copies are not part of the deployable current version and may be deleted after curated evidence is committed.
- Raw `radar-redesign/out/`, Console screenshots, unredacted Console URLs, CDK `cdk.out/`, zips, dependency folders, local browser/session data, `.env`, AWS profiles, and `.local/` runtime folders must not be required for migration and should not be pushed.
- For cross-computer evidence continuity, use redacted curated artifacts under `radar-redesign/reference-runs/` instead of raw runtime dumps.

## 2026-08-03 Skill 4 Resource Inventory Gate Decision

- Skill 4 的主要 close gate 從「Console 截圖 metadata」改為「可驗證資源盤點」。Console / Infrastructure Composer 截圖仍可用來讓 Cleo 人工確認畫面，但程式只驗證截圖的保存與分享 metadata，不宣稱自己已自動判讀圖片內容。
- `s4_inventory` 應以 CloudFormation stack resources、resource identifiers、tags、quote expected resources、permission surface 與 stage timing 產出 structured inventory，讓 Skill 5 能說明實際建立了什麼、哪些資源符合報價預期、哪些權限面需要 reviewer 注意。
- `s4-close` 可接受 `s4.resource-inventory.v1` 作為人工確認 evidence；Skill 5 final 應稱為「資源盤點人工確認」，不得在沒有截圖時寫成 Infrastructure Composer 截圖確認。
- S4 PoC 的價值定位是部署可行性、帳號/Region 相容性、IAM/resource wiring、runtime verification、pre-cleanup usage snapshot 與 cleanup 可重現性；不是用短期 runtime facts 偽裝成 AWS 帳單或正式採購報價。
- Skill 5 final 可以接受具 `cleanup_verified` 與 structured resource inventory 的新版 runtime；若處理舊 runtime 沒有 inventory，必須在限制中說明證據較舊、圖片內容仍是人工確認，不應混成新版完整證據鏈。

## 2026-08-03 Daily Log Writing Rule

- Formal daily logs should emphasize the day's structural project changes, design decisions, workflow corrections, validation evidence, and remaining risks. Do not let the last PoC run of the day dominate the narrative when larger S1-S5 architecture or process changes happened earlier.
- When reporting Git activity, distinguish whole-repository statistics from engineering-core statistics that exclude large reference artifacts, binary deletions, or generated evidence. Do not present one as the other.
- Formal logs and supervisor-facing entry pages should avoid file names, internal status codes, command flags, commit hashes, and abstract English machine terms unless they are truly necessary evidence. Prefer clear Traditional Chinese descriptions such as「人工核准區」、「資源盤點」、「結案報告」、「清除回查」and explain technical details in human terms.

## 2026-08-04 AI Execution Trace Continuity Rule

- 從 2026-08-04 起恢復 AI 每小時執行軌跡；過去 2026-07-27 至 2026-08-03 缺少每小時紀錄的部分不追補成假即時紀錄。
- Cleo 可能因 token 或工具限制在 Codex 與 Claude 之間切換；每次交接都要把目前目標、已完成事項、下一步、驗證證據與限制寫清楚，讓另一個 AI 能從 GitHub、PROJECT_MEMORY、AI_PM_INBOX、最新日誌與 AI 執行軌跡接續。
- 跨 AI 交接時不得只依賴對話記憶；GitHub main 與專案內文字紀錄是可接續的主要來源。
- 五個 Skill 每次執行結束都必須跑收尾 checklist：更新日誌或 inbox、必要時更新 README / migration、執行或說明驗證、檢查 git status、完成有意義的 commit、需要共享時 push、確認 GitHub 可見、留下下一步。Cleo 不應每次手動追問這些基本收尾。
- 每次進入 Skill 4 前，Skill 3 報告必須回答「這次 PoC 要證明什麼？如果成功，決策者會多知道什麼？」；答案必須是具體可測的證據，例如部署可行性、Region/帳號相容性、資源關係、權限邊界、runtime 行為、cleanup 可重現性或仍未知的限制。若回答不出來，即使分數高也不應進入 Skill 4。
## 2026-08-04 WorkSpaces AI Agents Evaluation State

- Cleo selected the AWS article `Amazon WorkSpaces Now Lets AI Agents Operate Desktop Applications` for a single-item Skill 1-3 run.
- Run ID is `direct-url-20260804-20fd4c4b`; candidate ID is `S1-791440D21925`.
- Skill 3 score is `4.6 / 5`, with expected generic PoC estimate USD `0.000543`, high scenario USD `0.005537`, and suggested approval ceiling USD `0.05`.
- Do not proceed to Skill 4 yet: the current quote uses `generic_usage_model`, `deployable_recipe_registered=false`, and `ap-southeast-1` feature support is not programmatically confirmed.
- Before any live WorkSpaces PoC, create a WorkSpaces-specific Skill 4 recipe, cost model, success criteria, cleanup scope, and region/environment confirmation.

## 2026-08-04 Cross-Computer Continuity

- Cleo may work from another computer on Thursday and Friday. GitHub `origin/main` is the handoff source of truth for code, Skill documents, project memory, daily-log evidence, AI execution traces, and curated docs.
- Raw local run artifacts under `radar-redesign/out/`, downloaded Claude zip files, extracted `_tmp_review_files*` folders, browser sessions, AWS Console login state, and local credentials are not expected to travel through GitHub.
- A new Codex instance on another computer should start by cloning/pulling the repository, reading `AGENTS.md`, `PROJECT_MEMORY.md`, `MIGRATION_STATUS.md`, `AI_PM_INBOX.md`, the latest `logs/daily/work-log-YYYY-MM-DD.md`, and `ai-execution-trace/daily/2026-08-04.md`.
- If a local HTML/PNG decision report is needed on the other computer, regenerate it from the committed code and the relevant URL or use the curated docs summary instead of expecting ignored `out/` artifacts to exist.

## 2026-08-04 Skill 4 Recipe Registry Gate

- Skill 4 now treats deployable recipes as a registered contract, not as ad hoc logic inferred from a headline. A candidate may be valuable and quoted in Skill 3, but Skill 4 must refuse live deployment unless a deployable recipe declares resources, cost coverage, success criteria, cleanup scope, evidence plan, and region/environment handling.
- Historical state on 2026-08-04: the WorkSpaces AI Agents article was blocked before live Skill 4 because it only matched a draft WorkSpaces recipe. This was superseded by the 2026-08-05 WorkSpaces recipe completion note below.
- Skill 3 human-facing approval should use the canonical field `approved_cost_ceiling_usd`. Older `approved_ceiling_usd` artifacts may be read for compatibility, but new reports and templates should not write that old field.
- S1-S5 pipeline timing should be carried across stage artifacts and rendered in Skill 5, separating program execution time from human waiting time.

## 2026-08-05 WorkSpaces AI Agents Skill 4 Recipe Completion

- The WorkSpaces AI Agents article is no longer blocked by a draft-only recipe: `workspaces_ai_agent_access_cdk` is now a deployable Skill 4 recipe with explicit resources, success criteria, cleanup scope, evidence plan, and registered cost model.
- Correction after Cleo's cost review: the current Skill 4 recipe is phase-1 infrastructure validation only. It may create the fleet/stack, verify AgentAccessConfig, and generate a short-lived streaming URL, but it must not open the URL or connect an AI agent session.
- The phase-1 WorkSpaces PoC cost model is Level A registered: low USD 0.05, expected USD 0.10, high USD 0.40, recommended approval ceiling USD 0.50.
- A full desktop agent session is phase 2 and needs separate approval. Once a Windows streaming user launches a session, the Windows RDS SAL user fee is monthly and cleanup cannot refund it. One-user full-session estimates are tracked separately at about USD 6.47 / 6.5325 / 6.87, and a second unique user can add another monthly user fee.
- The recipe validates the WorkSpaces Applications / AppStream agent-access entry point: CloudFormation stack creation, fleet running state, stack AgentAccessConfig, and redacted streaming URL generation. It does not prove a full LLM-driven desktop business workflow.
- Do not run live Skill 4 for WorkSpaces without Cleo's explicit approval, because it creates AppStream / WorkSpaces Applications resources and may incur cost. The completed code has only been validated by tests and CDK synth so far.

## 2026-08-05 Skill 3 Scoring Correction

- Skill 3 scoring must score the technology and PoC nature, not S1/S2 evidence completeness. Evidence coverage can create blockers or review notes, but must not add score points.
- The Skill 3 rubric now has five dimensions: technical value, verifiability, adoption prerequisites, controllability/stop conditions, and reversibility/cleanup.
- Human-facing Skill 3 reports must show score breakdown lines for every dimension: score, weight, weighted points, and the concrete reason.
- WorkSpaces AI Agents is the reference correction case: score 2.65 / 5 with technical value 4, verifiability 3, adoption prerequisites 2, controllability 2, reversibility 1. It is not recommended for Skill 4 under the current scope, despite having a deployable recipe.
- Do not restore a visible confidence score in reports. If evidence coverage is too weak, use review notes or blockers instead of letting coverage inflate the technical score.

## 2026-08-10 Official News With Insufficient Implementation Detail Case

- Cleo requested a new blocked case showing that an AWS official news article can still be stopped when it mostly contains product messaging, benefits, and outcome claims rather than concrete implementation instructions.
- The selected case is AWS News Blog `Announcing Amazon Quick Suite: your agentic teammate for answering questions and taking action`, run ID `direct-url-20260810-1aec8013`, with artifacts under `radar-redesign/out/quick-suite-ad-claim-20260810/`.
- Skill 3 result: score `3.7 / 5`, `recommend_poc=false`, blockers `implementation_detail_insufficient` and `no_deployable_recipe`; Skill 4 gate result `no_poc_candidates`, `cloud_resources_created=false`.
- The code now exposes true `poc_blockers` in the Skill 3 decision gate summary instead of only governance flags, and adds a generic `implementation_detail_insufficient` blocker when source architecture remains inferred/drafted and no deployable recipe exists.
- This case is intended for the 2026-08-14 presentation as a distinct stop example from WorkSpaces: WorkSpaces demonstrates cost/compliance/decision-increment risk, while Quick Suite demonstrates that official promotional claims are not enough for Skill 4 PoC.
- Correction after Cleo's reminder: the Quick Suite Skill 3 report must follow the redesigned HTML-first human report format, not the old plain Markdown-to-HTML output. For blocked / ad-claim cases, the architecture section should show a clear blocked architecture card instead of a "please generate image" placeholder, render tables as real HTML tables, and display blockers/review notes in Chinese rather than raw machine codes.
- Stronger report-language rule after Cleo's correction: supervisor-facing Skill 3 reports must read like a human technical decision report in Traditional Chinese. They should start with a supervisor summary, explain what the article says, why a PoC would or would not be valuable, what minimum architecture is or is not available, then show the score and gate result. Do not expose mojibake, raw blocker codes, raw status codes, or JSON-shaped field names in the human-facing HTML/Markdown report.
- 2026-08-13 correction after Cleo's review: Quick Suite verifiability was previously too high at `4 / 5` because the generic validation design was treated as if it were source-backed. The corrected rerun under `radar-redesign/out/quick-suite-rerun-20260813-verifiability/` scores Quick Suite `3.1 / 5`, with verifiability `1 / 5`, blockers `implementation_detail_insufficient`, `veto_verifiability`, and `no_deployable_recipe`. For official product/news articles that lack implementation details, resource list, IAM/data flow, success criteria, or cleanup scope, the validation design must not raise verifiability above low score merely because AI can imagine a before/after test.

## 2026-08-12 Final Proposal Skill Visual Style Rule

- Cleo rejected overly simple five-Skill icon cards for the 2026-08-14 final proposal. Skill visuals should look like the clearer Skill 3 report diagrams: detailed Traditional Chinese process / decision diagrams showing purpose, input, AI processing, human gate, evidence artifacts, go / stop judgment, and stage-specific value.
- For supervisor-facing visuals, especially Skill 4, budget expectation and explicit human approval must appear before PoC deployment. Do not draw or describe the expected budget as something discovered only after PoC completion.
- If the five Skills are explained as text, prefer five focused Markdown files over one generic table. Each file should be concise but specific and should use concrete mechanics, examples, formulas, scoring dimensions, or case evidence instead of generic descriptions. Do not include separate "delivery artifact", "GitHub location", or "20-second script" sections in the final-proposal Skill Markdown; those are too much slide clutter unless Cleo explicitly asks for handoff material.
- After Cleo's 2026-08-12 critique, Skill explanations should prove precision through concrete display examples: actual report table shape, Lambda or S3 Files case evidence, official pricing/formula basis, scoring or gate criteria, resource inventory numbers, and "hard-doing PoC" definitions. Avoid padding with broad claims; supervisor-facing text should be concise, Traditional Chinese, and directly explain how a human would judge the evidence.

## 2026-08-12 Skill 5 Future Work Quality Rule

- Cleo rejected generic Skill 5 `Future work` and related-reading output as not useful to real users. Skill 5 must make future work case-specific and decision-oriented: what to search externally, why that source would matter, what evidence would count, and how it would change the next PoC or stop decision.
- Related reading must be phrased as external research directions or exact search queries, not loose keywords such as `Future work`, `CloudFormation`, or `PoC cleanup` unless tied to the candidate's concrete architecture, cost, permission, failure-mode, or cleanup question.
- S5 must preserve evidence boundaries: generated external-search directions are recommendations for the next research step, not claims that the external content has already been verified. Any actual searched evidence must be fed back into S1/S2/S3 artifacts before being treated as report evidence.

## 2026-08-12 Skill 5 Human Report Readability Rule

- Cleo rejected Skill 5 reports that read like long status ledgers. Supervisor-facing S5 Markdown must begin with human conclusions: what the PoC discovered, whether this AWS account / target Region / tested permission path worked, what was actually completed, why it matters, what cannot be claimed, and what decision evidence should be added next.
- Do not expose internal file names, raw artifact wording, run IDs, quote IDs, raw status codes, internal recipe identifiers, or English-only success criteria in supervisor-facing S5 Markdown. Keep those details in JSON/GUI audit data.
- Human-facing S5 cost content should summarize expected estimate, approval ceiling, public-price nature, not-AWS-billing limitation, and cleanup status. Long line-item tables belong only in JSON/GUI or an explicitly requested appendix.

## 2026-08-13 Prophet Role Positioning

- Correction from Cleo: `預言者` means the full five-Skill workflow, not only the first discovery role. Skill 1-5 together form the prophet process: scan signals, compare candidates, evaluate one selected candidate, validate through controlled PoC when allowed, and report the evidence-backed conclusion.
- The "first step" of the prophet process is signal discovery / radar input, but the prophet role itself includes the complete S1-S5 evidence chain. Do not describe the prophet as merely a handoff before evaluation or validation.
- Future proposal and Skill 5 next-step language may still mention other downstream roles, but only after clearly stating that `預言者雷達` already covers the five-Skill discovery-to-reporting flow. Downstream roles should be framed as what happens after this evidence package is produced, such as product owner, governance reviewer, production architect, or implementation team.

## 2026-08-13 Career Positioning Preference

- Cleo explicitly stated that she does not feel suited to PM. Future career-positioning advice should not frame pure PM as the primary fit.
- When analyzing career direction from work records, prioritize technical/architecture/research-validation roles such as cloud solution architect, AI/cloud engineer, platform/DevOps engineer, solution engineer, technical consultant, or technology researcher. AI PM may still describe the collaboration workflow, but not Cleo's main career identity unless she reopens that direction.
- Cleo is a communications engineering student about to enter junior year. Career advice should treat her as still exploring, with room to build fundamentals and sample multiple technical directions before locking into a title.
- When Cleo asks for career or competency analysis, do not over-limit the answer to specific job titles. Start from higher-level transferable competencies, role archetypes, decision style, and growth trajectory, then map to possible roles only as examples.

## 2026-08-13 Skill 5 Related Articles and Application Examples Rule

- Cleo clarified that Skill 5 must produce `相關文章與應用實例`, not only future-work search directions. The report must include related articles / source targets and concrete application examples tied to the candidate technology.
- At minimum, S5 should separate already-known source articles from still-needed external searches, then explain why each article matters, which downstream role would use it, and which PoC / stop / adoption decision it could change.
- Application examples should be concrete use cases, not generic possibilities. Each example should say how the technology would be used, what next test or decision it implies, and whether the next owner is verifier, architect, governance reviewer, product owner, or implementation team.

## 2026-08-13 Skill 3 Deployment Decision Pause Rule

- Correction after Cleo's process review: even if Cleo asks to run the full Skill 1-5 prophet flow, Codex must pause after Skill 3 before any Skill 4 live AWS deployment.
- Before deployment, Codex must show the Skill 3 human decision report, including the flow / architecture diagram if available, score, PoC proof question, expected/high cost estimate, recommended approval ceiling, planned recipe/resources, success criteria, limits, and cleanup scope.
- Only after Cleo explicitly confirms deployment approval for Skill 4 may Codex create AWS resources. Do not treat "run the full flow" or "run S1-S5" as implicit approval to skip the Skill 3 decision gate.

## 2026-08-13 Controllability Rubric Clarification

- Cleo clarified that `可控制性與停止機制` should primarily mean whether AI / the workflow can recognize that a PoC is going wrong, admit the prior judgment is unsupported or mistaken, pause further action, and wait for human decision.
- This is distinct from `可逆性與終止`: controllability is about stopping or pausing while the action is unfolding; reversibility is about whether resources, costs, and evidence can be cleaned up or recovered after stopping.
- Do not let non-refundable cost or cleanup details dominate controllability scoring; those belong mainly to reversibility. Controllability scoring should emphasize blocker recognition, abort / awaiting-human gates, and whether unknowns are treated as reasons to pause instead of reasons to continue.

## 2026-08-13 Skill 3 Rubric Summary Display Rule

- Cleo prefers the current Skill 3 scoring-criteria document format; do not replace it with a different Skill 3 report-style layout unless explicitly requested.
- The rubric summary must still show the current weights and explain that Skill 3 report weighted points are calculated as `dimension score × dimension weight`, with total score equal to the weighted-point sum out of 5.
- If `SMI` appears in human-facing rubric documentation, explain that it is a Service Measurement Index reference label only. It does not add points and is not a separate decision gate.

## 2026-08-13 Four Case Current Skill 3 Scores

- Cleo requested a detailed re-evaluation of the four final-proposal cases using the current 2026-08-13 Skill 3 rubric and weights.
- Current detailed score reference: `final-proposal/四案例新版Skill3細節評分-20260813.md`.
- Recomputed results: Lambda self-managed code storage `4.35 / 5` success; S3 Files `4.15 / 5` success; WorkSpaces AI Agents `2.60 / 5` stop; Amazon Quick Suite `3.10 / 5` stop.
- The two stop cases are intentionally different: WorkSpaces stops mainly on reversibility / licensing / compliance and incomplete decision evidence; Quick Suite stops mainly on verifiability because the official article lacks implementation details and no deployable recipe exists.
## 2026-08-13 Daily Log README Sync Rule（2026-08-18 起部分取代）

- After a formal daily log is completed, always update the root `README.md` in the same task so the project homepage reflects the newest daily outcome, current status, and any important pending boundary. For logs after 2026-08-18, do not update Skill scores or cumulative total unless Cleo explicitly requests a historical scoring correction.
- Treat the README update as part of the daily-log completion checklist, not as an optional follow-up.

## 2026-08-14 Skill 1 Evidence Boundary Clarification

- Skill 1 must be explained as a two-layer evidence split, not a generic summary step.
- `可採信證據` means what the original source actually says: supported services, functions, availability, setup method, limits, pricing/region links, official URLs, or other source-backed statements.
- `待驗證推論` means what AI derives from the source: possible architecture, possible PoC shape, application context, business use case, proof question, or follow-up research question.
- Skill 2, Skill 3, and Skill 4 depend on this boundary. Do not let official promotional claims, AI-inferred architecture, and verifiable source facts collapse into the same evidence layer.
- A source can be official and still insufficient for PoC. If implementation details, resource list, IAM/data flow, success criteria, cleanup scope, or registered recipe are missing, AI-generated validation design remains a draft and must not raise verifiability or authorize Skill 4.

## 2026-08-14 CIP Biweekly Word Format

- When Cleo asks for the CIP biweekly work journal as a Word file, use the prior DOCX format as the source style: A4 portrait, one-page compact table, basic-info table, three-column progress table, feedback row, and signature line.
- Keep the Word version concise and outcome-based. Do not paste the full long Markdown biweekly report into the form; compress it into 2-3 bullets per work item and a short reflection/next-priority note.
- 2026-08-14 status: the 2026-08-03 to 2026-08-14 CIP biweekly Word file was completed and Cleo reported it has been submitted. Do not treat this biweekly journal as pending.

## 2026-08-14 Lambda And S3 Files Cleanup State

- Cleo approved cleanup for both the 2026-08-14 Lambda Skill 4 deployment and the 2026-08-13 S3 Files rerun deployment.
- Both runs were cleaned through `s4-abort --execute` cost-control cleanup because normal Infrastructure Composer screenshot-backed Console review evidence was not completed.
- Lambda stack `AgenticRadarS4BD3AD967` and S3 Files stack `AgenticRadarS4A9C9B006` no longer exist in CloudFormation in `ap-southeast-1`; run-prefix S3 bucket and IAM role lookups returned no residual resources.
- Treat both post-cleanup Skill 5 reports as `closed_without_console_review`, not normal actual-PoC final reports. Future final-success runs must complete screenshot-backed Console review before `s4-close --execute`.
