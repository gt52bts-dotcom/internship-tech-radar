# 技術雷達 Skill 積分紀錄

## Skill 定義

- `Skill 1 - Scan`：蒐集 AWS 新聞、官方文件、候選技術與問題線索。
- `Skill 2 - Compare`：比較候選技術、替代方案、限制、成本與適用情境。
- `Skill 3 - Evaluate`：用 rubric、風險、權限、安全、成本與可行性做決策。
- `Skill 4 - Validate`：以 CLI、CloudFormation、測試、PoC 或證據包驗證推論。
- `Skill 5 - Report`：產出可交付報告、dashboard、demo checklist、日誌與主管可讀材料。

## 評分標準

- 五個 Skill 的每日加總最高 10 分，不再用「每個 Skill 各自最高 10 分」累加。
- `1~3`：閱讀、整理、模板驗證、單點 CLI 查證或局部文件成果。
- `3~5`：本機 PoC、離線驗證、可追溯設計或小型可交付成果。
- `6~8`：公司帳戶或接近真實環境的端到端 PoC，但仍有 fallback、未回驗、未 cleanup 或品質限制。
- `9~10`：可重現、可展示、品質已回驗，且對核心目標有明確里程碑意義。若缺正式 API、cleanup、成本、安全或穩定性驗證，不可超過 10，也通常不給滿分。

## 每日分數

| 日期 | Scan | Compare | Evaluate | Validate | Report | 當日總分 | 目標對齊 |
|---|---:|---:|---:|---:|---:|---:|---|
| 2026-07-13 | 1 | 2 | 1 | 3 | 1 | 8 | direct |
| 2026-07-14 | 1 | 1 | 1 | 2 | 1 | 6 | supporting |
| 2026-07-15 | 1 | 1 | 1 | 1 | 1 | 5 | supporting |
| 2026-07-16 | 1 | 1 | 2 | 3 | 1 | 8 | direct |
| 2026-07-17 | 1 | 1 | 2 | 4 | 2 | 10 | direct |
| 2026-07-20 | 2 | 1 | 2 | 1 | 1 | 7 | direct |
| 2026-07-21 | 1 | 1 | 2 | 4 | 1 | 9 | direct |
| 2026-07-22 | 1 | 1 | 2 | 2 | 2 | 8 | direct |
| 2026-07-23 | 1 | 1 | 1 | 1 | 1 | 5 | direct |
| 2026-07-24 | 0 | 0 | 1 | 0 | 3 | 4 | direct |
| 2026-07-27 | 2 | 1 | 1 | 3 | 2 | 9 | direct |
| 2026-07-28 | 3 | 2 | 1 | 1 | 1 | 8 | direct |
| 2026-07-29 | 2 | 2 | 1 | 4 | 1 | 10 | direct |
| 2026-07-30 | 1 | 1 | 2 | 4 | 2 | 10 | direct |
| 2026-07-31 | 1 | 1 | 2 | 4 | 2 | 10 | direct |
| 2026-08-03 | 2 | 1 | 2 | 3 | 2 | 10 | direct |
| 2026-08-04 | 2 | 2 | 2 | 0 | 2 | 8 | direct |
| 2026-08-05 | 0 | 0 | 4 | 2 | 2 | 8 | direct |
| **2026-08-05 累積** | **23** | **20** | **30** | **42** | **28** | **143** |  |

## 2026-07-21 評分理由

- Scan +1：聚焦 S3 Files AWS News、官方文件、CLI schema 與使用條件；但只處理單一新聞與單一服務，不算廣泛掃描。
- Compare +1：比較 CLI direct resource 與 CloudFormation-managed resource、direct mount 與 access point mount；但未進一步比較多個替代服務。
- Evaluate +2：納入 IAM、POSIX 權限、成本、cleanup、去識別化證據與 exposed private key 風險；但缺完整成本估算與正式採用決策。
- Validate +4：手動 CLI PoC 與 CloudFormation-managed PoC 都完成實機雙向驗證；但未做效能、多節點、長時間穩定性與 cleanup 後回驗。
- Report +1：產出教學書、流程圖、證據摘錄、雷達式 PoC 報告與正式日誌；尚未濃縮成 final proposal 或主管版結論頁。

## 當前狀態

截至 2026-08-05，累積總分為 143。S1-S5 已整理為五個正式 Skill；WorkSpaces AI Agents 已改用通用五構面 rubric 重評為 2.35 / 5，因桌面畫面代理觀看的合規覆核、停止風險與可逆性不足而不建議進入 Skill 4。雖已補齊第一段基礎設施 recipe 與成本模型，但本日未建立 AWS 資源。

## 2026-07-24 評分理由

- Scan +0：今天沒有新增外部新聞、官方文件或帳號資源掃描。
- Compare +0：今天沒有新增替代技術或部署方案比較。
- Evaluate +1：初步釐清 S0／S1 責任邊界與 S4 PoC 人工核准、成本限制。
- Validate +0：依使用者更正，今天沒有完成可計分的 S0 測試、編譯檢查、S4 雙向資料驗證或 cleanup 回驗。
- Report +3：依 Mentor 回饋完成待辦／交付物管理校正，收斂最終發表驗證節奏，並整理 AI PM 科會 10 分鐘內容稿。

## 2026-07-22 評分理由

- Scan +1：盤點 S3 bucket、CloudTrail 與 S3 Files 相關資源，辨識哪些是專案資源、哪些是帳號治理資源；掃描範圍仍集中在 S3 Files cleanup 與帳號資源。
- Compare +1：比較手動 CLI、CDK deploy、CloudFormation deploy、Session Manager 與 SSH 的差異，並寫入教學書；尚未比較 S3 Files 與其他替代儲存服務。
- Evaluate +2：把成本、cleanup、CloudTrail 稽核、CDK bootstrap 權限限制、S3 prefix 路徑與日誌誠實度納入判斷；但新 stack 仍待 cleanup。
- Validate +2：完成舊 PoC cleanup 回驗，用 CLI 確認新 CloudFormation stack `CREATE_COMPLETE`，並由使用者截圖確認 Infrastructure Composer 資源關係；但尚未完成 EC2 mount 檢查與 S3 雙向同步驗證。
- Report +2：重寫日誌規則與歷史日誌，完成 CDK 部署教學書、CloudFormation 註解整理與 dashboard 同步；但 final proposal 仍待整理。

## 2026-07-23 評分理由

- Scan +1：指定 S3 Files 新聞以受控 `seed_article` 入口進入 S1，並保留與一般 RSS 路徑的差異。
- Compare +1：釐清手動指定新聞、RSS 掃描、LLM fallback 與 rubric fallback 的差異，避免把不同來源或不同驗證層級混在一起。
- Evaluate +1：確認 PoC gate 只能送人工審查，不能自動開始 PoC。
- Validate +1：指定新聞 execution 成功，且 layer 修正後確認 fallback 主因改為 API key 無效；不把外部 LLM 評分寫成成功。
- Report +1：AI PM 科會簡報開始改成以實際校正案例為主，但仍屬初步整理，不算完成版報告。

## 2026-07-27 評分理由

- Scan +2：S1 已對人工確認的 AWS 官方 URL 進行真實抓取，輸出可追溯的候選資料與來源狀態。
- Compare +1：明確拆分規則、官方 metadata 與 LLM hints，避免把輔助訊號與正式證據混用。
- Evaluate +1：保留 S0 human gate、URL 失敗回報與 LLM 不得直接作為證據的判斷邊界。
- Validate +3：S0、S1 的單元測試、編譯及 S0→S1 真實 URL 流程通過；尚未計入 AWS 部署或 S2-S5。
- Report +2：完成科會簡報重寫與 S1 學習文件，供 Mentor 與後續交接理解。

## 2026-07-28 評分理由

- Scan +3：完成直接 URL、RSS 與動態分類的 S1 真實資料入口，並保留 GA 證據篩選。
- Compare +2：S2 將 6 個候選轉成提案卡，並加入新加坡功能級可用性檢查。
- Evaluate +1：明確保留 S0 human gate、URL 失敗回報與 LLM 不得直接作為證據的判斷邊界。
- Validate +1：編譯通過，但正式重跑單元測試有失敗，僅計入問題發現與驗證邊界，未計入 AWS 資源驗證。
- Report +1：保留可追溯的規則與限制整理；尚未產出正式最終報告。

## 2026-07-30 評分理由

- Scan +1：以 AWS 官方 S3 Files URL 產出具 lineage 的候選 artifact。
- Compare +1：以官方文件確認使用條件、新加坡可用性與 pricing 來源。
- Evaluate +2：導入 s3.evaluation.v3，完成人工 shortlist 評估並串接可稽核 PoC quote。
- Validate +4：新 S3 Files stack 達 `CREATE_COMPLETE`，掛載、雙向資料、人工 Console review 與 cleanup 回查通過；另修正同步延遲的有限重試與同 stack 續驗。
- Report +2：產出包含完整報價、runtime、人工覆核與 cleanup 證據的 S5 final report，並保留實際帳務尚待核對的界線。

## 2026-07-31 評分理由

- Scan +1：以 AWS 官方 Amazon Connect Customer Data Lake 文章完成新的單一候選 Scan artifact；未進行廣泛新聞掃描。
- Compare +1：建立唯一候選比較卡與限制清單；未主張已完成多候選採用比較。
- Evaluate +2：完成單項固定 rubric、公開證據成本報價與缺少 recipe／rate card 的停止條件，並把預估成本與實際帳務成本明確分離。
- Validate +4：完成 S4/S5 approval、Console review、timeout abort 與 final 狀態規則硬化；另有 Lambda 與 S3 Files 的受控 live PoC、人工 Console 確認、cleanup 回查，以及 43 項主專案測試、編譯與腳本語法檢查證據。
- Report +2：完成 Mentor review package、可攜交接說明、成本對帳版報告與雙週工作進度，且保留 productionization、帳務與公司環境限制。

## 2026-08-03 評分理由

- Scan +2：新增 S1 新聞解釋能力，能從官方文章產出原文重點、前後差異、最小架構與應用情境，並用測試確認可追溯；同時以 AWS 官方 S3 Files 文章建立新的 S1 證據。
- Compare +1：整理 S3 Files 的 Region 證據、recipe、價格來源與部署前提，供單項 PoC 決策使用；未主張多候選採用排名。
- Evaluate +2：Skill 3 產出 4.4 / 5 評分、低／預期／高用量報價、USD 0.20 核准上限與內嵌架構圖 HTML 報告，讓人類在部署前判斷價值與成本。
- Validate +3：完成 Lambda 收尾與 S3 Files 實際 PoC；S3 Files 完成部署、掛載、雙向資料驗證、19 個資源盤點、報價對照與清除後回查。今日驗證成果很完整，但舊截圖輔助流程與 GUI 同步仍待整理，因此不再把所有新增分數集中到 Validate。
- Report +2：產出 Lambda 與 S3 Files 的 Skill 5 結案報告，更新 S4 資源盤點規則、S5 結案文案、專案記憶與正式日誌；仍清楚標示公開牌價估算不是 AWS 帳務成本。

## 2026-08-04 評分理由

- Scan +2：以 AWS 官方來源完成 8 個新功能候選雷達，並對 WorkSpaces AI Agents 建立可追溯的單篇 S1 artifact。
- Compare +2：完成雷達候選的 S2 比較，並保留 WorkSpaces 的專用 recipe 與區域證據限制，未把分析寫成可部署結論。
- Evaluate +2：將 PoC proof question 寫入 Skill 3／4 gate，並完成 WorkSpaces 初步部署前決策。其 Skill 3 分數、報價與 Skill 4 資格已在 2026-08-05 依新 rubric 校正；不把 8/4 的初步 4.6 / 5 或通用估價視為目前結論。
- Validate +0：今日未進入新的 Skill 4 部署或實機驗證，不以文件或分析取代驗證分數。
- Report +2：完成候選摘要、WorkSpaces GitHub 交接摘要、人類／AI 軌跡對比素材與跨 AI 接手規則。

## 2026-08-05 評分理由

- Scan +0：未新增正式的外部技術掃描，僅以既有 WorkSpaces 候選驗證評分修正。
- Compare +0：未產生新候選或排名比較；成本型態與可逆性比較只服務於既有候選的評估修正。
- Evaluate +4：完成可重複使用的五構面 rubric、CLI 匯出與 WorkSpaces 重評；將原本會被文件完整度高估的候選下修至 2.35 / 5，並以合規、停止與可逆性 blocker 作出不進 PoC 的決策。
- Validate +2：完成 WorkSpaces 第一段 recipe、成本模型、CDK synth 與 120 項針對性測試；未建立 AWS 資源，故不列為 live PoC 驗證。
- Report +2：完成評分準則文件、30 分鐘成果報告大綱、8/14 時程與 AI PM 簡報草稿狀態校正，保留可追溯的主管溝通素材。

## 2026-08-05 校正紀錄（不另計每日 Skill 分數）

- Skill 3 改為評估技術能力、可驗證性、導入前置條件、可控制性與停止機制、可逆性與終止；證據覆蓋率只形成 review note 或 blocker，不再提高分數。
- WorkSpaces AI Agents 最終為 2.65 / 5：技術能力 4、證據可驗證性 3、導入前置條件 2、可控制性與停止機制 2、可逆性與終止 1。
- 第一段基礎設施驗證報價為低／預期／高 USD 0.05／0.10／0.40，建議核准上限 USD 0.50；完整桌面 agent session 屬第二段，未納入同一筆核准。
- `recommend_poc=false`、`can_enter_skill4=false`，並新增 `compliance_review_required` blocker；沒有建立 AWS 資源。
- 已完成 Skill 3／Skill 4／recipe／costing 回歸測試 63 項。

## 2026-07-29 評分理由

- Scan +2：保留 AWS Blog 分類深挖，並以 Lambda 官方 URL 建立第二條可追溯候選 lineage。
- Compare +2：新增受控官方 Region 取證；缺證據改為 warning 與付費 PoC gate，避免把搜尋摘要或不相干頁面當證據。
- Evaluate +1：S3 以固定 rubric、人工 shortlist 和可選商業脈絡完成評估；未把缺少脈絡補造成事實。
- Validate +4：S3 Files 隔離 PoC 已完成部署、雙向驗證、Console 檢視及 cleanup 回查；Lambda PoC 已確認 CloudFormation、REFERENCE 設定與 invoke，但 Console review、實際成本與 cleanup 尚待完成，因此不給更高分。
- Report +1：S5 只能引用 artifact，產出 interim report 與可讀 GUI；未把待覆核的 Lambda PoC 寫成結案。
