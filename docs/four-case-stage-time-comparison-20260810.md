# 四個案例 Skill 階段純執行時間統計

日期：2026-08-10

目的：整理目前四個案例中，AI / 自動化流程「自己跑到認為完成」所花的時間，用來和 Cleo 手動完成同樣工作的時間比較。

## 統計口徑修正

- 這版只看 AI / 系統純執行時間，排除人工關卡等待。
- 不含 Cleo 核准時間、不含 Cleo 看 Console 的時間、不含等待人工回覆的時間。
- 成功案例統計到 Skill 5 final：Lambda self-managed S3 code storage、S3 Files。
- 失敗案例統計到 Skill 3 完成：WorkSpaces AI Agents、Amazon Quick Suite。
- 2026-08-11 已針對早期案例補跑 Skill 1，Skill 1 改採 `started_at/ended_at` 精準計時；其餘早期階段仍採 artifact 時間點推估的「非人工執行片段」。
- 2026-08-11 修正 S3 Files 口徑：原本約 21 分 14 秒的說法過寬，混入不該算入 PoC 本體的後段等待／整理口徑；本版拆成 PoC 部署驗證、資源盤點、cleanup 與 Skill 5 報告。
- Quick Suite 有完整 `stage_timings`，可分成「第一次純 pipeline」與「含後續報告中文化修正」兩種口徑。用來跟手動流程比，建議採第一次純 pipeline。

## 主表：不含人工關卡

| 案例 | 結果 | Skill 1 | Skill 2 | Skill 3 | Skill 4 | Skill 5 | AI 純執行時間 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Lambda self-managed S3 code storage | 成功，完成 Skill 5 final | 0.655 秒 | 約 0.7 秒 | 約 1.4 秒 | 約 3 分 14 秒 | 約 23 秒 | 約 3 分 40 秒 |
| S3 Files | 成功，完成 Skill 5 final | 1.118 秒 | 約 0.9 秒 | 約 3 分 55.6 秒 | 約 12 分 34 秒 | 約 2 分 14 秒 | 約 18 分 45 秒；PoC 部署驗證本體約 8 分 26 秒 |
| WorkSpaces AI Agents | 停止案例，停在 Skill 3 | 0.564 秒 | 約 1.0 秒 | 第一次約 3 分 22.1 秒；修正版 Skill 3 約 2 小時 27 分 47.5 秒 | 不進入 | 不進入 | 簡報建議標「初評約 3 分 24 秒；後續修正版是修正硬做傾向，不作速度比較」 |
| Amazon Quick Suite | 停止案例，停在 Skill 3 | 約 0.7 秒 | 約 4.1 秒 | 第一次約 0.045 秒；含報告中文化修正約 43 分 5.4 秒 | 不進入 | 不進入 | 約 4.8 秒完成第一次 Skill 1-3 判斷；中文化修正用來把停止理由寫成人看得懂 |

### S3 Files 時間拆解

S3 Files 的 21 分鐘說法不適合用來回答「PoC 跑多久」。依 `radar-redesign/out/s3-files-20260803-s1-s5/` artifact 時間點重拆後：

| 階段片段 | 時間 | 是否算 AI 純執行 |
| --- | ---: | --- |
| Skill 4 部署啟動到 runtime 驗證完成 | 約 8 分 26 秒 | 是，這是 PoC 部署驗證本體 |
| runtime 驗證完成到資源盤點完成 | 約 3 分 27 秒 | 是，屬於 Skill 4 證據整理 |
| 資源盤點完成到 pre-cleanup snapshot | 約 29 分 32 秒 | 否，這段主要是人工確認前等待 |
| cleanup artifact 寫入 | 約 41 秒 | 是，屬於 Skill 4 收尾 |
| Skill 5 final report 產出 | 約 2 分 14 秒 | 是 |

因此簡報若講 PoC 速度，應說「S3 Files 的 PoC 部署與自動驗證約 8 分 26 秒」；若講完整成功案例跑到 Skill 5，則說「排除人工等待後約 18 分 45 秒」。

## 停止案例的簡報口徑：什麼叫硬做

這兩個失敗案例不能只說「AI 很快擋下」，要說清楚它們曾經暴露出一個流程風險：AI 容易把不適合 PoC 的題目硬套成一個簡略版 demo。這次修正的價值，是把「不要硬做」變成明確規則。

**硬做的定義**：在 Skill 3 已經看出缺少部署前提、成本不可逆、缺少實作細節、缺少可部署 recipe，或 PoC 成功後也不會新增決策證據時，仍為了展示而臨時縮小範圍、編一個簡化架構、建立 AWS 資源，並把它包裝成 PoC 成功。

| 停止案例 | 一開始容易硬做的地方 | 為什麼不應硬做 | 修正後的說法 |
| --- | --- | --- | --- |
| WorkSpaces AI Agents | 把「AI agent 操作桌面」硬縮成只建立 WorkSpaces / AppStream 基礎入口，讓它看起來像已完成 PoC。 | 真正的桌面 agent session 會牽涉 Windows 使用者月費、合規審查、代理觀看或操作桌面等風險；cleanup 也不能退回已觸發的月費。簡略版只能證明入口存在，不能證明 AI 真的完成桌面工作流程。 | 停在 Skill 3，結論是目前不進 live Skill 4；下一步不是建立資源，而是先補清楚 recipe、成本、合規邊界與第二段核准。 |
| Amazon Quick Suite | 因為它是 AWS 官方新聞，就想用簡化架構把 agentic teammate 做成 demo。 | 文章主要是產品願景、效益宣稱與使用情境，沒有足夠的實作步驟、資源組合、API 或可驗證最小架構；硬做會變成 AI 自己補故事。 | 停在 Skill 3，結論是官方新聞不等於可 PoC；缺少實作細節與可部署 recipe 時，應先停止而不是建資源。 |

## 為什麼和上一版差很多

上一版的「可比較總時間」其實混入了人工關卡與等待時間，例如：

- 等 Cleo 核准是否進 Skill 4。
- 等 Cleo 看 AWS Console / Infrastructure Composer。
- 等人工確認 cleanup。
- 後續修報告、改版、重跑輸出。

這些對專案管理有意義，但不是你現在要的「AI 自己跑多久」。這版改成純執行時間後，才適合拿來和你手動做同樣工作比較。

## 簡報建議說法

可以這樣講：

> 四個案例中，成功案例如果做到完整 PoC 與 Skill 5 final，AI 自動化流程的純執行時間約落在數分鐘到二十分鐘內；S3 Files 的 PoC 部署與自動驗證本體約 8 分 26 秒，完整到 Skill 5 約 18 分 45 秒。停止案例的重點不是只看秒數，而是 Skill 3 能把「硬做 demo」擋下來：WorkSpaces 不能把高風險桌面代理硬縮成入口驗證，Quick Suite 也不能因為是官方新聞就用廣告詞硬編 PoC。人工關卡造成的等待時間另外計算，不能混在工具執行效率裡。

更保守一點可以說：

> 早期成功案例的 Skill 1 已補跑取得精準 `started_at/ended_at`；其餘早期階段仍採 artifact 推估。但可以確認主要耗時集中在 Skill 4 的 AWS 建立、盤點與 cleanup，而不是 Skill 1-3 的文件判讀。

## 手動時間比較欄位

| 案例 | AI 純執行時間 | Cleo 手動估計時間 | 節省時間 | 備註 |
| --- | ---: | ---: | ---: | --- |
| Lambda self-managed S3 code storage | 約 3 分 40 秒 | 待填 | 待填 | 成功，完整做到 Skill 5 final；Skill 1 已補跑精準計時，其餘早期階段為推估。 |
| S3 Files | 完整到 Skill 5 約 18 分 45 秒；PoC 部署驗證本體約 8 分 26 秒 | 待填 | 待填 | 成功，完整做到 Skill 5 final；Skill 1 已補跑精準計時，Skill 4 已拆除人工等待片段。 |
| WorkSpaces AI Agents | 初評約 3 分 24 秒；修正版另計 | 待填 | 待填 | 停止案例，停在 Skill 3；修正版重點是教流程不要把高風險桌面 agent 題目硬縮成入口 demo。 |
| Amazon Quick Suite | 約 4.8 秒 | 待填 | 待填 | 停止案例，停在 Skill 3；含中文報告修正則約 43 分 10.2 秒，重點是把「官方宣傳不足以 PoC」寫清楚。 |

## 來源 artifact

- Lambda：`radar-redesign/out/smoke-20260803-lambda-s3-decision-report/`
- S3 Files：`radar-redesign/out/s3-files-20260803-s1-s5/`
- WorkSpaces AI Agents：`radar-redesign/out/workspaces-ai-agents-20260804-s1-s3/`、`radar-redesign/out/workspaces-ai-agents-20260805-new-s3-report/`
- Amazon Quick Suite：`radar-redesign/out/quick-suite-ad-claim-20260810/`
- 2026-08-11 Skill 1 補跑精準計時：`radar-redesign/out/timing-rerun-skill1-20260811/`
