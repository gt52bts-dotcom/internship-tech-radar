# AWS 技術雷達重做區

這個資料夾保存新版 AWS 技術雷達的重新設計材料。

目前原則：

- 先討論定位、證據、評分、PoC gate、維運與 Skill 化，再寫程式。
- 不沿用舊版對外命名。
- GUI 是可實際使用的操作前端，後續預期部署到 S3 或搭配 CloudFront；五個 Skill 是長期可交接核心。
- 舊系統只作為經驗來源，不直接當作新版基礎。

已確認的新版方向：

- 正式名稱：AI Agentic 雲端技術雷達與評估系統。
- 建議 AWS resource prefix：`agentic-cloud-radar`。
- 第一版先完成後端流程與完整架構。
- S0 需求卡放在 S1 前面。
- 允許 runtime web search，但報告必須標示來源與證據等級。
- S4 PoC 預設成本上限為 USD 1。

目前文件：

- `design-baseline.md`：新版設計基準草案。
- `s0-backend-architecture.md`：S0 需求卡與後端架構設計草案。

目前程式切片：

- `agentic_cloud_radar/s0.py`：S0 需求卡標準化與驗證核心。
- `agentic_cloud_radar/cli.py`：本機 CLI 入口。
- `samples/s0-url-input.json`：指定 URL 情境的 S0 範例輸入。
- `tests/test_s0.py`：S0 單元測試。

本機執行：

```powershell
cd C:\Users\youhs\Documents\實習專案\radar-redesign
python -m agentic_cloud_radar.cli s0 --input .\samples\s0-url-input.json
python -m unittest discover -s tests
```

目前限制：

- S0 不向外搜尋、不抓 URL。
- LLM demand-card assistant 目前先做成 rule-based first implementation，用固定規則標記模糊需求；尚未串接外部 LLM API。
- 目前只完成 S0 本機核心，尚未完成 S1-S5、Lambda、CDK 或 GUI。
