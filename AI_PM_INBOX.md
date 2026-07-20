# AI PM 當日進度暫存

此檔只保存 17:00 前的原始證據，不是正式日誌。平日 17:00 排程完成統整後，將當日內容標記為已整理。

## 2026-07-15｜已統整至 `logs/daily/work-log-2026-07-15.md`

- 建立 Codex＋Git 的 AI PM 與跨電腦同步機制。
- 將 Notion 日誌模板與 7/13 日誌匯入 Git。
- 建立 private GitHub repository 與主管閱讀首頁，完成 push 並核對遠端 commit。
- Mentor 回饋：五個 Skill 指專案中的掃描、比較、評估、驗證與報告；新增五色儀表板、每日整數積分，並檢查每天工作是否能扣回各 Skill 的原始目標。
- 已新增平日 17:20 才產生正式日誌的規則；7/15 正式日誌暫不發布。
- GitHub 已新增 Private repository 內可直接閱讀的 `dashboard/README.md`，包含五個 Skill 累積分數、每日趨勢與可展開日期區塊；commit `d42c9b8` 已推送至 `origin/main`。
- Notion 已在 `Cleo的暑期實習日誌(2026CIP)` 每日資料加入五個 Skill 整數積分與自動加總欄位，並完成 7/13、7/14 分數回填。
- 原本位於工作區外層的 Notion 儀表板頁已移入 Cleo 日誌資料庫，新增 `📊 儀表板入口` 檢視；原始積分明細資料庫仍保留作為證據來源。
- 將 Notion 畫面使用的完整互動式 Skill 儀表板同步加入 GitHub，固定入口為 `dashboard/cleo-skill-dashboard.html`。
- 檢查 `雷達-v3-手動部署包.zip`：7 個 Lambda Python 套件與 Lambda policy、Step Functions policy、state machine definition 均通過離線語法檢查；程式碼保留單一入口、全候選走完五步驟後依平均分選 Top 3，GCP／Azure 比較僅出現在最終報告。
- 使用公司帳戶有效 CLI 身分在 `ap-southeast-1` 實查部署前置條件；Lambda、Step Functions、IAM、DynamoDB、Secrets Manager 與 S3 讀取／列舉皆被 Organizations SCP `explicit deny`，手動 Console 部署目前同樣受阻，需請 AWS 管理者調整 SCP、提供部署角色或代為部署。
- 手動包預期名稱的 S3 bucket 實查為不存在；原先回報已建的 S3／DynamoDB／Secret 尚待權限開通後核對實際名稱與設定，不列為已驗證部署成果。
- 手冊與 state machine definition 有一項驗證落差：`GenerateRunId` 會以執行開始時間覆蓋輸入的 `manual-demo-001`，因此 S3 輸出資料夾會是時間字串，不是手冊範例名稱。
- 使用者在公司 AWS Console 建立 `cathay-techintel-v3-lambda-policy` 時遇到 `The policy failed legacy parsing`；對照 `lambda-execution-policy.json` 判斷高機率是 `ACCOUNT_ID_HERE` 未完全替換為 12 碼帳號，或 S3 bucket/object 權限混在同一 statement 造成 IAM Review 警告，已提供拆分 S3 `ListBucket` 與物件讀寫權限的可貼上修正版 policy。
- 使用者回報已在公司 AWS Console 完成第 4 章 DynamoDB Table 建立：Table name `cathay-techintel-v3-picks-log`、Partition key `run_id` (String)、Sort key `pick_time` (String)、Capacity mode `On-demand`、Encryption 使用預設 Amazon DynamoDB owned key；此為部署進度證據，仍待權限允許後核對 Console/CLI 實際狀態。
- 使用者補充第 4 章之前的手動部署步驟也已完成，因此第 1 至第 4 章狀態記為使用者回報完成：Lambda 用 IAM policy、Lambda execution role、S3 bucket 與 lifecycle rule、DynamoDB table；此狀態仍待權限允許後核對實際資源。

### 17:20 後判定結果

- 對應 Skill：掃描 +2、比較 +2、評估 +2、驗證 +3、報告 +5。
- 積分：當日總分 +14，累積總分 49。
- 目標對齊：直接扣回五個 Skill 目標。

## 2026-07-16｜已統整至 `logs/daily/work-log-2026-07-16.md`

- 使用者更新 AI PM 規則：自 2026-07-16 起，平日正式日誌統整時間改為 Asia/Taipei 17:00；每日正式日誌後需同步更新 GitHub／HTML 互動儀表板與 Notion 儀表板。
- 補完 2026-07-15 正式日誌收尾：原先回驗 Notion 主日誌 `7/15` 五個 Skill 分數為掃描 +3、比較 +3、評估 +3、驗證 +6、報告 +8；原始 Skill 明細資料庫回驗為 5 筆、合計 23 分。使用者指出分數偏鬆，後續已改用嚴格標準修正。
- 準備將 2026-07-15 工作日誌、GitHub 閱讀首頁、Skill 積分檔與 dashboard 資料 commit/push，作為昨日工作成果的 Git checkpoint。
- 依使用者回饋修正 2026-07-15 Skill 分數：掃描 +2、比較 +2、評估 +2、驗證 +3、報告 +5，合計 14；主要理由是 Console 手動部署第 1 至第 4 章屬於必要但簡單的操作，且公司 AWS 資源狀態仍待權限允許後獨立核對，不應以高分里程碑計算。
- 使用者調整日誌偏好：每天不必刻意寫很多，做到哪寫到哪，避免為了完整感把日誌越寫越多。
- 依 `logs/daily/work-log-2026-07-13.md`、`logs/daily/work-log-2026-07-14.md`、`logs/daily/work-log-2026-07-15.md` 與本檔待統整證據，完成 `2026CIP_biweekly_worklog1_draft.docx` 雙週工作週誌草稿；措辭保留「個人 AWS 已驗證」、「公司帳戶使用者回報完成」、「仍待權限允許後核對」的區分，避免把尚未完成端到端測試的內容寫得過滿。
- 依使用者補充，將雙週誌第三項改為「專案進度同步、AI PM 儀表板與成果整理」，並寫入「為了同步專案進度，建立 AI PM 紀錄機制，串接 Git／GitHub、Notion 與本機日誌」；已另存 `2026CIP_OOO_雙週工作週誌1_草稿_AI_PM.docx`，避免覆蓋目前被 Word 開啟的舊草稿。
- 釐清手動部署第 5 章 Secrets Manager：若 7/14 舊版手動部署已建立同名 secret `cathay-techintel-v3/anthropic-api-key`，且位於同一帳號與 `ap-southeast-1`，目前不需要重建；可直接沿用同一 secret ARN，必要時只更新 secret value 為佔位符或正式 API key。若該 secret 已排程刪除，建議優先 Restore 取消刪除後沿用，避免同名 secret 在 recovery window 期間無法重新建立。未記錄任何 secret value。
- 使用者提供 AWS Secrets Manager 截圖作為第 5 章證據：Secret `cathay-techintel-v3/anthropic-api-key` 已存在於 `ap-southeast-1`，KMS key 為 `aws/secretsmanager`，ARN 顯示為 `arn:aws:secretsmanager:ap-southeast-1:092211181371:secret:cathay-techintel-v3/anthropic-api-key-Lhnx13`。畫面未顯示刪除排程；第 5 章可視為已找到既有 secret，後續只需確認 secret value 為佔位符或正式 API key，且不得在日誌中記錄密鑰值。
- 針對 Secrets Manager 範例程式碼與已完成部署步驟進行概念說明：範例區塊是給應用程式讀取 secret 的不同方式（Lambda extension、SDK、快取客戶端、EKS 等），不是手動部署時必須執行的額外步驟。已完成資源的角色可整理為：IAM policy/role 定義 Lambda 能做什麼、S3 保存輸入與輸出檔、DynamoDB 保存挑選紀錄、Secrets Manager 保存 Anthropic API key 且避免寫入程式碼或日誌。此說明可作為後續 final proposal「從照步驟部署進步到理解安全與資料流」的成長素材。
- 使用者完成第 6 章 Lambda Layer，AWS Console 顯示 `Successfully created layer cathay-techintel-v3-deps version 1`。使用者提供 Lambda Functions 清單，現有 3 個 function 為 `MAP_tagging-Function`、`aws-controltower-NotificationForwarder`、`StackSet-Password-Policy-CXL--PasswordPolicyLambda-...`，名稱均非 `cathay-techintel-v3-*` 前綴，判斷不屬於本專案第 7 章目標函式，且其中 Control Tower / StackSet 類名稱可能為公司治理資源，不應刪除。第 7 章應建立 7 個本專案 Lambda：S1/S2/S2b/S3/S4/S5/RecordHumanPick，並沿用 `cathay-techintel-v3-lambda-role` 與第 6 章 layer。
- 為支援第 7 章 Console 手動建立 Lambda，從 `radar-company-account-complete/radar/cdk/lambda_src` 產出 7 個可上傳 zip，位置為 `radar-company-account-complete/radar/manual-lambda-zips/`：`s1_scan.zip`、`s2_compare.zip`、`s2b_quote.zip`、`s3_evaluate.zip`、`s4_validate.zip`、`s5_report.zip`、`record_human_pick.zip`。已確認 `s1_scan.zip` 內容含 `s1_scan.py`、`common.py`、`pipeline_lib.py` 且不含 `__pycache__`，可供 `cathay-techintel-v3-s1scan` 上傳使用。
- 使用者回報第 7.1 第一個 Lambda `cathay-techintel-v3-s1scan` 已完成建立、上傳 `s1_scan.zip`、掛上 `cathay-techintel-v3-deps:1`、設定 handler、memory 與 timeout。後續需先補環境變數再測試，因 `common.py` 會在 import 時讀取 `BUCKET_NAME`；若缺環境變數，測試會直接失敗。
- 使用者回報第 7 章 7 個 Lambda Function 均已完成建立與設定，包含 code zip、handler、layer、memory/timeout 與共用環境變數；目前狀態視為「使用者回報完成，待 Step Functions 串接與端到端測試回驗」。7 個函式為 `cathay-techintel-v3-s1scan`、`cathay-techintel-v3-s2compare`、`cathay-techintel-v3-s2bquote`、`cathay-techintel-v3-s3evaluate`、`cathay-techintel-v3-s4validate`、`cathay-techintel-v3-s5report`、`cathay-techintel-v3-recordhumanpick`。
- Mentor 討論：AI PM 需要更嚴格，不能太鬆散。專案工作開始前需先定義屬於哪個 Skill 或動作、checkpoint、完成條件與驗證機制；每一步做完都要有驗證證據。較大的工作要有計畫型態與時間軸，若 checkpoint 或主管期待不清楚，AI PM 可以主動反問後再執行。此規則已更新到 `PROJECT_MEMORY.md` 與 `AI_PM_WORKFLOW.md`。
- 第 9 章 Step Functions checkpoint：本機封包未找到現成 `step-functions-definition.json`，已依 `radar-company-account-complete/radar/cdk/stacks/pipeline_stack.py` 的流程邏輯產出手動部署用 `radar-company-account-complete/radar/manual-step-functions/step-functions-definition.json`。已用 PowerShell `ConvertFrom-Json` 驗證 JSON 可解析，且確認無 `ACCOUNT_ID_HERE`；流程包含 `GenerateRunId`、`Task_S1`、`Task_S2`、`Task_Quote`、`QuoteApproved?`、`OverBudget_RubricMode`、`Task_S3`、`Task_S4`、`Task_S5`，引用 6 個主流程 Lambda，不含 `recordhumanpick`。另補產 `stepfunctions-execution-policy.json`，包含 Lambda invoke 與 Step Functions logging 所需 CloudWatch Logs 權限。
- 使用者建立 Step Functions state machine 時，Design 圖已正確顯示主流程與 quote choice 分支，但按 Create 後出現 `AccessDeniedException: The state machine IAM Role is not authorized to access the Log Destination`。判斷為 `cathay-techintel-v3-sfn-role` 尚缺 CloudWatch Logs delivery/resource policy 相關權限；下一步需更新或新增 inline policy，補上 `logs:CreateLogDelivery`、`logs:PutResourcePolicy`、`logs:DescribeLogGroups` 等權限後再重試建立。
- 第 10 章第一次手動執行：State machine `cathay-techintel-v3-pipeline` 可啟動，`GenerateRunId` 成功，但 `Task_S1` 失敗並顯示 `ParamValidationError`。初步判斷高機率是 S1 Lambda 的環境變數，尤其 `BUCKET_NAME` 參數格式錯誤（例如填成 S3 ARN、空值或 key/value 放反），導致 S1 寫入 S3 `put_object` 時參數驗證失敗。下一步需查看 Cause 並核對 `cathay-techintel-v3-s1scan` 的 environment variables。
- 第 10 章第二次手動執行 `manual-demo-002`：`BUCKET_NAME` 格式問題已修到可通過參數驗證，但 `Task_S1` 在寫入 `s1_scan.json` 時出現 `AccessDenied`，原因為 `cathay-techintel-v3-lambda-role` 沒有 `s3:PutObject` 到 `arn:aws:s3:::cathay-techintel-v3-data-092211181371/runs/...` 的 identity-based policy。已產出 `radar-company-account-complete/radar/manual-step-functions/lambda-execution-policy.json`，包含 S3 讀寫、DynamoDB pick log、Secrets Manager read 與 CloudWatch Logs 權限，供更新 Lambda execution role 使用。
- 第 10 章 redrive 後，使用者貼出 Step Functions output：`Task_S1`、`Task_S2`、`Task_Quote` 均成功，S1 kept_count 29，S2 kept_count 6，Quote decision 為 `approve`，total_usd 為 `0.0892`，max_run_usd 為 `0.5`；目前已通過檢查清單中的 Quote 閘門 approve 與估價約 $0.089。實際 run_id 被 `GenerateRunId` 轉為 `2026-07-16T06-45-13.905Z` / S3 key 使用 `2026-07-16T06-45-13.905Z`（冒號轉 hyphen），後續驗證 S3 路徑應查 `runs/2026-07-16T06-45-13.905Z/`。

### 2026-07-16 15:01 Step Functions redrive 部分通過證據

- 使用者貼上 Step Functions redrive 後的執行輸出，確認 `Task_S1`、`Task_S2`、`Task_Quote` 都回傳 `StatusCode: 200`。
- S1 輸出：`runs/2026-07-16T06-45-13.905Z/s1_scan.json`，`kept_count=29`。
- S2 輸出：`runs/2026-07-16T06-45-13.905Z/s2_compare.json`，`kept_count=6`。
- Quote 輸出：`runs/2026-07-16T06-45-13.905Z/quotation.json`，`decision=approve`，`total_usd=0.0892`，`max_run_usd=0.5`。
- 下一個 checkpoint：確認 `Task_S3`、`Task_S4`、`Task_S5` 全綠，並到 S3/DynamoDB 驗證完整產出。

### 2026-07-16 15:05 Step Functions Task_S3 失敗待排查

- 使用者確認先前 `BUCKET_NAME` trailing space 問題已排除，且 Step Functions 圖上 `GenerateRunId`、`Task_S1`、`Task_S2`、`Task_Quote`、`QuoteApproved?` 已通過。
- Redrive 後 `Task_S3` 仍失敗；事件列表顯示第一次 `Task_S3` 在 14:58:38 failed，第二次 redrive 從 `Task_S3` 開始，於 15:03:01 failed。
- 下一個 checkpoint：取得 `Task_S3` 的 `Error` / `Cause` 或 CloudWatch Lambda log，以判斷是 Lambda timeout、Secrets Manager/S3/DynamoDB 權限、Anthropic key placeholder、或程式資料格式問題。

### 2026-07-16 15:10 Task_S3 失敗原因定位

- 使用者貼上 `Task_S3` error/cause：`AuthenticationError`，Anthropic API 回傳 `401 invalid x-api-key`。
- Stack trace 顯示錯誤發生在 `s3_evaluate.py -> llm_override -> call_anthropic -> anthropic_client().messages.create`，代表 `USE_ANTHROPIC=true` 時程式確實進入 LLM override 流程。
- 判斷：Secrets Manager 目前仍是 placeholder 或非有效 Anthropic API key，導致非 rubric-only 路徑嘗試呼叫 Anthropic 失敗。下一步若尚未取得公司核准 API key，應將相關 Lambda 的 `USE_ANTHROPIC` 調為 `false` 以驗證 rubric-only demo；若已有正式 key，則更新 Secrets Manager secret value，不能把 key 貼進聊天或日誌。

### 2026-07-16 15:18 API-first fallback 程式修正

- 依使用者要求，改成「有有效 Anthropic API key 就先用 API；key 缺失、placeholder、401 invalid key 或 Anthropic 呼叫失敗時，自動降級 rubric-only，避免 Step Functions 在 S3/S4 中斷」。
- 修改 `radar-company-account-complete/radar/cdk/lambda_src/common.py`：Secret value 會 strip 並辨識 placeholder；`call_anthropic` 捕捉 Anthropic 呼叫例外並記錄 `fallback_count` / `fallback_errors`；發生錯誤時清掉 key/client cache，方便後續更新 Secret 後重新讀取。
- 修改 `s3_evaluate.py`、`s4_validate.py`：輸出 `mode` 依實際 LLM 呼叫結果標註，例如 `api.anthropic.com`、`api.anthropic.com-partial-with-rubric-fallback`、`rubric-only (anthropic failed; fallback used)`。
- 驗證：`python -m py_compile` 通過；重新產生 `manual-lambda-zips` 下 7 個 Lambda zip；檢查 `s3_evaluate.zip` 內含新版 `common.py` / `s3_evaluate.py` 且未包含 `__pycache__`。

### 2026-07-16 15:25 Task_S5 handler 設定錯誤

- 使用者 redrive 後 Step Functions 圖顯示 `Task_S3`、`Task_S4` 已通過，表示 API-first fallback 修正已讓評估與驗證階段繼續執行。
- `Task_S5` 失敗原因：`Unable to import module 'lambda_function': No module named 'lambda_function'`。
- 判斷：`cathay-techintel-v3-s5report` 的 Lambda Handler 仍為 AWS 預設 `lambda_function.lambda_handler`，需改成 `s5_report.handler` 後 redrive。

### 2026-07-16 15:35 Step Functions 全流程成功

- 使用者完成 S5 handler 修正並 redrive，Step Functions 圖顯示 `GenerateRunId`、`Task_S1`、`Task_S2`、`Task_Quote`、`QuoteApproved?`、`Task_S3`、`Task_S4`、`Task_S5` 全部綠色成功。
- 這是 v3 company-account manual deployment 的第一次端到端成功執行。下一個 checkpoint：到 S3 驗證 run folder 產出 9 個檔案，並到 DynamoDB 驗證 AI pick log。

### 2026-07-16 15:55 HR 雙週誌格式修正

- 使用者指出先前產出的雙週工作週誌格式錯誤，並提供 HR 原始範本 `C:\Users\youhs\Downloads\2026CIP_OOO_雙週工作週誌1.docx`。
- 重新以 HR 原始範本為底，不重建版面；填入基本資料 `王冠婷／雲端技術發展部／雲端應用開發科`。
- 將內容壓回原始表單的 3 個工作列，並把建議內容與心得放回範本原本的合併儲存格列。
- 輸出 `2026CIP_王冠婷_雙週工作週誌1_格式正確版.docx`；結構檢查確認仍為 2 張表，工作進度表為 6 列 3 欄，最後兩列維持 `gridSpan=3` 合併欄。

### 17:00 後判定結果

- 對應 Skill：掃描 +3、比較 +3、評估 +5、驗證 +7、報告 +5。
- 積分：當日總分 +23，累積總分 72。
- 目標對齊：直接扣回五個 Skill 目標。

## 2026-07-17｜已統整至 `logs/daily/work-log-2026-07-17.md`

- 使用者決定因 CDK deploy 卡在公司 Organizations SCP（`ssm:GetParameter` 讀取 `/cdk-bootstrap/hnb659fds/version` 被 explicit deny），改採純 CloudFormation 方案以避開 CDK bootstrap / asset publishing roles。
- 已新增 `radar-company-account-complete/radar/manual-cloudformation/cathay-techintel-v3.yaml`，作為 `ap-southeast-1` 專用 CloudFormation template；內容建立 S3 data bucket、DynamoDB pick log、可選 Secrets Manager secret、Lambda execution role、Lambda layer、7 個 Lambda function、Step Functions state machine、CloudWatch log groups 與預設 disabled 的 EventBridge Scheduler。
- Template 設計改用 `ArtifactBucket`、`LambdaCodeS3Key`、`LambdaLayerS3Key` 參數承接已上傳的 Lambda source zip 與 dependency layer zip，不依賴 CDK bootstrap bucket、`cdk-hnb659fds-*` roles 或 `/cdk-bootstrap/.../version`。
- 已新增 `radar-company-account-complete/radar/manual-cloudformation/README.md`，整理本機打包 `lambda-code.zip` / `lambda-layer.zip`、上傳 S3 artifact bucket、以 `aws cloudformation deploy` 部署、以及手動啟動 Step Functions 的指令。
- 靜態檢查：template 檔案存在，未出現 `CDKToolkit`、`cdk-hnb659fds`、`cdk-bootstrap`、`AWS::CDK`、`us-east-1` 或 tab；明確含 `ap-southeast-1` Region guard。AWS 端 `aws cloudformation validate-template` 因公司 SCP explicit deny `cloudformation:ValidateTemplate`，尚無法由目前 `cleo` 身分完成雲端驗證。
- 使用者指出 2026-07-16 Notion 日誌過於粗略；已核對 Git 正式日誌 `logs/daily/work-log-2026-07-16.md` 與 Notion 頁面 `7/16`。
- 修正 Notion `7/16` 主日誌內容：補回今日主題、完成事項、執行驗證、Skill 進度與積分、流程圖、Mentor 討論筆記、問題處理、技術調整、提醒事項與今日總結。
- 修正 Notion `7/16` 屬性欄位：副標題、今日備註與總結、Mentor 討論關鍵字，以及 Skill 分數。分數改為掃描 +3、比較 +3、評估 +5、驗證 +7、報告 +5，合計 23 分，與 Git 正式日誌一致。
- 回讀 Notion 頁面確認更新已生效；後續若正式統整 2026-07-17 日誌，可把此項列為 AI PM／報告品質修正，不額外計入 7/16 專案執行分數。
- 回應使用者「目前專案如何從 40/55 分架構推到 95 分」的策略問題：已重讀 `PROJECT_MEMORY.md`、`logs/daily/work-log-2026-07-16.md`、`radar-company-account-complete/radar/architecture-scan/architecture_scan.md` 與 `pipeline-architecture.md`，並查詢 AWS Well-Architected、Serverless Lens、Bedrock Guardrails／Evaluation／Prompt Management／Prompt Routing、Step Functions human approval、Powertools、Cost Anomaly Detection、NIST AI RMF、OWASP LLM Top 10、ISO/IEC 42001、Thoughtworks／Zalando Tech Radar 等資料。初步判斷：核心流程已接近完成，後續高分方向應轉向「決策治理層、可解釋證據圖、human-in-the-loop、評估基準、觀測與成本治理、雷達產品化 UI／API、final proposal 成效證據」。
- 使用者決定先把三個高分升級加入系統：Evidence Ledger、Human Review Loop、Evaluation Harness。
- 已修改 `radar-company-account-complete/radar/cdk/lambda_src/pipeline_lib.py`：新增 evidence confidence、governance flags、Tech Radar ring、`build_evidence_ledger()`、`build_review_packet()`，並讓 HTML 報告顯示 Evidence Ledger 與 Human Review Gate 區塊。
- 已修改 `s5_report.py`：每次 S5 會額外輸出 `evidence-ledger.json` 與 `review-packet.json`，`s5_report.json` 會記錄對應 key 與 `human_review_status=awaiting_human_review`，DynamoDB AI pick log 也會保留 evidence/review artifact key。
- 已修改 `record_human_pick.py`：人類回饋從單純 `picked_ids` 擴充為 approve / reject / override / comment，並記錄 reviewer、human_minutes、blind、rationale、review/evidence artifact key。
- 已新增 `radar-company-account-complete/radar/tools/evaluation_harness.py`：用 packaged fixtures 離線 replay full flow，輸出 `benchmark-report.md/json`，檢查 Top 3、full-flow、source URL、evidence confidence、review packet 與 blocked Bedrock L0 規則。
- 已更新 `radar-company-account-complete/radar/README.md` 與 `DEPLOY.md`，補上三個升級的使用方式、S3 新輸出、human review payload 與 evaluation harness 指令。
- 已重新產生 `radar-company-account-complete/radar/manual-lambda-zips/` 下 7 個手動部署 zip；驗證 `s5_report.zip` 已含 `evidence_ledger_key` / `review_packet_key`，`record_human_pick.zip` 已含 approve/reject/override/comment 邏輯。
- 驗證：不寫 `.pyc` 的 source compile 通過 `pipeline_lib.py`、`s5_report.py`、`record_human_pick.py`、`evaluation_harness.py`；`python radar-company-account-complete/radar/tools/evaluation_harness.py --out radar-company-account-complete/radar/tools/out/benchmark` 通過，quality gate=pass，Top 3 為 A03、A04、A10。
- 使用者回報在 S3 Console 看不到報告；依截圖判斷 `report.html` 與 `evidence-ledger.json` 已成功產出於 `runs/2026-07-17T01-08-13.216Z/`，但目前停在 S3 object Properties 頁，且 bucket 為 private，直接開 Object URL 會受 bucket policy / Block Public Access 影響。處理建議：使用 Console 的 `Open` 或 `Download`，不要為了看報告改成 public；後續 human review payload 的 run_id 應改用實際 run id `2026-07-17T01-08-13.216Z`。
- 使用者提供下載後的 `C:\Users\youhs\Downloads\report.html`；已確認新版報告成功包含 `Evidence Ledger`、`Human Review Gate`、`awaiting_human_review`、Budget Quotation、Pipeline Funnel 與 Research disclosure。此 run 使用 RSS 真實來源，run id 為 `2026-07-17T01-08-13.216Z`，Top 3 IDs 為 `R-493965E0`、`R-07FA8EA4`、`R-28074DF1`。報告顯示 quote gate approve、估價 $0.0892，但實際 LLM token 為 0，代表本次仍是 fallback/rubric 路徑，不可敘述成真實 Anthropic API 評分已完成。
- 使用者追問「Algorithmic Decision Layer」與「多日 human feedback 統計」後，已實作第二批 Decision Intelligence 升級：`decision-layer.json`、`feedback-stats.json`、`audit-packet.json`。
- 已修改 `common.py` 新增 `read_pick_logs()` 與 Decimal 轉換，讓 S5 能掃描 DynamoDB `cathay-techintel-v3-picks-log` 的既有 AI/human logs 做輕量統計；已確認手動 Lambda policy 具備 `dynamodb:Scan`。
- 已修改 `pipeline_lib.py`：新增 `build_feedback_stats()`、`build_decision_layer()`、`build_audit_packet()`；決策層採可解釋 weighted policy，整合 average score、evidence confidence、enterprise case、evaluator/validator agreement、governance flags 與 human feedback signal，並明確標示這不是已訓練 ML 模型。
- 已修改 `s5_report.py`：每次 S5 會額外輸出 `decision-layer.json`、`feedback-stats.json`、`audit-packet.json`，並在 `s5_report.json` 與 Step Functions response 回傳對應 key。
- 已更新 `README.md`、`DEPLOY.md` 與 `evaluation_harness.py`；離線 harness 現在會驗證 decision layer、feedback sample size honesty 與 audit packet。
- 驗證：source compile 通過 `common.py`、`pipeline_lib.py`、`s5_report.py`、`evaluation_harness.py`；`python radar-company-account-complete/radar/tools/evaluation_harness.py --out radar-company-account-complete/radar/tools/out/benchmark` 通過，quality gate=pass。benchmark 顯示 decision layer Top 3 可與 raw average Top 3 不同，這是設計上用「可解釋決策分數」補強 raw score 的結果。
- 已重新產生 `manual-lambda-zips/` 下 7 個 zip，並驗證 `s5_report.zip` 含 `decision_layer_key`、`feedback_stats_key`、`audit_packet_key`。下一步若要在公司 AWS 驗證第二批升級，需重新上傳新版 `s5_report.zip` 後重跑 Step Functions。
- 使用者新增長期偏好：自 2026-07-17 起，AI 也要維護自己的每日執行軌跡，使用 Markdown，且不要寫成流水帳。已更新 `PROJECT_MEMORY.md` 與 `AI_PM_WORKFLOW.md`，並建立 `ai-execution-trace/daily/2026-07-17.md` 作為今日起始紀錄。
- 使用者進一步指定今日 AI 執行軌跡需每小時記錄一次，且這是 AI 自身的執行軌跡，不需要寫專案前情提要；同時要求把使用者日誌與 AI 執行軌跡分不同目錄保存，並推送到同一個 GitHub 專案。目錄規劃更新為 `logs/daily/` 保存正式每日實習日誌，`ai-execution-trace/daily/` 保存 AI 每小時執行軌跡。
- 已建立今天限定的每小時 heartbeat automation `2026-07-17-ai`，用於追加 `ai-execution-trace/daily/2026-07-17.md` 的當小時 AI 執行軌跡。
- 已將根目錄巢狀 `internship-tech-radar/` 加入 `.gitignore`，避免後續 commit 誤納入重複 repository。
- 目錄調整與 AI 執行軌跡已提交並推送到 GitHub `origin/main`，commit 為 `b2fdbb5 Organize logs and add AI execution trace`；遠端 `refs/heads/main` 已回報同一 commit hash。
- 使用者在專案根目錄重新執行 `aws cloudformation validate-template --profile intern --region ap-southeast-1 --template-body file://cloudformation/cathay-techintel-v3.yaml`；第一次仍顯示 SCP explicit deny，但第二次成功回傳 template Parameters，表示目前 CloudFormation template 已通過 AWS 端 validate-template。下一步需處理 artifact zip 上傳與既有同名資源衝突風險。
- 純 CloudFormation 部署第一次嘗試失敗，根因為 `PythonDependenciesLayer` 讀不到 `s3://cathay-techintel-v3-data-092211181371/artifacts/cathay-techintel-v3/lambda-layer.zip`（NoSuchKey），CloudFormation rollback 後已刪除 failed stack。
- 已從 `radar-company-account-complete/radar/cdk` 產出並上傳 `lambda-code.zip` 與 `lambda-layer.zip` 至 `s3://cathay-techintel-v3-data-092211181371/artifacts/cathay-techintel-v3/`。
- 重新部署 `cathay-techintel-v3-cfn` 成功，CloudFormation stack resources 全部 `CREATE_COMPLETE`，輸出包含 data bucket `cathay-techintel-v3-cfn-data-092211181371`、DynamoDB table `cathay-techintel-v3-cfn-picks-log` 與 state machine `arn:aws:states:ap-southeast-1:092211181371:stateMachine:cathay-techintel-v3-cfn-pipeline`。
- 已啟動 Step Functions execution `company-cfn-001`；狀態 `SUCCEEDED`，S1 kept_count=27，S2 kept_count=6，Quote decision=approve、total_usd=0.0892，S3 evaluated_count=6，S4 validated_count=6，S5 產出 `report.html`、`s5_report.json`、`evidence-ledger.json`、`review-packet.json`、`decision-layer.json`、`feedback-stats.json`、`audit-packet.json` 與 `cost-estimate.yaml`。未在日誌保存 presigned URL 或 token。
- 依使用者需求完成下週部會自我介紹簡報模板版，輸出 `outputs/部會自我介紹_王冠婷_模板版.pptx`，共 4 頁：個人背景、CIP 實習計畫摘要、下班後日常、基隆口袋地圖。
- 使用者要求不要 AI 圖，因此最終模板版只沿用 `C:\Users\youhs\Downloads\IT簡報模板_v2.6_fin.pptx` 的公司模板風格與內建視覺元素，未插入先前生成的 AI 圖片。
- 驗證：以純英文暫存檔重跑 `slides_test.py`，結果 `Test passed. No overflow detected.`；正式 PPTX 也已用 `render_slides.py` 渲染，並人工檢視第 1 至第 4 頁，確認中文字、模板 logo、卡片與頁面版面正常。模板內建 EMF 圖像曾在 artifact-tool 匯出時提示 unsupported，但正式渲染結果可見模板 logo 與視覺元素。
- 候選分類：偏報告／對外溝通支援；主要支援 CIP 部會 onboarding 與個人介紹，不直接計入技術雷達核心五 Skill，正式 17:00 統整時再決定是否記為支援性成果。
- 使用者更新下週部會自我介紹簡報需求：改為 7 頁，風格參考 `C:\Users\youhs\Downloads\Teal and grey Modern Pitch Deck Presentation.pdf`，首頁參考 `C:\Users\youhs\Downloads\Cleo.pdf`，並加入 AI PM、human-AI 角色定義、agentic organization 與人的工作軌跡／AI 執行軌跡。
- 已完成新版 7 頁簡報 `outputs/部會自我介紹_王冠婷_AI_PM_7頁版.pptx`：第 1 頁首頁、第 2 頁個人背景、第 3 頁實習專案目標、第 4 頁 AI PM 角色、第 5 頁人與 AI 角色邊界、第 6 頁 agentic organization、第 7 頁下班後生活與基隆口袋地圖。
- 內容壓縮策略：把 `AGENTS.md` 與 `AI_PM_WORKFLOW.md` 的工程規則轉成中文簡報語言，將 AI PM 定義為「質詢者、協作者、紀錄者、協調者」，並強調人類與 AI 互補、不互相取代。
- 視覺處理：將 `Cleo.pdf` 首頁照片裁成左右視覺欄，其他頁採 teal/grey pitch deck 的大標、灰綠幾何背景、圓角資訊框與低密度排版。
- 驗證：以純英文暫存檔執行 `slides_test.py` 通過，結果 `Test passed. No overflow detected.`；再用 `render_slides.py` 渲染 7 頁並人工檢視第 1、3、4、5、6、7 頁，修正第 3 頁 `Compare` 英文換行後重新匯出。
- 候選分類：對外溝通／報告支援，支援 CIP 部會 onboarding 與 AI PM 概念說明；除非 17:00 統整時另有專案核心證據，不建議計入技術雷達核心五 Skill 分數。

### 17:00 後判定結果

- 對應 Skill：掃描 +4、比較 +5、評估 +8、驗證 +9、報告 +7。
- 積分：當日總分 +33，累積總分 105。
- 目標對齊：直接扣回五個 Skill 目標；部會自我介紹簡報屬報告／溝通支援，不單獨提高核心 Skill 分數。
- 同步項目：已建立 Git 正式日誌、補回 7/13 至 7/16 AI 執行軌跡日總結，並更新 Git 版 Skill 儀表板資料。

## 2026-07-20｜17:00 前暫存

- 使用者要求延續今日建議的三項工作：整理 final proposal 的 7/17 成果素材、補專案執行軌跡圖、建立 demo checklist。
- 已新增 `final-proposal/7-17成果素材.md`，把 7/17 CloudFormation stack、Step Functions `company-cfn-001`、Evidence/Review/Decision/Audit artifacts、evaluation harness、fallback/rubric 限制整理成可直接放進 final proposal 的素材。
- 已更新 `final-proposal/簡報架構與執行軌跡.md`，將原本停在公司帳戶手動部署的狀態，改成 CloudFormation 可重建部署、`company-cfn-001 SUCCEEDED` 與治理 artifacts 的最新軌跡。
- 已新增 `final-proposal/demo-checklist.md`，整理 demo 前檢查、展示路線、要打開的檔案、已驗證與待驗證限制；明確標示本次仍是 fallback/rubric 路徑，不可宣稱正式 Anthropic API 評分完成。
- 已建立 `ai-execution-trace/daily/2026-07-20.md`，記錄本小時 AI 執行軌跡。
- 已整理 AWS Kiro CLI / MCP / Bedrock AgentCore 相關範例報導候選，新增 `research/aws-new-tech-candidates-2026-07-20.md`；建議優先驗證 Kiro CLI + MCP 支援案件流程，因為可直接對應目前專案的 Evidence Ledger、Human Review Gate、Audit Packet 與 final proposal demo。
- 使用者新增長期限制：公司目前無法使用 Bedrock，因此日後新技術選題不主動推薦 Bedrock / Bedrock AgentCore 系列。已更新 `PROJECT_MEMORY.md` 與 `research/aws-new-tech-candidates-2026-07-20.md`，後續只保留 Bedrock 內容作為不採用原因或概念對照。
- 使用者釐清線上投保穩定性 PoC 應建立在既有雲端技術雷達之上：由雷達先搜尋與比較候選雲端技術、評估是否適合線上投保、產出報價，再進入測試與報告。已更新 `PROJECT_MEMORY.md`，並新增 `research/online-insurance-reliability-radar-poc.md` 作為設計草案。
- 使用者進一步定義技術雷達的第一層級：先由 GUI / 需求表單輸入應用端問題、舊方法限制、條件與成功標準，再啟動 S1-S5。已更新 `PROJECT_MEMORY.md` 與 `research/online-insurance-reliability-radar-poc.md`，將 S0 定義為 `Demand Input`，避免雷達無邊界掃描造成白做。
- 使用者指出自己不一定知道公司實際遇到什麼問題；已將技術雷達前置層補為 `S-1 Problem Discovery`，先以低侵入、非敏感來源整理問題候選，待人類確認後才進入 S0 需求卡，避免把推測當成公司真實痛點。
- 使用者詢問 S0 是否需要導入 LLM API key 對外搜尋；已決定 S0 不直接外搜，只可選擇性用 LLM 協助需求整理、追問缺漏與敏感資訊檢查。真正外部搜尋與技術蒐集放在 S1，且需等 S0 需求卡經人類確認後才啟動；API key 必須只放後端或 Secrets Manager。
- 已執行線上投保穩定性 S1 網路掃描，查找 AWS Blog、AWS 官方文件與 GitHub 類似案例；新增 `research/online-insurance-reliability-s1-scan-2026-07-20.md`。初步判斷最值得借鏡的是 CloudWatch Synthetics / Playwright canary + incident evidence，Application Signals / Resilience Hub / FIS 作為後續有內部架構權限時的第二階段。
- 已完成線上投保穩定性黑箱 PoC 第一版：新增 `poc/online-insurance-reliability/`，包含 mock 線上投保服務、synthetic canary、README 操作步驟與本機驗證輸出；驗證矩陣確認 `normal=PASS`，`quote_500`、`confirmation_timeout`、`frontend_js_error` 均為預期 `FAIL`，並產出 Markdown report 與 incident packet JSON。
- 使用者確認 S2 比較標準「是否可黑箱驗證、不碰 PII、不需完整內部架構、能產 incident packet、可估成本、可延伸 AWS」方向可用；已新增 `research/online-insurance-reliability-s2-compare-2026-07-20.md`，將候選技術評分並選出第一階段主方案：CloudWatch Synthetics / Playwright journey canary、multi-step API canary、EventBridge + Lambda incident packet。
- 使用者表示現在可用 CLI；已用 `intern` profile 驗證 AWS CLI 可查詢 Price List API，新增 `research/online-insurance-reliability-s2b-quote-2026-07-20.md`。Tokyo 估算結果：低頻驗證版約 US$6.09/月、正式起步版約 US$37.45/月、高頻強化版約 US$263.25/月；未保存帳號 ARN、account id、憑證或 API key。
- 使用者詢問目前做到哪，以及沒有 AWS 權限如何測試；已新增 `research/online-insurance-reliability-s3-evaluate-2026-07-20.md`。文件明確區分本機功能驗證、AWS CLI 定價查證、AWS 正式部署待驗證與真實投保流程待確認；S3 加權評估為 4.35/5，建議進入下一階段但先採低頻驗證版或正式起步版。
- 使用者要求教學如何部署到 AWS；已新增 `poc/online-insurance-reliability/aws-deploy-guide.md` 與 Playwright canary 範例 `poc/online-insurance-reliability/aws/canary/insurance_journey_canary.js`。已用 CLI 查證 `ap-southeast-1` 可用 Playwright runtime（例如 `syn-nodejs-playwright-7.1`），部署教學採 Console first，明確提醒 AWS canary 不能直接打本機 localhost，需公司 sandbox/test endpoint 或先部署 mock endpoint。
- 使用者與 mentor 決定暫停保單系統測試與 S0 建置，改為深化 S1-S5 核心能力；已完成 S3 Files 新聞截斷測試報告 `research/s3-files-s1-s5-evaluation-2026-07-20.md`。驗證證據：官方 AWS News / S3 Files 文件已查證，CLI 已確認 `aws s3files` command group、`create-file-system` / `create-mount-target` schema，且 `aws s3files list-file-systems --profile intern --region ap-southeast-1` 回傳空清單；未建立任何 AWS 資源。
