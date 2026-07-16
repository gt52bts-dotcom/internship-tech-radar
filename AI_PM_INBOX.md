# AI PM 當日進度暫存

此檔只保存 17:20 前的原始證據，不是正式日誌。平日 17:20 排程完成統整後，將當日內容標記為已整理。

## 2026-07-15｜已統整至 `work-log-2026-07-15.md`

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

- 對應 Skill：掃描 +3、比較 +3、評估 +3、驗證 +6、報告 +8。
- 積分：當日總分 +23，累積總分 58。
- 目標對齊：直接扣回五個 Skill 目標。

## 2026-07-16｜待統整

- 補完 2026-07-15 正式日誌收尾：回驗 Notion 主日誌 `7/15` 五個 Skill 分數為掃描 +3、比較 +3、評估 +3、驗證 +6、報告 +8；原始 Skill 明細資料庫回驗為 5 筆、合計 23 分。
- 準備將 2026-07-15 工作日誌、GitHub 閱讀首頁、Skill 積分檔與 dashboard 資料 commit/push，作為昨日工作成果的 Git checkpoint。
