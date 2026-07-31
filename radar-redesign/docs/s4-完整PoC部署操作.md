# S4 完整 PoC 部署操作：從 Skill 3 artifact 到截圖確認 cleanup

`agentic_cloud_radar.s4` 負責判定 PoC gate；`s4_deployer.py` 才負責已核准後的完整 S4。兩者合起來才符合「部署、驗證、Console 回驗、cleanup」的交付定義。

## 1. 不會自動建資源的保證

以下任一情況都只會停在 artifact，不會呼叫 AWS：

- 只執行 `s4` 或 `s4-deploy`，沒有 `--execute`。
- approval 沒有 `deployment_authorized: true`。
- S3 未推薦此候選、成本超過 policy、或沒有真人 `approved_by`。
- S1/S2/S3 路徑、run ID、candidate ID 或 S3 內容不一致。
- 沒有此候選專用的 recipe。

目前已註冊兩個 recipe：`s3_files_cdk` 位於 `poc/s3-files-cdk-poc/`，曾在隔離測試環境完成端到端回驗；`lambda_self_managed_s3_code_storage_cdk` 位於 `poc/lambda-self-managed-storage-cdk-poc/`，已通過 CDK synth 與 CloudFormation contract 驗證。其他新聞候選仍必須先新增自己的 CDK recipe 與驗證 handler，否則結果會是 `needs_poc_recipe`。

## 2. Approval 契約

先用 `s4-approval-template` 產生 [s4-deployment-approval.example.json](../samples/s4-deployment-approval.example.json) 同型的 approval 檔，再由具名人類檢查與核准：

- `selected_candidate_id`：S3 裡的其中一個候選。
- `lineage`：這一次 S1、S2、S3 artifact 的絕對或可解析路徑。S4 會重新讀取、核對 stage、run ID、candidate ID，並記錄 SHA-256。
- `approved_by`：具名核准人。
- `deployment_authorized: true`：看過 Skill 3 結果後的明確部署核准。
- `region_warning_acknowledged: true`：只有 S3 為 `region_unknown` 且核准人仍同意在目標 Region 測試時才可設為 true。

Region、profile、recipe 成功標準與 cleanup scope 由系統提供預設。若 Skill 3 已建立可稽核報價，S4 會使用其中的預期成本與建議核准上限；人工可覆寫成更嚴格的上限。有效成本上限一律取 Skill 3 建議、人類核准與內建 sandbox ceiling 三者最小值。固定 USD 3 是 sandbox policy ceiling，不是 AWS 報價。`--execute`、Console review 與 cleanup 仍不可省略。

部署前請先在 S3 artifact 檢查：

- `cost_estimate.status=estimated`
- `cost_estimate.quote.quote_id`
- `cost_estimate.quote.estimated_range_usd`
- `cost_estimate.quote.recommended_approval_ceiling_usd`
- 報價是否仍在 `valid_until` 內

## 3. 命令順序

```powershell
Set-Location C:\Users\youhs\Documents\實習專案\radar-redesign

# 只產生、檢閱 deployment context；不會建立 AWS 資源。
python -m agentic_cloud_radar.cli s4-approval-template `
  --input .\out\run\s3.json `
  --selected-candidate-id "<candidate-id>" `
  --approved-by "Cleo" `
  --authorize `
  --output .\out\run\s4-approval.json

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

# 產生本次 Infrastructure Composer 截圖與人工確認清單；不會 cleanup。
python -m agentic_cloud_radar.cli s4-console-review-packet `
  --input .\out\run\s4-runtime.json `
  --review-timeout-minutes 60 `
  --output .\out\run\s4-console-review-packet.json

node .\scripts\s4-capture-infrastructure-composer.mjs `
  --runtime .\out\run\s4-runtime.json `
  --packet .\out\run\s4-console-review-packet.json `
  --output-dir .\out\run\s4-console-review `
  --evidence-output .\out\run\s4-console-review-evidence.json `
  --shared-via conversation

# Codex 將 Playwright 截下的 Infrastructure Composer canvas PNG
# 顯示到 GUI 或這段對話供 Cleo 確認後，才執行這個單一 close 指令。
python -m agentic_cloud_radar.cli s4-close `
  --input .\out\run\s4-runtime.json `
  --packet .\out\run\s4-console-review-packet.json `
  --review-evidence .\out\run\s4-console-review-evidence.json `
  --confirmed-by "Cleo" `
  --shared-via conversation `
  --notes "Infrastructure Composer screenshot reviewed; cleanup approved." `
  --execute `
  --output .\out\run\s4-runtime-cleaned.json

# Skill 5 final report 要讀 cleanup 後的 runtime。
python -m agentic_cloud_radar.cli s5 `
  --s1 .\out\run\s1.json `
  --s2 .\out\run\s2.json `
  --s3 .\out\run\s3.json `
  --s4 .\out\run\s4.json `
  --runtime .\out\run\s4-runtime-cleaned.json `
  --output .\out\run\s5-report.json `
  --markdown-output .\out\run\s5-report.md
```

## 4. S3 Files recipe 實際做什麼

1. 用 run ID 衍生 stack name 與 resource prefix。
2. 呼叫既有 CDK app synth 出 CloudFormation template，並以 CloudFormation `create-stack` 部署。
3. 讀取 stack outputs，在測試 bucket 放一個非敏感檔案。
4. 等待 EC2 的 SSM Online，透過 SSM 確認 S3 Files mount、讀取 S3 放入的檔案、寫回 mount。
5. 由 S3 讀回 mount 寫入的檔案，建立雙向驗證。
6. runtime artifact 停在 `awaiting_console_review`，不能直接 cleanup。
7. Codex 依 packet 呼叫 Playwright，開啟可見瀏覽器進 AWS Console / CloudFormation / **Infrastructure Composer**，截取中間 canvas PNG，並在 GUI 或對話中交由具名人類確認。
8. 明確確認後，`s4-close --execute` 先清空此 stack 的 versioned test bucket，再刪除 stack 並等 CloudFormation deletion 完成。
9. 只有 `cleanup_verified`、Infrastructure Composer 截圖 metadata 與 `display_channel_confirmed` 都齊全的新版 runtime，可讓 Skill 5 寫出實際 PoC 的 `final` 結論。

runtime artifact 只保存 lineage、狀態、recipe、驗證結果與 cleanup 狀態；不保存 AWS account ID、ARN、IP 或 SSM command output。

Console 截圖不要放進 Git；Playwright 會先隱藏 Console chrome，再截取中間 canvas，對遮蔽後 PNG 算 SHA-256，最後才顯示給人類。`samples/s4-console-review-evidence.example.json` 的 metadata 契約記錄受保護的參照、SHA-256、截圖時間、run-derived stack name、Region 與 capture 時宣告的展示管道；關閉時的 `--shared-via` 才是 `display_channel_confirmed`。程式只驗 metadata 與 packet binding，不會自動判讀圖片內容；完整人機流程請使用 `skills/validate-cloud-poc/templates/console-review-agent-template.md`。

## 5. 逾時、部署失敗與 cleanup 失敗

若 runtime 長時間停在 `awaiting_console_review`，或因 deployment / cleanup 失敗而無法走正常截圖確認，優先避免付費資源失控：

```powershell
python -m agentic_cloud_radar.cli s4-abort `
  --input .\out\run\s4-runtime.json `
  --packet .\out\run\s4-console-review-packet.json `
  --confirmed-by "Cleo" `
  --reason "Console review timed out; emergency cleanup approved for cost control." `
  --execute `
  --output .\out\run\s4-runtime-aborted.json
```

這條路徑會在 runtime 標示 `skipped_for_cost_control` 與 `abort_without_console_review`，不可被寫成正常 Console-reviewed final。若 cleanup 仍失敗，CLI 會把 `cleanup_failed` runtime 寫到 output，保留錯誤與殘留資源風險供後續處理。

## 6. Lambda self-managed S3 code storage recipe

Lambda recipe 只使用這次 run 衍生名稱的測試資源：一個版本化、加密且封鎖公開存取的 S3 bucket；一個在 CloudFormation 內上傳非敏感 `.zip` 的 custom resource；以及一個 `AWS::Lambda::Function`。目標函數的 `Code` 會明確寫入 `S3ObjectStorageMode: REFERENCE`、S3 key 與 S3 object version，並以 bucket policy 只讓 Lambda service principal 讀取該 object version。

S4 部署後會檢查 CloudFormation output 的 `REFERENCE` 與 S3 version，再 invoke 函數，要求其回傳本次 run ID 和 `storage_mode=REFERENCE`。這代表 CloudFormation 接受了 reference mode，且函數可由 self-managed S3 code 啟動。cleanup 仍先清空這個 stack 的 versioned bucket，再刪除整個 stack。
