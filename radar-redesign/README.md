# Agentic Cloud Radar

這個原型把雲端技術探索拆成五個可重用 Skills：S1 Scan、S2 Compare、S3 Evaluate、S4 Validate、S5 Report。五個階段皆有本機 CLI、artifact contract 與測試；正式 Skill 入口位於 [`skills/`](./skills/)，共用 `agentic_cloud_radar/` 核心，不複製或改寫執行邏輯。

## 五個正式 Skills

| Skill | 入口 | 責任 |
|---|---|---|
| Skill 1 Scan | [`scan-cloud-technologies`](./skills/scan-cloud-technologies/SKILL.md) | 掃描可信公開來源、清理雜訊並建立可追溯候選。 |
| Skill 2 Compare | [`compare-cloud-candidates`](./skills/compare-cloud-candidates/SKILL.md) | 建立證據提案卡與比較矩陣，準備人工 shortlist。 |
| Skill 3 Evaluate | [`evaluate-cloud-candidate`](./skills/evaluate-cloud-candidate/SKILL.md) | 依固定 rubric 評估人工選定候選，保留證據限制。 |
| Skill 4 Validate | [`validate-cloud-poc`](./skills/validate-cloud-poc/SKILL.md) | 執行低風險驗證或具人工核准、成本與 cleanup gate 的 PoC。 |
| Skill 5 Report | [`report-cloud-evidence`](./skills/report-cloud-evidence/SKILL.md) | 只依 S1-S4 artifact 產出 JSON、Markdown 與 GUI 報告。 |

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

它不自動選冠軍、不假裝已知公司痛點，也不自動開 PoC。人類可從有證據卡片的候選中選最多三項進 S3；正式付費 PoC 到 S4 才要求確認 target Region、成本、權限與 cleanup，若確認不了就降級為文件／本機／低風險驗證。

```powershell
python -m agentic_cloud_radar.cli s2 `
  --input .\out\s1-landscape.json `
  --output .\out\s2-landscape-proposals.json
```

## S3/S4：評估、受控部署與驗證

S3 只接受 S2 artifact 和 human shortlist request；沒有 shortlist 就會停在 `needs_human_shortlist`。S4 預設只建立低風險 validation artifact，不會建立 AWS 資源，也不會自動啟動付費 PoC。

S3 v2 將原本混在 `recommend_s4` 的決策拆開：`recommend_low_risk_validation` 判斷是否值得做文件／本機／validator 驗證，`eligible_for_paid_poc_review` 則獨立檢查公司問題脈絡、可用環境、禁止資料／權限、治理旗標與 Region 證據。舊 `recommend_s4` 暫時保留並只映射到低風險建議；S4 的付費 gate 不再依賴這個相容欄位。

```powershell
python -m agentic_cloud_radar.cli s3 `
  --input .\out\s2-landscape-proposals.json `
  --shortlist .\out\s3-local-shortlist-request.json `
  --output .\out\s3-local-evaluate.json

python -m agentic_cloud_radar.cli s4 `
  --input .\out\s3-local-evaluate.json `
  --output .\out\s4-local-validate.json
```

完整 PoC 使用另外三個明確命令，正常 `s4` 不會部署。`s4-deploy` 先產生 deployment context，只有 approval 具有完整 S1/S2/S3 lineage、指定 recipe、Region、成本、真人核准與 `deployment_authorized=true`，且命令再附 `--execute` 才能建立資源。部署後必須由人執行 `s4-console-review`，再用 `s4-cleanup --execute` 刪除該次 stack 與測試資料。已註冊的 recipe 是 S3 Files 與 Lambda self-managed S3 code storage；兩者都有 intern 非 production live PoC 證據。S3 Files 已完成 Console review 與 cleanup；Lambda 已部署並 invoke，已確認 CloudFormation 架構與 `CREATE_COMPLETE`，仍待儲存設定人工確認及 cleanup 決策。未註冊的候選會停在 `needs_poc_recipe`，不會套用別的模板。

## S5：證據報告

S5 只讀取同一 lineage 的 S1-S4 artifact 與可選 runtime evidence，輸出 JSON、Markdown 與 GUI model。缺少 artifact 或 `run_id` 不一致時標記為 `incomplete_artifacts`；只有 runtime 已記錄 `cleanup_verified` 才能產生 final report，其餘保持 interim。

```powershell
python -m agentic_cloud_radar.cli s5 `
  --s1 .\out\s1.json `
  --s2 .\out\s2.json `
  --s3 .\out\s3.json `
  --s4 .\out\s4.json `
  --runtime .\out\s4-runtime.json `
  --output .\out\s5-report.json `
  --markdown-output .\out\s5-report.md
```

## 檔案

- `agentic_cloud_radar/s1.py`：掃描與 URL 匯入。
- `agentic_cloud_radar/s2.py`：證據比較、候選提案卡、比較矩陣。
- `agentic_cloud_radar/s3.py`：固定 rubric 評估 human shortlist。
- `agentic_cloud_radar/s4.py`：低風險驗證 artifact 與 paid-PoC gate 檢查。
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
