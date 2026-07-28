# Agentic Cloud Radar

這個原型把雲端技術探索拆成五個 Skills：S1 Scan、S2 Compare、S3 Evaluate、S4 Validate、S5 Report。目前本機可執行 S1 與 S2；兩者只使用執行當下取得的公開資料，不使用 demo 文章、假 URL 或人工補寫的技術 metadata。

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
- 新加坡 `ap-southeast-1` 是硬門檻：只有有「特定功能」官方證據明確可在該 Region 使用的候選，才可進 S3 shortlist；只有服務 endpoint、沒有 feature-level 證據時仍不可考慮。

它不自動選冠軍、不假裝已知公司痛點，也不自動開 PoC。人類只能從新加坡合格候選中選最多三項進 S3。

```powershell
python -m agentic_cloud_radar.cli s2 `
  --input .\out\s1-landscape.json `
  --output .\out\s2-landscape-proposals.json
```

## 檔案

- `agentic_cloud_radar/s1.py`：掃描與 URL 匯入。
- `agentic_cloud_radar/s2.py`：證據比較、候選提案卡、比較矩陣。
- `docs/s1-極細註解版.md`：S1 資料流與命令說明。
- `docs/s2-極細註解版.md`：S2 提案卡欄位與比較指標。
- `s0-backend-architecture.md`：更新後的 S1/S2 入口架構。

## 驗證

```powershell
python -m compileall agentic_cloud_radar
python -m unittest discover -s tests -v
```

PowerShell 5.1 用 `Set-Content -Encoding utf8` 產生 JSON 時可能加上 BOM；CLI 以 `utf-8-sig` 讀取 input，因此有 BOM 或無 BOM 都可讀取。
