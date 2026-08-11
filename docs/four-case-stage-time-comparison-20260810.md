# 四個案例 Skill 階段純執行時間統計

日期：2026-08-10

目的：整理目前四個案例中，AI / 自動化流程「自己跑到認為完成」所花的時間，用來和 Cleo 手動完成同樣工作的時間比較。

## 統計口徑修正

- 這版只看 AI / 系統純執行時間，排除人工關卡等待。
- 不含 Cleo 核准時間、不含 Cleo 看 Console 的時間、不含等待人工回覆的時間。
- 成功案例統計到 Skill 5 final：Lambda self-managed S3 code storage、S3 Files。
- 失敗案例統計到 Skill 3 完成：WorkSpaces AI Agents、Amazon Quick Suite。
- 早期兩個成功案例還沒有完整 `stage_timings`，因此以下是由 artifact 時間點推估的「非人工執行片段」，不是秒級精準計時。
- Quick Suite 有完整 `stage_timings`，可分成「第一次純 pipeline」與「含後續報告中文化修正」兩種口徑。用來跟手動流程比，建議採第一次純 pipeline。

## 主表：不含人工關卡

| 案例 | 結果 | Skill 1 | Skill 2 | Skill 3 | Skill 4 | Skill 5 | AI 純執行時間 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Lambda self-managed S3 code storage | 成功，完成 Skill 5 final | 未精準記錄，推估很短 | 約 0.7 秒 | 約 1.4 秒 | 約 3 分 14 秒 | 約 23 秒 | 約 3 分 40 秒以上 |
| S3 Files | 成功，完成 Skill 5 final | 未精準記錄，推估很短 | 約 0.9 秒 | 約 3 分 55.6 秒 | 約 14 分 21 秒 | 約 2 分 54.9 秒 | 約 21 分 12 秒以上 |
| WorkSpaces AI Agents | 失敗，停在 Skill 3 | 未精準記錄，推估很短 | 約 1.0 秒 | 第一次 Skill 1-3 約 3 分 23 秒；修正版 Skill 3 約 2 小時 27 分 47.5 秒 | 不進入 | 不進入 | 簡報建議標「約 3 分 23 秒完成初評；後續修正版另計」 |
| Amazon Quick Suite | 失敗，停在 Skill 3 | 約 0.7 秒 | 約 4.1 秒 | 第一次約 0.045 秒；含報告中文化修正約 43 分 5.4 秒 | 不進入 | 不進入 | 約 4.8 秒完成第一次 Skill 1-3 判斷 |

## 為什麼和上一版差很多

上一版的「可比較總時間」其實混入了人工關卡與等待時間，例如：

- 等 Cleo 核准是否進 Skill 4。
- 等 Cleo 看 AWS Console / Infrastructure Composer。
- 等人工確認 cleanup。
- 後續修報告、改版、重跑輸出。

這些對專案管理有意義，但不是你現在要的「AI 自己跑多久」。這版改成純執行時間後，才適合拿來和你手動做同樣工作比較。

## 簡報建議說法

可以這樣講：

> 四個案例中，成功案例如果做到完整 PoC 與 Skill 5 final，AI 自動化流程的純執行時間約落在數分鐘到二十多分鐘；失敗案例則能在 Skill 3 就停止，Quick Suite 第一次純 pipeline 約 4.8 秒就判斷不應進入 Skill 4。人工關卡造成的等待時間另外計算，不能混在工具執行效率裡。

更保守一點可以說：

> 因早期成功案例尚未完整記錄每個 command 的 `started_at/ended_at`，成功案例時間採 artifact 推估；但可以確認主要耗時集中在 Skill 4 的 AWS 建立、盤點與 cleanup，而不是 Skill 1-3 的文件判讀。

## 手動時間比較欄位

| 案例 | AI 純執行時間 | Cleo 手動估計時間 | 節省時間 | 備註 |
| --- | ---: | ---: | ---: | --- |
| Lambda self-managed S3 code storage | 約 3 分 40 秒以上 | 待填 | 待填 | 成功，完整做到 Skill 5 final；早期計時為推估。 |
| S3 Files | 約 21 分 12 秒以上 | 待填 | 待填 | 成功，完整做到 Skill 5 final；早期計時為推估。 |
| WorkSpaces AI Agents | 初評約 3 分 23 秒；修正版另計 | 待填 | 待填 | 失敗案例，停在 Skill 3；跨日修正版不適合當純流程速度。 |
| Amazon Quick Suite | 約 4.8 秒 | 待填 | 待填 | 失敗案例，停在 Skill 3；含中文報告修正則約 43 分 10.2 秒。 |

## 來源 artifact

- Lambda：`radar-redesign/out/smoke-20260803-lambda-s3-decision-report/`
- S3 Files：`radar-redesign/out/s3-files-20260803-s1-s5/`
- WorkSpaces AI Agents：`radar-redesign/out/workspaces-ai-agents-20260804-s1-s3/`、`radar-redesign/out/workspaces-ai-agents-20260805-new-s3-report/`
- Amazon Quick Suite：`radar-redesign/out/quick-suite-ad-claim-20260810/`
