# 公司帳戶部署手冊

適用封包：`Cathay Tech Intel Pipeline v3` 公司帳戶落地版  
目標區域：`ap-southeast-1`  
專案前綴：`cathay-techintel-v3`

## 0. 部署前確認

在終端機確認工具版本：

```powershell
node --version
npm --version
python --version
aws --version
```

建議版本：

- Node.js 18 以上
- Python 3.9 以上
- AWS CLI v2
- AWS CDK CLI v2

安裝 CDK CLI：

```powershell
npm install -g aws-cdk
cdk --version
```

## 1. 設定公司帳戶憑證

```powershell
aws configure --profile intern
```

請填入公司帳戶提供的：

- AWS Access Key ID
- AWS Secret Access Key
- Default region name：`ap-southeast-1`
- Default output format：`json`

驗證目前身分：

```powershell
aws sts get-caller-identity --profile intern
```

確認 `Account` 是公司帳戶，不是個人帳戶。

接著設定本次 shell 使用該 profile：

```powershell
$env:AWS_PROFILE = "intern"
```

## 2. 安裝 Python 依賴與 Lambda Layer

```powershell
cd cdk
python -m pip install -r requirements.txt
.\scripts\build-layer.ps1 -Python python
```

確認 layer 產物存在：

```text
cdk/layer_build/python/
```

其中應包含 `anthropic` 與 `feedparser` 等套件。

## 3. Bootstrap

每個 AWS account + region 第一次使用 CDK 都需要 bootstrap：

```powershell
cdk bootstrap aws://<COMPANY_ACCOUNT_ID>/ap-southeast-1
```

若這一步出現 `AccessDenied`，通常是公司帳戶不允許目前使用者建立 CDK bootstrap IAM role。請 mentor 或管理員代跑一次。完成後可用下列指令確認：

```powershell
aws cloudformation describe-stacks `
  --profile intern `
  --stack-name CDKToolkit `
  --region ap-southeast-1
```

## 4. Synth 檢查

```powershell
cdk synth
```

這一步只在本機產生 CloudFormation template，不會建立 AWS 資源。若這裡失敗，通常是程式碼或依賴問題。

## 5. 部署三個 Stack

先部署預設落地版：

```powershell
cdk deploy cathay-techintel-v3-data cathay-techintel-v3-secrets cathay-techintel-v3-pipeline
```

預設部署內容：

- S3 data/report bucket
- DynamoDB pick log table
- Secrets Manager 初始佔位值
- Lambda S1/S2/S2b/S3/S4/S5
- RecordHumanPick Lambda
- Step Functions
- EventBridge schedule resource，狀態為 disabled
- CloudWatch Logs

預設不部署：

- CloudFront
- Amazon Bedrock
- OpenSearch / RDS / EC2
- API Gateway / Cognito

## 6. 寫入 Anthropic API Key

Secrets Manager 初始值是佔位字串。部署後請更新成真正 key：

```powershell
aws secretsmanager put-secret-value `
  --profile intern `
  --secret-id cathay-techintel-v3/anthropic-api-key `
  --secret-string "sk-ant-YOUR_REAL_KEY" `
  --region ap-southeast-1
```

安全規則：

- key 不貼聊天工具。
- key 不寫進 git。
- key 不截圖。
- 若 key 尚未更新，S3/S4 會走 rubric fallback，仍可驗證 AWS 流程。

## 7. 手動執行 Pipeline

從 deploy output 複製 `StateMachineArn`，然後執行：

```powershell
aws stepfunctions start-execution `
  --profile intern `
  --state-machine-arn "<StateMachineArn>" `
  --input "{\"run_id\":\"company-landing-001\"}" `
  --region ap-southeast-1
```

查看最近執行：

```powershell
aws stepfunctions list-executions `
  --profile intern `
  --state-machine-arn "<StateMachineArn>" `
  --max-results 5 `
  --region ap-southeast-1
```

## 8. 檢查報價單與報告

每次執行會產生：

```text
s3://<bucket>/runs/<run_id>/quotation.json
s3://<bucket>/runs/<run_id>/quotation.html
s3://<bucket>/runs/<run_id>/report.html
s3://<bucket>/runs/<run_id>/cost-estimate.yaml
s3://<bucket>/reports/latest.html
s3://<bucket>/reports/cost-estimate.yaml
```

列出該次執行輸出：

```powershell
aws s3 ls s3://cathay-techintel-v3-data-<COMPANY_ACCOUNT_ID>/runs/company-landing-001/ `
  --profile intern `
  --region ap-southeast-1
```

下載報價單與報告：

```powershell
aws s3 cp s3://cathay-techintel-v3-data-<COMPANY_ACCOUNT_ID>/runs/company-landing-001/quotation.html ./quotation.html `
  --profile intern `
  --region ap-southeast-1

aws s3 cp s3://cathay-techintel-v3-data-<COMPANY_ACCOUNT_ID>/runs/company-landing-001/report.html ./report.html `
  --profile intern `
  --region ap-southeast-1
```

S5 Lambda 回傳中也會提供 `report_url` presigned URL。

## 9. 開啟排程

預設排程關閉。若要每日台灣時間 08:00 自動執行：

```powershell
cdk deploy cathay-techintel-v3-pipeline -c schedule_enabled=true
```

## 10. 開啟 API Gateway / Cognito

預設 API 關閉。若需要由外部工具用 Cognito token 手動啟動 pipeline：

```powershell
cdk deploy cathay-techintel-v3-pipeline -c enable_api=true
```

部署後會輸出：

- `ControlApiUrl`
- `UserPoolId`
- `UserPoolClientId`

API endpoint：

```text
POST <ControlApiUrl>/runs
```

## 11. RQ1 人工 Pick 記錄

建立 `pick.json`：

```json
{
  "run_id": "company-landing-001",
  "picked_ids": ["A03"],
  "reviewer": "grace",
  "human_minutes": 18,
  "blind": true,
  "note": "人工盲測選題紀錄"
}
```

呼叫 Lambda：

```powershell
aws lambda invoke `
  --profile intern `
  --function-name cathay-techintel-v3-recordhumanpick `
  --cli-binary-format raw-in-base64-out `
  --payload file://pick.json `
  output.json `
  --region ap-southeast-1
```

檢查 DynamoDB：

```powershell
aws dynamodb scan `
  --profile intern `
  --table-name cathay-techintel-v3-picks-log `
  --region ap-southeast-1
```

## 12. 常見卡點

| 問題 | 常見原因 | 處理方式 |
|---|---|---|
| `cdk bootstrap` AccessDenied | 沒有建立 IAM role 權限 | 請 mentor / admin 代跑 bootstrap |
| `cdk deploy` UnauthorizedOperation | 公司 SCP 阻擋服務或 action | 保存錯誤訊息，回報缺少的 service/action |
| Lambda `No module named anthropic` | `layer_build/python` 未建好 | 重新執行 `scripts/build-layer.ps1` |
| S3/S4 沒有真的呼叫 LLM | Secret 仍是佔位字串或 key 無效 | 更新 Secrets Manager key |
| 報價超過上限 | `MAX_RUN_USD` 太低或候選數增加 | 確認預算後用 `-c max_run_usd=...` 調整 |
| 找不到報告 URL | 公司版不用 CloudFront | 從 S3 下載，或看 S5 output 的 presigned URL |

## 13. 清理資源

落地驗證後若不保留環境：

```powershell
cdk destroy --all
```

這會刪除本封包建立的 CDK 資源。執行前請先確認 S3 報告與 DynamoDB 記錄是否需要留存。
