# Skill 3 Evaluate｜PoC 前先回答值不值得做

## 一句話定位

Skill 3 是整套流程最重要的決策點。它在任何 AWS 資源被建立前，先產出主管看得懂的中文決策報告：分數、報價、架構、blocker、PoC 要證明什麼。

## 人類應該怎麼理解

以前看到新技術，容易直接想「做個 PoC 看看」。但在企業情境裡，PoC 不是免費的好奇心；它會牽涉時間、成本、權限、合規和 cleanup。

Skill 3 的任務就是在進 Skill 4 以前先問清楚：這個候選技術到底值得驗證嗎？要花多少？有沒有可部署 recipe？成功後決策者會多知道什麼？如果這些回答不清楚，就應該停下來。

## 它實際做什麼

- 只評估人類選定的單一候選。
- 依固定 rubric 評分，不為特定產品寫死分數。
- 評分構面包含技術價值、可驗證性、導入前提、可控制性與停止條件、可逆性與 cleanup。
- 產出部署前 PoC 報價：low / expected / high、公式、費率、來源、假設與建議核准上限。
- 檢查是否有可部署 Skill 4 recipe。
- 產出 HTML-first 中文決策報告，先解釋文章和架構，再顯示分數與是否建議進 PoC。
- 必須回答 proof question：這次 PoC 要證明什麼？成功後決策者會多知道什麼？

## 亮點

- **把成本移到部署前**：預算不是 PoC 做完後才回報，而是在 Skill 3 就先估。
- **把硬做擋下來**：如果只有廣告詞、沒有 recipe、成本不可逆、成功後也沒有決策增量，就不進 Skill 4。
- **人看得懂**：報告不是 raw JSON，而是主管能讀的繁體中文 HTML 報告。
- **分數可被質疑**：每個構面都有理由，不只是一個總分。
- **技術資格不等於部署批准**：`recommend_poc=true` 只表示技術上值得考慮，仍需要人類具名核准才能進 Skill 4。

## 案例中可以怎麼講

- Lambda 和 S3 Files 是成功案例：Skill 3 能定義清楚 PoC 要驗證的部署與 runtime 行為，因此後面能進 Skill 4。
- WorkSpaces 是停止案例：完整桌面 agent session 可能觸發月費和合規風險，簡略版入口驗證又不能證明真正業務價值，因此不應硬做。
- Quick Suite 是停止案例：即使是 AWS 官方新聞，若內容主要是願景和成效宣稱、缺少實作細節與 recipe，也不應進 Skill 4。

## 交付物

- `s3.json`
- Skill 3 HTML 決策報告
- PoC 成本估算報價單
- score breakdown
- blocker / review notes
- PoC decision gate

## GitHub 位置

- Skill 規格：`radar-redesign/skills/evaluate-cloud-candidate/SKILL.md`
- Agent 入口：`radar-redesign/skills/evaluate-cloud-candidate/agents/openai.yaml`
- 共用核心：`radar-redesign/agentic_cloud_radar/s3.py`
- 評分準則：`radar-redesign/agentic_cloud_radar/rubric.py`

## 20 秒講稿

> Skill 3 是我這套流程的煞車和方向盤。它在 PoC 前先把技術價值、可驗證性、成本、recipe、風險和 proof question 寫成人看得懂的報告；回答不出來時，停止本身就是成果，因為它避免了為了展示而硬做。
