# 2026-08-04 WorkSpaces AI Agents 文章 Skill 1-3 評估摘要

## 評估對象

- 文章：Amazon WorkSpaces Now Lets AI Agents Operate Desktop Applications
- 來源：https://aws.amazon.com/blogs/desktop-and-application-streaming/amazon-workspaces-now-lets-ai-agents-operate-desktop-applications/
- Run ID：direct-url-20260804-20fd4c4b
- Candidate ID：S1-791440D21925
- 本次範圍：Skill 1 掃描、Skill 2 比較、Skill 3 評估與報價

## 文章在講什麼

這篇文章的核心是：AWS WorkSpaces Applications 現在支援讓 AI agent 連進受管理的桌面應用環境，去操作沒有現代 API 的舊系統或 Windows 桌面程式。

它的價值不是「讓 AI 隨便控制桌面」，而是把原本昂貴又不穩的純畫面操作，改成混合模式：

- 能用工具或 API 的步驟，就讓 agent 直接呼叫工具。
- 只有真的需要 GUI 的步驟，才回到畫面操作。
- 人類可以觀察或中止 agent session。
- 活動證據可透過 S3、CloudWatch、CloudTrail 等來源留下紀錄。

> 2026-08-05 校正：以下 8/4 初步評估已由新版 Skill 3 rubric 取代。本文件保留作為當日分析紀錄；目前應以 `2.65 / 5`、`recommend_poc=false`、`can_enter_skill4=false` 和 `compliance_review_required` blocker 為準。

## 2026-08-05 校正後結論

- Skill 3 分數：2.65 / 5（未達 3.75 / 5 PoC 門檻）
- 評分細項：技術能力 4、證據可驗證性 3、導入前置條件 2、可控制性與停止機制 2、可逆性與終止 1。
- PoC blocker：`compliance_review_required`
- 第一段基礎設施驗證報價：低／預期／高 USD 0.05／0.10／0.40；建議核准上限 USD 0.50。
- 專用第一段基礎設施驗證 recipe 已登錄，但不代表可以部署。完整桌面 agent session 是第二段，必須另行定義任務與核准。
- 結論：不可進入 Skill 4，沒有建立 AWS 資源。

## 2026-08-04 初步 Skill 3 結論（歷史紀錄）

- Skill 3 分數：4.6 / 5
- 決策狀態：等待人工決策
- 是否自動進入 Skill 4：否
- 技術上是否值得繼續看：是
- 目前是否可直接部署 Skill 4：否

原因是這篇的技術價值很高，但目前還沒有 WorkSpaces AI agent access 專用的 Skill 4 PoC recipe。Skill 3 這次使用的是通用低用量模型報價，不是候選專用 recipe 報價。

## 報價摘要

- Quote ID：POC-QUOTE-E8A03C3CB4CF
- 報價性質：PoC 前非正式公開牌價估算
- 目標區域：ap-southeast-1
- 低用量：USD 0.000054
- 預期用量：USD 0.000543
- 高用量：USD 0.005537
- 建議核准上限：USD 0.05
- 報價模型：generic_usage_model
- 專用部署 recipe：尚未登錄

這份估價只涵蓋目前模型偵測到的 S3 / CloudWatch / IAM 線索，不能代表完整 WorkSpaces Applications、串流 session、MCP endpoint、目錄整合或正式企業環境成本。

## PoC 要證明什麼

如果之後要進 Skill 4，這次 PoC 不該只是證明「AWS 有發這個功能」。Skill 3 已經能看出功能價值，Skill 4 應該補上的是實作風險與可驗證性：

- AI agent 是否能在受管理的 WorkSpaces session 中操作指定桌面應用。
- 是否能限制 agent 權限，並保留人類觀察或中止能力。
- 是否能留下足夠證據，讓人知道 agent 做了什麼、何時做、是否成功。
- 是否能把 session 證據、CloudWatch 指標、CloudTrail 記錄與測試結果整理成可審查的 Skill 5 結論。
- 是否能確認 ap-southeast-1 或公司可用區域真的支援本功能。

如果成功，決策者會多知道：這個功能是否能從「新聞看起來有價值」變成「公司環境有機會落地，而且可以被監控、審計、停止與清理」。

## 目前不能直接進 Skill 4 的原因

- 目標區域支援尚未由程式確認。
- 尚未建立 WorkSpaces AI agent access 的專用 PoC recipe。
- 目前報價是通用估價，不是 WorkSpaces 專用成本模型。
- 真實 PoC 可能需要既有 WorkSpaces Applications 環境、MCP endpoint、身份驗證設定、測試桌面應用，以及更明確的權限邊界。

## 本機產物

這些是本機完整產物，不納入 GitHub 原始輸出：

- `radar-redesign/out/workspaces-ai-agents-20260804-s1-s3/s1.json`
- `radar-redesign/out/workspaces-ai-agents-20260804-s1-s3/s2.json`
- `radar-redesign/out/workspaces-ai-agents-20260804-s1-s3/s3.json`
- `radar-redesign/out/workspaces-ai-agents-20260804-s1-s3/skill3-poc-decision-report.html`
- `radar-redesign/out/workspaces-ai-agents-20260804-s1-s3/skill3-poc-architecture-workspaces-ai-agent.png`

## 下一步

若要繼續這篇，先補 WorkSpaces 專用 Skill 4 PoC recipe 與成本模型，再確認目標區域與公司測試環境。完成前，不應直接建立 AWS 資源。
