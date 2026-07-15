# Cathay Tech Intel Pipeline v3

公司帳戶落地版，部署區域固定為 `ap-southeast-1`。

本版本不是架構草稿。封包內已包含可部署的 AWS runtime、Lambda handlers、Step Functions 流程、報價閘門、成本文件、Skills、案例資料與 RQ1/RQ2/RQ3 留痕設計。

## 系統定位

v3 技術雷達把每日雲端技術情報流程拆成三層：

- `Skills`：AI 工作規則與本地可讀知識庫。
- `CDK`：AWS 雲端資源與部署定義。
- `Anthropic API`：S3/S4 evaluator / validator 的 AI 評分能力。

公司帳戶版刻意不依賴 Amazon Bedrock，也不使用 CloudFront。報告以 S3 物件與 presigned URL 交付，降低公司帳戶中 SCP、Region restriction、global service 權限造成的部署風險。

## 已包含內容

### AWS Runtime

- S3：儲存每次 pipeline 的 JSON、HTML、報價單與成本估算。
- DynamoDB：儲存 AI pick 與 human pick log，支援 RQ1/RQ2/RQ3 追蹤。
- Secrets Manager：保存 Anthropic API key。
- Lambda：完整 S1-S5 pipeline handlers、報價 Lambda、人工 pick Lambda、選配 API start Lambda。
- Step Functions：編排 S1 → S2 → Quote Gate → S3 → S4 → S5。
- EventBridge Scheduler：每日 08:00 台北時間排程，預設關閉，可用 context 開啟。
- Cognito + API Gateway：選配手動啟動 API，可用 `-c enable_api=true` 開啟。
- CloudWatch Logs：Lambda 與 Step Functions 執行紀錄。

### Pipeline

1. S1 掃描 AWS 技術來源與 fixtures。
2. S2 依國泰情境與公司需求排序。
3. S2b 執行前報價，產出 `quotation.json` / `quotation.html`。
4. S3 evaluator 評估所有 L1 候選。
5. S4 validator 獨立重評候選。
6. S5 依 evaluator / validator 平均分數選 Top 3，產出最終報告。

若報價超過 `MAX_RUN_USD`，流程會自動改走 zero-token rubric fallback，不會中斷。

### 文件

- `DEPLOY.md`：公司帳戶部署步驟。
- `docs/v3-技術雷達-報價單.md`：正式中文報價單。
- `docs/v3-tech-radar-quotation.md`：ASCII 檔名報價單副本，避免解壓工具中文檔名顯示問題。
- `docs/cost-quotation.md`：成本與預算策略。
- `docs/cost-estimate.yaml`：機器可讀成本估算。
- `docs/cloudformation-yaml-note.md`：CloudFormation / YAML 說明。
- `architecture-scan/architecture_scan.md`：架構掃描結果。

## 成本與報價

目前預設：

- 單次執行上限：`MAX_RUN_USD=0.50`
- S2 後保留候選：6
- Evaluator：Claude Sonnet 4.5
- Validator：Claude Haiku 4.5
- 單次完整 LLM 報價：約 USD 0.0892
- 輕量落地驗證月估：約 USD 5-15
- 實作 / 驗證預算上限：USD 100

每次執行會輸出：

```text
s3://<bucket>/runs/<run_id>/quotation.json
s3://<bucket>/runs/<run_id>/quotation.html
s3://<bucket>/runs/<run_id>/report.html
s3://<bucket>/runs/<run_id>/cost-estimate.yaml
s3://<bucket>/reports/latest.html
s3://<bucket>/reports/cost-estimate.yaml
```

## 部署摘要

```powershell
cd cdk
python -m pip install -r requirements.txt
.\scripts\build-layer.ps1 -Python python

aws configure --profile intern
$env:AWS_PROFILE = "intern"
aws sts get-caller-identity --profile intern

cdk bootstrap aws://<COMPANY_ACCOUNT_ID>/ap-southeast-1
cdk synth
cdk deploy cathay-techintel-v3-data cathay-techintel-v3-secrets cathay-techintel-v3-pipeline
```

部署後更新 Anthropic API key：

```powershell
aws secretsmanager put-secret-value `
  --profile intern `
  --secret-id cathay-techintel-v3/anthropic-api-key `
  --secret-string "sk-ant-YOUR_REAL_KEY" `
  --region ap-southeast-1
```

手動執行：

```powershell
aws stepfunctions start-execution `
  --profile intern `
  --state-machine-arn "<StateMachineArn>" `
  --input "{\"run_id\":\"company-landing-001\"}" `
  --region ap-southeast-1
```

詳細步驟請看 `DEPLOY.md`。

## 公司帳戶注意事項

- 若 `cdk bootstrap` 因 IAM 權限失敗，請 mentor / admin 代跑一次 `CDKToolkit` bootstrap。
- 若公司 SCP 阻擋某服務，先保留錯誤訊息中的 service/action，回報權限需求。
- 若 Anthropic key 尚未更新，S3/S4 會走 rubric fallback，流程仍可驗證部署。
- EventBridge 排程與 API Gateway 預設關閉，正式需要時再用 context 開啟。
- 落地驗證後若不需保留資源，可執行 `cdk destroy --all`。

## 封包狀態

此封包是完整公司帳戶部署版：

- 已有可部署 CDK stacks。
- 已有 Lambda handlers 與 pipeline shared library。
- 已有報價單與報價閘門。
- 已有成本估算與公司帳戶部署文件。
- 已有本地 Skills 與案例資料。

部署前仍需由公司帳戶提供 AWS credentials、CDK bootstrap 權限與 Anthropic API key。
