# Agentic Cloud Radar

這個原型把雲端技術探索拆成五個可重用 Skills：S1 Scan、S2 Compare、S3 Evaluate、S4 Validate、S5 Report。五個階段皆有本機 CLI、artifact contract 與測試；正式 Skill 入口位於 [`skills/`](./skills/)，共用 `agentic_cloud_radar/` 核心，不複製或改寫執行邏輯。

## 五個正式 Skills

| Skill | 入口 | 責任 |
|---|---|---|
| Skill 1 Scan | [`scan-cloud-technologies`](./skills/scan-cloud-technologies/SKILL.md) | 掃描可信公開來源、清理雜訊並建立可追溯候選。 |
| Skill 2 Compare | [`compare-cloud-candidates`](./skills/compare-cloud-candidates/SKILL.md) | 建立證據提案卡與比較矩陣，準備人工 shortlist。 |
| Skill 3 Evaluate | [`evaluate-cloud-candidate`](./skills/evaluate-cloud-candidate/SKILL.md) | 依固定 rubric 評估人工選定候選；已登錄 recipe 同時產出可稽核的 PoC 成本估算報價單。 |
| Skill 4 Validate | [`validate-cloud-poc`](./skills/validate-cloud-poc/SKILL.md) | 檢查 Skill 3 報價、人工核准、成本上限與 cleanup gate，並執行唯一的受控付費 PoC。 |
| Skill 5 Report | [`report-cloud-evidence`](./skills/report-cloud-evidence/SKILL.md) | 只依 S1-S4 artifact 產出含逐項報價與估算／實際帳務對帳的 JSON、Markdown 與 GUI 報告。 |

## 新入口與流程

```text
使用者貼 URL ──────────────────────> S1 URL Import ─> S2 Proposal Cards ─> S3

使用者要求掃描最新／GA 技術 ───────> S1 Discovery  ─> S2 Proposal Cards ─> S3
```

S0 不再是入口關卡。過去 S0 想做的事（問題、預期改善、成功條件、限制）已移進 S2，變成每一個 S1 候選各自的提案卡。這樣系統先認識真實技術，再問「它值得解哪個問題」，不會在還不知道候選之前先要求人填空泛需求。

## S1：真實候選蒐集

`s1` 是掃描入口，可帶可選的 scope hints，但不需要確認卡。它會讀 AWS Blogs 的即時分類目錄與 RSS，並在非 GA-only 模式下使用 GitHub Public Repository Search。

`s1-url` 是直接匯入入口。使用者已明確指定 URL，因此完全不經 S0；但仍檢查 HTTPS、受信任公開網域、redirect 與 HTML content type。目前允許 AWS、GitHub、GitLab、Codeberg。

```powershell
# 掃描跨領域技術；input 只放掃描範圍與 GA 等可選條件
python -m agentic_cloud_radar.cli s1 `
  --input .\out\landscape-request.json `
  --output .\out\s1-landscape.json

# 直接匯入一篇真正想看的文章；不經 S0
python -m agentic_cloud_radar.cli s1-url `
  --url "https://aws.amazon.com/blogs/aws/launching-s3-files-making-s3-buckets-accessible-as-file-systems/" `
  --output .\out\s1-s3-files.json
```

範例 scan request：

```json
{
  "discovery_scope": "landscape",
  "max_source_age_days": 3650,
  "max_candidates": 12,
  "maturity_requirement": "ga_evidence_required",
  "constraints": { "excluded_services": ["Bedrock"] }
}
```

## S2：候選提案卡與比較板

S2 不再只是補連結。它將每個可追溯候選做成 `proposal_card`，並建立固定欄位的 `comparison_matrix`：

- 技術範圍、交付型態、來源支持的能力與環境訊號。
- 改善假設與改善程度：只有來源有量化文字才標示為量化；否則明確標示為待驗證假設。
- 可能好處、規劃上的利弊、成熟度、文件／定價／區域證據與證據覆蓋率。
- 每個候選要先量的 before/after 指標、成功證據、stop conditions、下一個人工問題。
- Region 只作狀態標記：有功能級官方證據時標 `available_ap_southeast_1`，缺證據時標 `region_unknown` warning；它不再阻擋 S3 shortlist。

S2 先重新抓 S1 原始文章與其中候選相關連結，再用 AWS 的公開搜尋索引補找原文未連出的官方 docs／產品頁／公告。搜尋結果只用來發現 URL；每個 URL 都要重新抓取並通過「候選功能名稱與 Singapore 同段出現」的檢查，才會成為 Region 證據。

它不自動選冠軍，也不自動開 PoC。人類只要從有證據卡片的候選中選一項進 S3，不必另外填公司問題、使用環境或資料限制；Region 與定價缺口保留為提醒。

```powershell
python -m agentic_cloud_radar.cli s2 `
  --input .\out\s1-landscape.json `
  --output .\out\s2-landscape-proposals.json
```

## S3/S4：評估、受控部署與驗證

S3 只接受 S2 artifact 和單項 human selection request；沒有人工選定候選，或一次選超過一項，就會停在 `needs_human_shortlist`。S4 的 gate artifact 不會建立 AWS 資源，也不會自動啟動 PoC；Skill 4 本身只有一種含資源、可能產生成本的受控 PoC。

S3 v4 採公開證據模式：單項候選必須先產出完整 PoC 預估報價單。唯一決策欄位 `recommend_poc` 要求 5 分制加權分 `>= 3.75`、信心至少 `medium`、沒有 PoC blocker，且報價狀態為 `estimated`。這個欄位代表「技術上具備受控 PoC 資格」，不是公司工作負載適配性已驗證，也不是業務採用建議。Skill 4 只代表受控、會建立 AWS 資源的付費 PoC；Region 與定價不確定性會列在 `poc_review_notes`，但正式付費部署時 Region 必須可用，或由具名核准人在 approval 明確標示 `region_warning_acknowledged=true`。舊決策欄位只作讀取舊 artifact 的相容 fallback。

```powershell
python -m agentic_cloud_radar.cli s3 `
  --input .\out\s2-landscape-proposals.json `
  --shortlist .\out\s3-local-shortlist-request.json `
  --output .\out\s3-local-evaluate.json

python -m agentic_cloud_radar.cli s4 `
  --input .\out\s3-local-evaluate.json `
  --output .\out\s4-local-validate.json
```

完整 PoC 使用明確命令，正常 `s4` 不會部署。`s4-approval-template` 先從 Skill 3 artifact 產生 approval 檔，核准人再檢查候選、`deployment_authorized=true`、成本上限與 S1/S2/S3 artifact 路徑。若 Skill 3 有已登錄的成本模型，S4 會帶入報價單的預期總額與建議核准上限；有效上限一律取 Skill 3 建議、人類核准、內建 sandbox ceiling 三者最小值。命令仍須另附 `--execute` 才能建立資源。部署完成後，Codex 必須在 AWS Console 檢視 Infrastructure Composer、截圖並上傳 GUI 或對話供具名人類確認；`s4-close --execute` 必須同時讀 `s4-console-review-packet.json` 與 evidence JSON，才會自動清除該次 stack 與測試資料。若 review 逾時或失敗，`s4-abort --execute` 可在具名成本控制確認後執行緊急 cleanup，但 Skill 5 不會把它當成正常截圖確認。已註冊的 recipe 是 S3 Files 與 Lambda self-managed S3 code storage；未註冊候選會停在 `needs_poc_recipe`。

S3 Files 報價模型目前採新加坡區 AWS 公開牌價與三種用量情境：低用量 1 小時／0.02 GB、預期 2 小時／0.10 GB、高用量 4 小時／0.50 GB。報價逐項列出 EC2、EBS、S3 Files 儲存與資料操作、S3 Standard 儲存與 requests；有效期七天。它是靜態 rate card 估算，不是即時 AWS Pricing API 查價，也不是 AWS 帳單或正式採購報價。Skill 5 會另列「預估成本 vs 可歸因實際帳務成本」；若沒有 Cost Explorer、Billing 或 CUR artifact，實際成本固定標示 `pending`，不得由 runtime 反推。

## S5：證據報告

S5 只讀取同一 lineage 的 S1-S4 artifact 與可選 runtime evidence，輸出 JSON、Markdown 與 GUI model。缺少 artifact 或 `run_id` 不一致時標記為 `incomplete_artifacts`；只有 runtime 已記錄 `cleanup_verified` 才能產生 final report，新版 `s4.runtime-evidence.v3` 還必須有 Infrastructure Composer 截圖 metadata。其餘保持 interim 或 incomplete。

```powershell
python -m agentic_cloud_radar.cli s5 `
  --s1 .\out\s1.json `
  --s2 .\out\s2.json `
  --s3 .\out\s3.json `
  --s4 .\out\s4.json `
  --runtime .\out\run\s4-runtime-cleaned.json `
  --billing .\out\cost-explorer-attribution.json `
  --output .\out\s5-report.json `
  --markdown-output .\out\s5-report.md
```

`--billing` 是可選參數；帳務資料尚未可歸因時不要提供，報告會保留 `pending_actual_cost`。

## 範圍界線

這五個 Skill 是可重做的技術雷達流程包與 PoC 證據鏈，不是完整上線的 AWS 產品系統。Cognito/API Gateway、EventBridge、Step Functions、CloudWatch alarms、正式 CI/CD deployment、長期資料庫與權限治理屬於下一階段產品化架構，不能因為五個 Skill 可跑就宣稱已完成 production-ready 系統。

## 檔案

- `agentic_cloud_radar/s1.py`：掃描與 URL 匯入。
- `agentic_cloud_radar/s2.py`：證據比較、候選提案卡、比較矩陣。
- `agentic_cloud_radar/s3.py`：固定 rubric 評估 human shortlist。
- `agentic_cloud_radar/s4.py`：不建立資源的 approval gate 與簡化 PoC 檢查。
- `agentic_cloud_radar/s5.py`：artifact-only JSON、Markdown 與 GUI report renderer。
- `skills/`：五個可被 Codex 識別與重用的正式 Skill packages。
- `docs/s1-極細註解版.md`：S1 資料流與命令說明。
- `docs/s2-極細註解版.md`：S2 提案卡欄位與比較指標。
- `docs/s3-s4-極細註解版.md`：S3/S4 評分、降級與重跑方式。
- `docs/s1-s4-程式碼導讀與註解.md`：從 CLI、artifact 契約到 S4 外掛式 PoC 的程式碼閱讀地圖。
- `docs/s4-完整PoC部署操作.md`：完整 S4 的 approval、lineage、部署、Console 回驗與 cleanup 操作說明。

## 驗證

```powershell
python -m compileall agentic_cloud_radar
python -m unittest discover -s tests -v
```

PowerShell 5.1 用 `Set-Content -Encoding utf8` 產生 JSON 時可能加上 BOM；CLI 以 `utf-8-sig` 讀取 input，因此有 BOM 或無 BOM 都可讀取。
