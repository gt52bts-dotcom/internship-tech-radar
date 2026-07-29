# S4 完整 PoC 部署操作：從 S3 artifact 到 cleanup

`agentic_cloud_radar.s4` 仍負責判定 paid-PoC gate；`s4_deployer.py` 才負責已核准後的完整 S4。兩者合起來才符合「部署、驗證、Console 回驗、cleanup」的交付定義。

## 1. 不會自動建資源的保證

以下任一情況都只會停在 artifact，不會呼叫 AWS：

- 只執行 `s4` 或 `s4-deploy`，沒有 `--execute`。
- approval 沒有 `deployment_authorized: true`。
- S3 未推薦此候選、成本超過 policy、或沒有真人 `approved_by`。
- S1/S2/S3 路徑、run ID、candidate ID 或 S3 內容不一致。
- 沒有此候選專用的 recipe。

目前已註冊兩個 recipe：`s3_files_cdk` 位於 `poc/s3-files-cdk-poc/`，曾在 intern 環境完成端到端回驗；`lambda_self_managed_s3_code_storage_cdk` 位於 `poc/lambda-self-managed-storage-cdk-poc/`，已通過 CDK synth 與 CloudFormation contract 驗證，等待本次人工核准後首次 live PoC。其他新聞候選仍必須先新增自己的 CDK recipe 與驗證 handler，否則結果會是 `needs_poc_recipe`。

## 2. Approval 契約

以 [s4-deployment-approval.example.json](../samples/s4-deployment-approval.example.json) 為起點。它必須包含：

- `selected_candidate_id`：S3 裡的其中一個候選。
- `lineage`：這一次 S1、S2、S3 artifact 的絕對或可解析路徑。S4 會重新讀取、核對 stage、run ID、candidate ID，並記錄 SHA-256。
- `validation_type: paid_poc`、`approved_by`、`estimated_usd`、`automatic_poc_start: false`。
- `deployment_authorized: true`：Cleo 看過 S3 通知後的明確部署核准。
- 若 `region_status=region_unknown`，還要以 `region_warning_acknowledged: true` 明確承認證據缺口；這只放行 Region warning，不會略過成本、核准、lineage 或 recipe gate。
- `deployment.profile`、`deployment.target_region`、成功標準與 cleanup 範圍。

## 3. 命令順序

```powershell
Set-Location C:\Users\youhs\Documents\實習專案\radar-redesign

# 只產生、檢閱 deployment context；不會建立 AWS 資源。
python -m agentic_cloud_radar.cli s4-deploy `
  --input .\out\run\s3.json `
  --approval .\out\run\s4-approval.json `
  --output .\out\run\s4-deployment-context.json

# Cleo 檢閱 context 後，才明確以 --execute 建立該次 recipe 的資源。
python -m agentic_cloud_radar.cli s4-deploy `
  --input .\out\run\s3.json `
  --approval .\out\run\s4-approval.json `
  --output .\out\run\s4-deployment-context.json `
  --execute `
  --runtime-output .\out\run\s4-runtime.json

# 在 CloudFormation / Infrastructure Composer 完成真人回驗後記錄確認。
python -m agentic_cloud_radar.cli s4-console-review `
  --input .\out\run\s4-runtime.json `
  --confirmed-by "Cleo" `
  --output .\out\run\s4-console-reviewed.json

# 最後才明確清理；會只處理此 runtime artifact 指向的 stack。
python -m agentic_cloud_radar.cli s4-cleanup `
  --input .\out\run\s4-console-reviewed.json `
  --execute `
  --output .\out\run\s4-cleanup.json
```

## 4. S3 Files recipe 實際做什麼

1. 用 run ID 衍生 stack name 與 resource prefix。
2. 呼叫既有 CDK app synth 出 CloudFormation template，並以 CloudFormation `create-stack` 部署。
3. 讀取 stack outputs，在測試 bucket 放一個非敏感檔案。
4. 等待 EC2 的 SSM Online，透過 SSM 確認 S3 Files mount、讀取 S3 放入的檔案、寫回 mount。
5. 由 S3 讀回 mount 寫入的檔案，建立雙向驗證。
6. runtime artifact 停在 `awaiting_console_review`，不能直接 cleanup。
7. Console review 後，先清空此 stack 的 versioned test bucket，再刪除 stack 並等 CloudFormation deletion 完成。

runtime artifact 只保存 lineage、狀態、recipe、驗證結果與 cleanup 狀態；不保存 AWS account ID、ARN、IP 或 SSM command output。

## 5. Lambda self-managed S3 code storage recipe

Lambda recipe 只使用這次 run 衍生名稱的測試資源：一個版本化、加密且封鎖公開存取的 S3 bucket；一個在 CloudFormation 內上傳非敏感 `.zip` 的 custom resource；以及一個 `AWS::Lambda::Function`。目標函數的 `Code` 會明確寫入 `S3ObjectStorageMode: REFERENCE`、S3 key 與 S3 object version，並以 bucket policy 只讓 Lambda service principal 讀取該 object version。

S4 部署後會檢查 CloudFormation output 的 `REFERENCE` 與 S3 version，再 invoke 函數，要求其回傳本次 run ID 和 `storage_mode=REFERENCE`。這代表 CloudFormation 接受了 reference mode，且函數可由 self-managed S3 code 啟動。cleanup 仍先清空這個 stack 的 versioned bucket，再刪除整個 stack。
