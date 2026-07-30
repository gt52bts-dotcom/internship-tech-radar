# Agentic Cloud Radar 設計基線

## 1. 目標

把「看見一篇新技術新聞」走到「有證據、可量測、可停止的 PoC 提案」：

```text
S1 Scan -> S2 Compare + Proposal -> S3 Evaluate -> human gate -> S4 Validate -> S5 Report
```

## 2. 入口

系統沒有入口 S0。入口只有兩種：

1. 使用者指定公開 URL：直接進 `S1 URL Import`。
2. 使用者要求技術探索：直接進 `S1 Discovery`。

URL import 仍有 HTTPS、trusted host、redirect、content-type 的資料安全檢查；這些是來源驗證，不是需求審查。

## 3. 五個 Skills

| Skill | 產物 | 不能做的事 |
| --- | --- | --- |
| S1 Scan | 真實候選、來源、擷取文字、GA evidence、data gaps | 不推薦、不做商業適配結論 |
| S2 Compare | 候選提案卡、比較矩陣、改善假設、利弊、驗證設計 | 不自動選題、不把 unknown 補成事實 |
| S3 Evaluate | 人類短名單的比較與決策依據 | 不繞過人工 shortlist |
| S4 Validate | 已核准且可 cleanup 的低風險驗證 | 不碰敏感／production data，不超 USD 3 |
| S5 Report | 可回查的結論、限制、證據與後續 | 不把估計寫成已驗證 |

## 4. S2 的提案卡規格

每個 S1 candidate 都要有：

- Source-backed technology mechanism。
- 待確認的問題、使用者、baseline、成功條件。
- Potential improvement vectors 與量化／質化證據等級。
- Benefits（有來源）與 tradeoffs（標 source fact 或 planning inference）。
- 成熟度、文件／定價／區域證據、環境訊號。
- Before/after metrics、stop conditions、下一個人工問題。

S2 的 purpose 是讓 Mentor 或使用者可以從同一張矩陣判斷「哪張提案值得花時間補情境」，不是讓模型假裝能直接排序。

## 5. 證據原則

- 每個候選都保留 source URL、是否真實 fetch、來源類型與 data gaps。
- 官方 AWS 來源才能被用來證明 AWS GA；GitHub 等公開來源只證明該專案的公開存在與 metadata。
- 價格與 Region 未查到時，輸出 unknown 或 review note，不要求使用者補環境表單。
- `ap-southeast-1` 不再是 shortlist 或 PoC 審查硬門檻。S2 只標記 Region status：有功能級官方證據時為 `available_ap_southeast_1`，未查到時為 `region_unknown` warning。
- 只把 verified、implemented awaiting validation、estimated 三種主張分開寫。

## 6. 目前完整流程圖

```mermaid
flowchart TD
    subgraph POL["Policy 層（取代原 S0，靜態設定不是入口輸入）"]
        POL1["policy.json<br/>preferred_region = ap-southeast-1<br/>excluded_services = Bedrock<br/>max_small_poc_usd = 3.00<br/>official_hosts allowlist"]
        POL2["policy_ref = 指紋 sha256[:12]<br/>每個 artifact 都必須帶<br/>缺少即標 policy_unavailable"]
        POL1 --> POL2
    end

    POL2 -.->|"約束隨 artifact 一路傳遞"| S1
    POL2 -.-> S2
    POL2 -.-> S3
    POL2 -.-> S4
    POL2 -.-> S5

    IN["Cleo / Mentor<br/>提出方向或貼公開來源"] --> ENT{"S1 入口類型"}
    ENT -->|"貼 URL"| E1["S1 URL Import<br/>公開 HTTPS URL"]
    ENT -->|"探索"| E2["S1 Discovery<br/>AWS Blogs 動態目錄 / What's New<br/>GitHub 公開 repo 搜尋"]

    E1 --> FETCH["單一 HTTP 出口<br/>fetch_trusted_html_document()<br/>host allowlist 檢查"]
    E2 --> FETCH
    FETCH --> GA{"GA 篩選"}
    GA -->|"Preview / 彙整文"| GAX["排除並記錄原因<br/>excluded_non_ga"]
    GA -->|"GA"| REG["region 訊號抽取<br/>只標記不排除"]

    REG --> RS{"region_status 三態"}
    RS --> RS1["available_ap_southeast_1<br/>官方功能級證據"]
    RS --> RS2["other_region_only<br/>官方證據顯示僅他區"]
    RS --> RS3["region_unknown<br/>查不到官方區域證據"]

    RS1 --> EXC
    RS2 --> EXC
    RS3 --> EXC
    EXC{"excluded_services 檢查"}
    EXC -->|"命中 Bedrock"| EXC1["標 governance_flag<br/>excluded_by_policy"]
    EXC -->|"未命中"| S1

    S1["S1 Scan Artifact<br/>來源 / 標題 / 摘要 / 官方性<br/>fetch 狀態 / region_status<br/>warning / data gap / policy_ref"]
    EXC1 --> S1

    S1 --> S2CHK{"S1 可用嗎"}
    S2CHK -->|"否"| S2E1["blocked_s1_not_usable"]
    S2CHK -->|"是"| S2

    S2["S2 Compare<br/>只讀 S1 可回查候選<br/>重抓官方文件與其自引連結"]
    S2 --> CARD["Proposal Card 每候選一張"]
    CARD --> C1["source-backed fact<br/>官方來源已證實"]
    CARD --> C2["planning inference<br/>規劃推論（必須標明）"]
    CARD --> C3["unknown / data gap<br/>證據不足"]
    CARD --> C4["region_status<br/>降級為 warning 不再擋路"]
    CARD --> C5["pricing<br/>無官方定價證據一律 unknown<br/>絕不估價"]

    CARD --> GATE
    GATE["Human Shortlist Gate<br/>真人最多挑 3 項<br/>不需公司問題或環境表單"]
    GATE -->|"未提供"| GE1["needs_human_shortlist<br/>流程停在這裡"]
    GATE -->|"已提供"| S3

    S3["S3 Evaluate 固定 rubric<br/>不因候選調權重"]
    S3 --> D1["技術價值 0.35<br/>公開來源支持的能力"]
    S3 --> D2["導入前提 0.25<br/>文件 / 定價 / Region<br/>region_status 在此扣分"]
    S3 --> D3["可驗證性 0.25<br/>能否做最小 PoC 或文件驗證"]
    S3 --> D4["風險與停損 0.15<br/>stop conditions 必填"]
    S3 --> D5["成本不列入技術分數<br/>僅記錄估算<br/>供 S4 上限檢查"]

    D1 --> S3O["S3 Evaluate Artifact<br/>加權分 / confidence / stop conditions<br/>low-risk 與 PoC review 雙判斷"]
    D2 --> S3O
    D3 --> S3O
    D4 --> S3O
    D5 --> S3O

    S3O --> S3Q{"recommend_low_risk_validation"}
    S3Q -->|"否"| S3N["保留評估結果<br/>標示不建議驗證原因<br/>仍進入 S5 報告"]
    S3Q -->|"是"| S4G

    S4G["S4 Validate Gate<br/>具名核准 + 選定候選<br/>其餘使用 recipe 預設"]
    S4G --> VT{"驗證類型"}
    VT --> V1["低風險驗證<br/>文件驗證 / 本機 / validator artifact"]
    VT --> V2["最小 PoC<br/>可能建立 AWS 資源"]

    V2 --> V2C{"簡化 PoC 檢查"}
    V2C --> V2C1["eligible_for_poc_review"]
    V2C --> V2C2["內建小額成本上限"]
    V2C --> V2C3["approved_by 非空<br/>deployment_authorized=true"]
    V2C1 --> V2R{"檢查全過"}
    V2C2 --> V2R
    V2C3 --> V2R
    V2R -->|"否"| V2X["降級為低風險驗證<br/>並記錄 downgrade 原因"]
    V2R -->|"是"| S4A

    V1 --> S4A
    V2X --> S4A
    S4A["S4 Validate Artifact<br/>證據 / 測試結果 / 限制 /<br/>失敗原因 / cleanup 狀態"]

    S3N --> S5
    S4A --> S5

    S5["S5 Report<br/>輸入契約：只吃 S1/S2/S3/S4 artifact<br/>artifact 沒有的敘述一律 unknown<br/>禁止 fallback 補字"]
    S5 --> R1["漏斗統計<br/>feeds → 候選 → GA →<br/>各 region_status → shortlist →<br/>評估 → 驗證"]
    S5 --> R2["證據帳本 evidence ledger<br/>每一句話可回查 URL"]
    S5 --> R3["三分區呈現<br/>已驗證 / 待區域上線 /<br/>證據不足"]
    S5 --> R4["PoC Gate<br/>加權分 >= 3.75<br/>confidence >= medium<br/>無 governance flag"]
    R4 --> R5["automatic_poc_start 永遠 false<br/>僅標 eligible_for_human_poc_review"]

    R1 --> DEL["交付層"]
    R2 --> DEL
    R3 --> DEL
    R5 --> DEL
    DEL --> DEL1["Agent mode<br/>五個可重用 Skill 規格<br/>S1-S5 各一"]
    DEL --> DEL2["Deployed mode<br/>GUI + AWS backend"]
    DEL --> DEL3["Final proposal /<br/>Dashboard / Mentor review package"]

    GAX --> S5
    GE1 --> S5
    S2E1 --> S5
```
