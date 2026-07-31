# S1/S2 現況與交接

> 舊檔名保留連結相容性。S0 已從入口移除，現行架構請以本文件、`README.md`、`s1-極細註解版.md`、`s2-極細註解版.md` 為準。

## 已完成

- `agentic_cloud_radar/s1.py`
  - `s1-url`：使用者指定 URL 直接進 S1；保留 HTTPS、allowlist、redirect、HTML 檢查。
  - `s1`：AWS Blogs 動態分類＋RSS，並在非 GA-only 時搜尋 GitHub 公開 repository。
  - S1 不再要求 S0 confirmation；問題文字只作 optional discovery hint。
- `agentic_cloud_radar/s2.py`
  - 對每個候選建立 `proposal_card`，內含問題待確認欄、改善假設、好處、利弊、量測設計與 stop conditions。
  - 產出 `comparison_matrix` 與 `cross_candidate_findings`，不產生假精準總分或自動 shortlist。
- `agentic_cloud_radar/cli.py`
  - `s1 --input <discovery request>`
  - `s1-url --url <public URL>`
  - `s2 --input <s1 artifact>`

## 下一步

1. 用 S2 matrix 選一張提案卡進行單項評估。
2. 對每張補真實 workflow、target user、baseline、成功標準與預算／權限邊界。
3. S3 只評估這些已有人類情境的 proposal；S4 前維持 human PoC gate。

## 不可退回的原則

- 不用 demo URL、假參數或編造技術主張。
- S1 發現技術，S2 才提出它可能值得解的問題。
- 來源證據、規劃推論、公司驗證結果要在 artifact 中分開。
