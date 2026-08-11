# 五個 Skill：Codex 怎麼找到、GitHub 要放哪裡

## Codex 通常怎麼找本機以外的 Skill

1. 先看目前工作階段注入的 Skill 清單，確認有哪些 Skill 已經可用。
2. 如果使用者提到外部工具、plugin 或不在清單內的 Skill，使用 `tool_search` 找延遲載入的工具或 plugin。
3. 找到 Skill 後，一定先讀完整 `SKILL.md`，再照裡面的 CLI、輸入輸出與 guardrail 執行。
4. 如果 Skill 來自 GitHub，要在 repo 裡清楚寫出 Skill package 的相對路徑，並保留 agent 設定檔，接手的人才知道要呼叫哪一個 Skill。

## 這個專案的放置規則

每個 Skill 都是一個 GitHub 可追蹤的 package：

- 主規格：`radar-redesign/skills/<skill-name>/SKILL.md`
- Agent 入口：`radar-redesign/skills/<skill-name>/agents/openai.yaml`
- 共用核心：`radar-redesign/agentic_cloud_radar/`
- 重要原則：Skill 文件只描述流程與 guardrail，真正邏輯重用專案核心，不把程式複製進每個 Skill。

## 五個 Skill 摘要

| Skill | GitHub 檔名 | Agent 入口檔 | 兩句話摘要 |
|---|---|---|---|
| Skill 1 Scan | `radar-redesign/skills/scan-cloud-technologies/SKILL.md` | `radar-redesign/skills/scan-cloud-technologies/agents/openai.yaml` | 讀取可信的公開雲端來源，整理成可追溯的候選技術 artifact。重點是保留來源、成熟度、服務線索與缺口，不排名、不判斷是否 PoC。 |
| Skill 2 Compare | `radar-redesign/skills/compare-cloud-candidates/SKILL.md` | `radar-redesign/skills/compare-cloud-candidates/agents/openai.yaml` | 把 Skill 1 候選轉成同一格式的提案卡與比較矩陣。重點是找官方文件、Region、價格與限制證據，但不替人選冠軍。 |
| Skill 3 Evaluate | `radar-redesign/skills/evaluate-cloud-candidate/SKILL.md` | `radar-redesign/skills/evaluate-cloud-candidate/agents/openai.yaml` | 對人類選定的單一候選做評分、風險、報價與 PoC proof question。重點是進 Skill 4 前先判斷值不值得、花多少、能不能驗證，以及是否會硬做。 |
| Skill 4 Validate | `radar-redesign/skills/validate-cloud-poc/SKILL.md` | `radar-redesign/skills/validate-cloud-poc/agents/openai.yaml` | 在具名核准與成本上限後，才建立受控 AWS PoC、驗證 runtime、盤點資源並 cleanup。重點是只用已登錄 recipe，不臨場硬補架構，不跨 run 清資源。 |
| Skill 5 Report | `radar-redesign/skills/report-cloud-evidence/SKILL.md` | `radar-redesign/skills/report-cloud-evidence/agents/openai.yaml` | 把 Skill 1 到 Skill 4 的 artifact 組成可審查報告。重點是只報告已記錄證據、部署前估價、runtime evidence、資源盤點與未知限制，不重新推論或做帳單對帳。 |

## 講稿

> 我的交付物不是只有聊天紀錄，而是五個放在 GitHub 的可重用 Skill。Codex 找 Skill 時不是憑記憶亂猜，它會先看可用 Skill 清單；如果不在本機，就透過工具搜尋 plugin 或外部來源。真正執行時，每個 Skill 都要先讀自己的 `SKILL.md`，再照 `agents/openai.yaml` 提供的入口提示呼叫，所以 GitHub 上一定要寫清楚檔案位置。
