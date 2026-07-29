# 技術驗證報告｜AWS Lambda 宣布自主管理程式碼儲存空間 - AWS

- 報告狀態：interim
- Run ID：direct-url-20260729-9d2a3d3c
- 來源：https://aws.amazon.com/tw/about-aws/whats-new/2026/07/lambda-self-managed-code-storage/

## 一句結論

> PoC 技術驗證通過。CloudFormation deployment、REFERENCE 設定與 Lambda invoke 已通過。AWS Console review 與 cleanup 尚待完成。

## 評估摘要

| 指標 | 結果 |
| --- | --- |
| Skill 3 加權分 | 4.0 |
| 信心 | medium |
| 區域狀態 | available_ap_southeast_1 |
| 是否建議 Skill 4 | 是 |
| 成本 | unknown |

## 技術驗證

| 檢查 | 狀態 |
| --- | --- |
| Skill 4 validation | paid_poc_ready_for_manual_start |
| CloudFormation | CREATE_COMPLETE |
| 自動化驗證 | verified |
| AWS Console review | required |
| cleanup | pending_console_review |

## 已證實的事實

- 官方來源已記錄：https://aws.amazon.com/tw/about-aws/whats-new/2026/07/lambda-self-managed-code-storage/
- Skill 3 加權分已依固定 rubric 計算：4.0
- CloudFormation stack 已達 CREATE_COMPLETE。
- Skill 4 自動化驗證已通過：cloudformation_reference_mode。
- Skill 4 自動化驗證已通過：lambda_invoke。

## 尚未驗證或證據不足

- No candidate-relevant official AWS pricing page was fetched in this S2 run.
- No candidate-relevant official AWS Region or availability page was fetched in this S2 run.
- 官方定價或實際成本尚未在 artifact 中證實。
- AWS Console review 尚未完成或尚未記錄。
- cleanup 尚未完成或尚未記錄。

## 後續提醒

- No safe non-production environment or required permission is available.
- Official pricing or cleanup cannot be bounded within the USD 3 cap.
- No measurable baseline exists for the proposed workflow.
- 完成 AWS Console review 後，才能執行受控 cleanup。

## 證據帳本

| 敘述 | 類型 | 狀態 | 證據 |
| --- | --- | --- | --- |
| 候選技術的公開來源 | source-backed fact | recorded | https://aws.amazon.com/tw/about-aws/whats-new/2026/07/lambda-self-managed-code-storage/ |
| recipe | runtime evidence | lambda_self_managed_s3_code_storage_cdk | S4 runtime artifact |
| cloudformation_reference_mode | runtime evidence | verified | S4 runtime artifact |
| lambda_invoke | runtime evidence | verified | S4 runtime artifact |
