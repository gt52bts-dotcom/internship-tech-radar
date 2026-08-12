---
name: validate-cloud-poc
description: 在 Skill 3 已產出完整估算與人類核准後，執行單一受控 AWS PoC 階段，並保留 artifact lineage 與簡短 human gate。適用於 Skill 4 quote-versus-ceiling 檢查、CDK 或 CloudFormation deployment、具名人類核准、runtime evidence、Console/resource inventory review，以及 run-scoped cleanup。
---

# Skill 4 Validate：受控 AWS PoC 驗證

Skill 4 只代表一件事：建立邊界明確、成本可控、可清除的 AWS PoC 資源。它永遠不會自動開始，也不是第二條 low-risk validation track。

## 核心定位

Skill 4 的價值不是展示「有跑起來」，而是產出實際 runtime evidence：

- 目標帳號與 Region 是否真的能建立資源。
- recipe 是否建立預期的 resource relationship。
- 權限是否足以完成最小測試。
- runtime check 是否通過。
- cleanup 是否可控且可回查。

## PoC gate

從 `radar-redesign/` 執行：

```powershell
python -m agentic_cloud_radar.cli s4 `
  --input .\out\run\s3.json `
  --output .\out\run\s4.json
```

這個指令只建立 approval gate artifact。沒有 approval 時，結果是 `awaiting_poc_approval`；它不會把 Skill 4 改成 no-cost validation。

## 受控 PoC 條件

任何 live action 前，先讀 `docs/s4-受控PoC部署流程.md` 或目前 repository 中對應的 Skill 4 操作文件。

必須同時具備：

- S1/S2/S3 lineage 與 artifact hash 一致。
- Skill 3 `recommend_poc=true`。
- Skill 3 有具體 PoC proof question，說清楚這次 PoC 要證明什麼、成功會新增什麼決策證據、做完後仍未知什麼。
- 有 registered candidate-specific recipe 和完整 Skill 3 quote。
- effective ceiling 取三者最小值：Skill 3 recommended approval ceiling、人類核准 ceiling、內建 sandbox ceiling。
- target Region 必須有官方證據，或在 `region_unknown` 時明確用 `region_warning_acknowledged=true` 承認風險。
- 具名人類核准，且 `deployment_authorized=true`。
- 第二次明確 CLI `--execute`。

除非 reviewer 提供更嚴格限制，否則使用內建 small-cost ceiling、target Region、recipe success criteria 與 cleanup scope。

## 執行指令

建立 approval template：

```powershell
python -m agentic_cloud_radar.cli s4-approval-template `
  --input .\out\run\s3.json `
  --selected-candidate-id "<candidate-id>" `
  --approved-by "<named-human>" `
  --authorize `
  --output .\out\run\s4-approval.json
```

部署受控 PoC：

```powershell
python -m agentic_cloud_radar.cli s4-deploy `
  --input .\out\run\s3.json `
  --approval .\out\run\s4-approval.json `
  --output .\out\run\s4-deployment-context.json `
  --runtime-output .\out\run\s4-runtime.json `
  --execute
```

建立 review packet：

```powershell
python -m agentic_cloud_radar.cli s4-console-review-packet `
  --input .\out\run\s4-runtime.json `
  --review-timeout-minutes 60 `
  --output .\out\run\s4-console-review-packet.json
```

完成人工確認並清除：

```powershell
python -m agentic_cloud_radar.cli s4-close `
  --input .\out\run\s4-runtime.json `
  --packet .\out\run\s4-console-review-packet.json `
  --review-evidence .\out\run\s4-console-review\<run-id>\s4-console-review-evidence.json `
  --confirmed-by "<named-human>" `
  --shared-via conversation `
  --notes "<concise-review-note>" `
  --output .\out\run\s4-runtime-cleaned.json `
  --usage-snapshot-output .\out\run\pre_cleanup_usage_snapshot.json `
  --execute
```

## Resource inventory gate

早期流程曾用 Infrastructure Composer screenshot 作為 review gate，但程式不能真正理解圖片內容，只能驗證檔案與 metadata 存在。新版 gate 以 CloudFormation resource inventory 為主：

```powershell
aws cloudformation describe-stack-resources --stack-name <run-derived-stack>
```

`agentic_cloud_radar/s4_inventory.py` 會把 response 轉成 review packet：

- 每個 resource 的 logical id、type、status、redacted physical id。
- deployed resources 與 Skill 3 quote 中定價資源的 reconciliation。
- `deployed_not_quoted` 代表 quote 漏列實際建立的 resource，必須修正 resource list，不是金額 rounding issue。
- 本次 run 實際需要的 IAM actions，這些通常不是公開文件會完整列出的內容。
- `inventory_sha256`，確保人類確認的 bytes 和程式 hash 的 bytes 是同一份文件。

具名人類仍必須在 cleanup 前確認。Playwright、headful browser、screenshot storage 不再是必要流程。

## Workflow

1. 在接觸 AWS 前，確認 lineage、quote status、estimated range、validity 和 approval。
2. 在 approval 或 deployment notes 中重述 PoC proof question。若 proof question 模糊、缺失，或 Skill 3 已完全回答，部署前停止並要求更清楚的目的。
3. 產生 candidate recipe 並檢查 CloudFormation。
4. 只建立 run-derived sandbox resources。
5. 如果同一 run-derived stack 已經是 `CREATE_COMPLETE`，恢復 verification，不建立重複資源。
6. 候選服務可能有 eventual consistency；對預期短暫 read-back gap 使用 bounded retry，超時後失敗。
7. 記錄 deployment status 和 runtime checks，但不得記錄 secrets、account IDs、full ARNs 或 private addresses。
8. 暫停等待具名人類 cleanup confirmation。不能把部署核准當作 cleanup 確認。
9. 執行 `s4-close --execute`。刪除前記錄 `pre_cleanup_usage_snapshot.json`，包含 create/delete-before timestamps、CloudFormation resources、resource tags、S3 object count/versions/bytes、Lambda configuration、CloudWatch metrics，以及 recipe-specific runtime facts，例如 EC2 state。
10. pre-cleanup snapshot 只屬於 usage evidence，不是 billing evidence。不要為了 Cost Explorer 或 Billing data 延遲 cleanup。
11. cleanup 只清除 reviewed run，並重新查詢 scoped resources。
12. Skill 5 的 actual-PoC conclusion 只能從 `cleanup_verified` runtime artifact 產生。

## Timeout 與 abort

`review_deadline` 是 review timeout 的唯一客觀定義。超過 deadline，或 deployment / normal-close failure 後，只能在有具名 cost-control approver 和 reason 時使用：

```powershell
python -m agentic_cloud_radar.cli s4-abort --execute ...
```

timeout abort 必須包含 `--packet .\out\run\s4-console-review-packet.json`。它會記錄 `skipped_for_cost_control` / `abort_without_console_review`；Skill 5 不得把它當成正常 Console review final。

## Registered recipes

目前支援：

- S3 Files：EC2 mount 與 S3 bucket 雙向 object check。
- Lambda self-managed S3 code storage：versioned artifact、`REFERENCE` mode 與 invoke verification。

未知候選必須停在 `needs_poc_recipe`。

固定 sandbox ceiling 是 policy control，不是 quote。不要用它替代缺失的 rates。

## Recipe registry contract

Skill 4 不應臨時推論 recipe。所有可部署 recipe 必須登錄在 `agentic_cloud_radar/s4_recipes/registry.py`，並使用 `base.py` 的契約。

常見狀態：

| 狀態 | 意義 | 是否可建立 AWS 資源 |
|---|---|---|
| `recipe_registered` | 有可部署 recipe | 可以，但仍需 approval 與 `--execute` |
| `recipe_draft_only` | 只有草稿，還不能部署 | 不可以 |
| `needs_new_recipe` | 沒有對應 recipe | 不可以 |

沒有 `deployable_recipe_registered=true` 時，不得進 deployment。

## Stage timing

每個 stage 會記錄 `started_at`、`ended_at`，在人類 gate 另記錄 `human_wait_seconds`。

`agentic_cloud_radar/pipeline_timing.py` 會分開回報 machine time 與 human wait。不要把它們合成一個 elapsed figure，否則會把人類 approval bottleneck 誤解成程式慢。

`time_to_first_success_seconds` 是用來比較 adoption friction 的單一指標。

## 驗證

```powershell
python -m unittest tests.test_s3_s4 -v
```

## 階段收尾清單

結束 Skill 4 前，必須完成並回報：

- 更新 `AI_PM_INBOX.md` 或正式 daily log，記錄階段成果、證據、blocker 與下一步。
- 若本次改變專案狀態或跨電腦交接內容，更新 `README.md`、`MIGRATION_STATUS.md` 或其他 handoff 文件。
- 執行相關驗證指令，若無法執行要說明原因。
- 檢查 `git status --short`，並說明變更是否符合預期。
- 在需要共享時提交有意義的 commit。
- 需要同步時 push branch。
- 宣稱已同步前，確認 GitHub 上看得到 pushed state。
- 用清楚繁中留下下一個人類或 AI 需要做的動作。

## 下一階段

把 S4 validation artifact 和 optional runtime evidence 交給 `$report-cloud-evidence`。
