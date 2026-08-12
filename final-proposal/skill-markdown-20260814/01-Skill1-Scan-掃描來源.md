# Skill 1 Scan｜把 AWS 新聞變成可追蹤的候選技術卡

## 一句話定位

Skill 1 不是「摘要文章」。它的工作是把一篇 AWS 官方新聞或可信公開來源，整理成後面能比較、能評估、能被追問來源的候選 artifact。

## 人類應該怎麼理解

看到 AWS 新聞時，最容易被標題和成效宣稱帶著走。Skill 1 先做第一層整理：這篇文章到底說了什麼新功能、哪些句子是來源直接寫的、哪些是 AI 推導出來的可能架構、哪些資訊還缺。

它把「我看過這篇」變成「我知道這篇可以拿來評估什麼，也知道哪些地方不能當證據」。

## 它實際做什麼

- 接收單一 AWS 官方 URL，或從可信來源掃描候選技術。
- 保留來源 URL、標題、擷取時間、成熟度線索、相關 AWS 服務與缺口。
- 把文章拆成 `key_points`、`significance`、`implementation_architecture`、`possible_application_contexts`。
- 標記每段資訊的來源型態：原文、摘要、架構推論或假設。
- 移除行銷雜訊，但不把弱證據包裝成強證據。

## 亮點

- **去廣告化**：AWS 官方文章也可能有很多宣傳語，Skill 1 會先把「功能事實」和「價值宣稱」分開。
- **證據分層**：只有原文與摘要能支撐已驗證事實；AI 推論的架構會被標成推論，不會假裝是官方做法。
- **留下缺口**：如果文章沒寫 Region、價格、實作步驟或服務元件，這些不會被補故事，而是帶到後面當 review gap。
- **建立共同語言**：人不用重新讀完整文章，也能知道這個候選為什麼被留下。

## 這關不做什麼

- 不排名。
- 不判斷要不要 PoC。
- 不建立 AWS 資源。
- 不因為來源是 AWS 官方就自動相信所有成效宣稱。
- 不把 GitHub metadata 或二手資訊當成 AWS GA 證據。

## 案例中可以怎麼講

- S3 Files 和 Lambda 的成功案例，都是先從官方文章被整理成可追蹤候選，再進後續評估。
- Quick Suite 則顯示 Skill 1 的價值：它能保留文章主張，但也能讓後面看到「文章偏產品願景，實作細節不足」。

## 交付物

- `s1.json`
- 候選技術卡
- 來源證據與缺口
- 後續 Skill 2 可直接讀取的結構化資料

## GitHub 位置

- Skill 規格：`radar-redesign/skills/scan-cloud-technologies/SKILL.md`
- Agent 入口：`radar-redesign/skills/scan-cloud-technologies/agents/openai.yaml`
- 共用核心：`radar-redesign/agentic_cloud_radar/s1.py`

## 20 秒講稿

> Skill 1 解決的是新技術資訊太雜的問題。它不是單純摘要 AWS 新聞，而是把文章拆成來源事實、AI 摘要、架構推論和證據缺口，讓後面每一步都能追溯「這個判斷從哪裡來」。
