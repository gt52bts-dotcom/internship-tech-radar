---
name: report-cloud-evidence
description: 將 S1 到 S4 artifact、PoC 成本估算與 optional runtime evidence 轉成可追溯 JSON、主管可讀 Markdown 與 GUI report model，且不新增未被證據支持的宣稱。適用於 Skill 5 interim/final 技術報告、證據帳本、已驗證/未驗證摘要、artifact lineage 檢查，以及 presentation-ready report data。
---

# Skill 5 Report：證據結案與人類摘要

Skill 5 只整理已記錄的證據。它不抓新來源、不重新評分、不推論缺失事實，也不操作 AWS。

## 核心定位

Skill 5 的價值是把 Skill 1 到 Skill 4 的證據轉成兩種輸出：

- **人類版 Markdown**：給主管或 reviewer 快速看懂結果。它先回答 PoC 發現什麼、帳號/地區/權限能不能用、實際做完什麼、為什麼有意義、還不能宣稱什麼、下一步要補什麼決策證據。
- **JSON / GUI model**：保留完整 audit trail，包括 quote line items、stage evidence、evidence ledger、runtime checks、resource inventory、permission surface、timing、future work 和 external research directions。

人類版不是狀態帳本，不應塞滿 run ID、quote ID、artifact、raw status code、internal recipe identifier 或英文 success criteria。

## 執行方式

從 `radar-redesign/` 執行：

```powershell
python -m agentic_cloud_radar.cli s5 `
  --s1 .\out\run\s1.json `
  --s2 .\out\run\s2.json `
  --s3 .\out\run\s3.json `
  --s4 .\out\run\s4.json `
  --runtime .\out\run\s4-runtime-cleaned.json `
  --output .\out\run\s5-report.json `
  --markdown-output .\out\run\s5-report.md
```

`--runtime` 是 optional。部署或 cleanup 前的 interim report 可以省略它。

沒有 `--billing` input：本 pipeline 只報告 pre-deployment estimate，不會和 AWS Billing / Cost Explorer / CUR 對帳。

重用 `agentic_cloud_radar/s5.py`。

## 工作流程

1. 檢查 S1/S2/S3/S4 stage presence、`run_id` 和 candidate lineage。
2. artifact 缺失或 run 不一致時，標記 `incomplete_artifacts`。
3. 顯示 Skill 3 score，但不重新計算。例如 `4.4 / 5`。不要顯示或推導獨立 certainty metric。
4. 完整 Skill 3 quote 保留在 JSON / GUI data。人類版 Markdown 只摘要 expected cost、approval ceiling、cost nature 和 official price basis。除非使用者要求 calculation appendix，否則不要顯示 quote ID 或長 line-item table。
5. 所有成本只能呈現為 estimate。不得說成 verified、reconciled、invoiced 或 actual cost。
6. 如果 S4 runtime 有 `pre_cleanup_usage_snapshot`，詳細 runtime usage evidence 留在 JSON / GUI data。人類版 Markdown 只摘要 cleanup result，並說明 runtime usage 不是 AWS billing evidence。
7. 人類版 Markdown 必須以一屏內可讀的主管摘要開頭，回答：
   - PoC 做完發現什麼？
   - 這個 AWS account、target Region、tested permission path 能不能跑？
   - 實際完成哪些事？
   - 這件事對公司或導入判斷的意義是什麼？
   - 現在還不能宣稱什麼？
   - 下一步要補哪個 decision evidence？
8. S1-S5 stage evidence 和 claim-source ledger 保留在 JSON / GUI data。除非使用者要求 audit appendix，不要把它們渲染成 Markdown 長表。
9. 不要在人類版 Markdown 曝露 internal file names、raw artifact wording、run IDs、quote IDs、raw status codes、internal recipe identifiers 或 English-only success criteria。用繁中翻譯成「發現、完成、限制、意義」。
10. 產出一份 JSON report、一份 embedded Markdown、一份 stable GUI model。
11. Future work 必須是 case-specific external research directions：精確 search query、為什麼要查、什麼證據才有用、查到後會如何改變下一輪 PoC 或 stop decision。
12. 只有 runtime status 是 `cleanup_verified` 時，report 才能是 `final`。新的 `s4.runtime-evidence.v3` 還需要 Console/resource inventory review metadata 與 `display_channel_confirmed`。Cost-control abort 是 `final_without_console_review`，report type 是 `closed_without_console_review`，不能當正常 actual-PoC final。

## 人類版 Markdown 必備區塊

人類版 Markdown 是 summary report，不是 audit dump。必備區塊：

- **一眼看重點**：結論、做完發現、對公司的意義、主要不能宣稱的限制。
- **帳號、地區、權限能不能用**：表格回答 AWS account、target Region、tested permission path、cleanup 是否可用或已驗證。
- **我實際做完了什麼**：來源整理、Skill 3 score、成本估算、部署、runtime checks、Console/resource inventory review、cleanup。
- **這次 PoC 證明了什麼**：只列真正有意義的 verified behavior，並翻成繁中。
- **成本與清除狀態**：expected estimate、approval ceiling、public-price nature、不是 AWS billing、cleanup result。
- **還不能拿來宣稱的事**：例如非 production validation、未測效能/可靠性/長時間運作、預估成本不是帳單。
- **下一步要補的決策證據**：case-specific next test 或 external research direction。
- **官方來源**：候選的可信公開來源 URL。

## JSON / GUI model 保留的 audit trail

機器可讀輸出仍需保留：

- candidate / source
- Skill 3 score 與 full quote details
- quote line items、公式、source URLs
- validation rows 與 runtime checks
- pre-cleanup usage snapshot
- resource inventory
- permission surface
- stage timings
- verified facts
- unknown or not verified
- future work
- external research directions
- reviewer questions
- related reading
- S1-S5 stage evidence
- evidence source table
- S1-S4 funnel

## Claim rules

- Named-human cost ceiling 不是官方價格。
- Public-price quotation 是 non-binding estimate，不是 AWS invoice、formal AWS sales quote 或 actual bill。
- PoC quote 通常使用月費或 usage-based public price units；若 PoC 只跑幾小時，要寫清楚換算基礎。
- Lambda 成本必須描述成 request count 與 duration / GB-second，不是 always-on resource。
- Skill 3 quote 預設是 static public-rate-card estimate；除非 `live_pricing_api_used=true`，否則不是 real-time AWS Pricing API quotation。
- `recommend_poc` 代表技術上具備 controlled PoC 資格，不代表 candidate 適合公司 workload。
- Runtime duration、CloudFormation status、cleanup status 都不是 cost evidence。
- `pre_cleanup_usage_snapshot` 是 immediate runtime evidence，可支持成本說明，但不能轉成 actual AWS cost。
- 本 pipeline 不把 quote 和 AWS billing 對帳。要明說這個限制，不得暗示金額已被帳單確認。
- JSON / GUI audit data 中，line item 的 billing method 和 formula 必須完整，讓 reviewer 能檢查 calculation。
- 不要漏列 zero-charge recipe resources、usage assumptions、exclusions 或 source URLs。
- `CREATE_COMPLETE` 是 deployment evidence，不是 cleanup evidence。
- `deployed_not_quoted` 代表 quote 漏列實際建立的 resource，應視為 quote defect，不是 rounding difference。
- Permission surface 只涵蓋 tested recipe，不是 production permission set。
- Machine time 和 human wait 要分開報告，不要合成單一 elapsed figure。
- Console screenshot metadata 只證明 redacted PNG 被 capture 和 hash。`display_channel_confirmed` 記錄具名人類在哪裡看到它；程式不解讀 image content。
- Forced cleanup 是 cost control，不是 deployed stack 已經完成 Console review 的證明。
- Sandbox evidence 只證明 tested recipe 與 tested workload，不得泛化成所有環境都可用。
- Missing evidence 必須維持 `unknown`。
- Future work 不得是 generic filler，例如「準備 final proposal」、「read AWS docs」、「do more testing」。必須連到候選具體 PoC decision，說明要外搜什麼、什麼證據有用、會改變哪個決策。

## 外部搜尋與延伸閱讀規則

Skill 5 可以產出 external research directions，但要清楚標示：

- 這是下一步搜尋建議，不是已驗證結論。
- 採用前，搜尋到的證據必須回填 S1/S2/S3 artifact，才能變成 report evidence。
- 每個方向要包含 query、why、useful evidence shape、after-search action。

例如 Lambda self-managed S3 code storage：

- 搜 `Lambda self-managed S3 code storage deployment artifact rollback versioning`
- 搜 `Lambda S3ObjectStorageMode REFERENCE bucket policy GetObjectVersion code signing`
- 搜 `Lambda self-managed S3 code storage lifecycle quota cold start troubleshooting`

例如 S3 Files：

- 搜 `S3 Files EC2 mount workload migration NFS S3 bucket architecture`
- 搜 `S3 Files IAM access point mount target VPC security group permissions`
- 搜 `S3 Files pricing troubleshooting consistency latency mount failure`

## 驗證

```powershell
python -m unittest tests.test_s5 -v
```

## 階段收尾清單

結束 Skill 5 前，必須完成並回報：

- 更新 `AI_PM_INBOX.md` 或正式 daily log，記錄階段成果、證據、blocker 與下一步。
- 若本次改變專案狀態或跨電腦交接內容，更新 `README.md`、`MIGRATION_STATUS.md` 或其他 handoff 文件。
- 執行相關驗證指令，若無法執行要說明原因。
- 檢查 `git status --short`，並說明變更是否符合預期。
- 在需要共享時提交有意義的 commit。
- 需要同步時 push branch。
- 宣稱已同步前，確認 GitHub 上看得到 pushed state。
- 用清楚繁中留下下一個人類或 AI 需要做的動作。
