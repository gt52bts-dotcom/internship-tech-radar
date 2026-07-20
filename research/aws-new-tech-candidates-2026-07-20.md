# AWS 新技術候選資料 - 2026-07-20

## 目標

先挑出可以接到目前 Tech Radar / AI PM 專案的 AWS 新技術與範例報導，並把「今天能不能實際驗證一次」講清楚。優先選擇能產生可截圖、可寫進 final proposal、可放進 demo checklist 的材料。

## 選題限制

公司目前無法使用 Amazon Bedrock / Bedrock AgentCore，因此後續不把 Bedrock 系列列為推薦實作題目。相關報導只保留為產業趨勢或「不採用原因」參考。

## 候選清單

| 候選 | 來源 | 可以學什麼 | 跟目前專案的關聯 | 今日驗證可行性 |
|---|---|---|---|---|
| Kiro CLI + CloudWatch / AWS / Support MCP 的支援案件流程 | AWS Cloud Operations Blog：Transform AWS Support case workflows with Kiro CLI | 用 AI CLI 先查 logs/metrics/docs，再產生含證據的 Support case | 很像目前的 Evidence Ledger、Human Review Gate、AI PM inbox：把散落證據整理成可審查的案件包 | 高。可先做 dry-run evidence packet；完整 Kiro 需安裝 Kiro CLI 與 `uv/uvx` |
| AWS MCP Server GA | AWS News Blog：The AWS MCP Server is now generally available | 讓 agent 用既有 IAM 身分呼叫 AWS API、讀文件、執行沙盒 Python script，並有 CloudTrail / CloudWatch 可觀測性 | 可以把目前「人手查 AWS 狀態」升級成 agent-assisted 的 read-only 驗證流程 | 中高。此環境目前有 AWS CLI，但沒有 `uv/uvx`；可先驗證 read-only AWS CLI 等價流程 |
| Bedrock AgentCore Support Companion | AWS Machine Learning Blog：Build an AI-powered AWS Support Companion with Amazon Bedrock AgentCore | 用 AgentCore、Strands Agents、MCP、Guardrails 做支援助理 | 與支援助理概念相近，但公司目前不能用 Bedrock | 排除。不列為今日或日後推薦實作題目 |
| AgentOps on Bedrock AgentCore | AWS Machine Learning Blog：AgentOps: operationalize agentic AI at scale | 治理、安全、版本化部署、評估、可觀測性四大面向 | 可作為治理概念參考，但不能作為落地技術路線 | 排除。不列為實作題目；只保留概念對照 |
| Bedrock AgentCore Web Search | AWS News Blog：Announcing Web Search on Amazon Bedrock AgentCore | 讓 agent 取得即時網路知識，透過 AgentCore Gateway 以 MCP target 使用 | 可提醒 Skill 1 Scan 需要資料新鮮度，但不採用 AgentCore | 排除。後續若做 Web Search，改找非 Bedrock 路線 |
| Kiro + MCP 做 RDS log analysis | AWS Database Blog：Amazon RDS log analysis with Kiro and MCP | 用自然語言查 CloudWatch 裡的 RDS logs | 可當作「CloudWatch evidence gathering」的同類範例 | 中。若沒有 RDS log 資料，今天只能做模式驗證 |
| Kiro + MCP 做 EC2 到 EKS Auto Mode migration | AWS Containers Blog：Migrate Amazon EC2 to EKS Auto Mode using Kiro CLI and MCP servers | 用 agent 協助 Dockerfile、Kubernetes manifest、EKS Auto Mode 部署 | 技術很新，但和目前 Tech Radar / evidence workflow 連結較間接 | 低。今天不建議優先玩 |

## 建議先玩的題目

先選 **Kiro CLI + MCP 支援案件流程**。

理由不是它最炫，而是它最貼近目前成果：我們已經有 CloudFormation stack、Step Functions execution、S3 report artifacts、Evidence Ledger、Decision Layer、Audit Packet。今天可以把這些證據轉成一個「support-case-style evidence packet」，模擬 AWS blog 裡的「先調查、查文件、整理證據、再決定是否升級」流程。

## 驗證路線

### A. 安全 dry-run：不呼叫外部 mutating API

- 讀本地專案與既有驗證紀錄。
- 整理一份 support-case-style evidence packet。
- 欄位包含：問題、影響、已查證證據、AWS 資源、時間線、排除項目、建議下一步。
- 產出可以直接納入 final proposal 的「AI-assisted support workflow」示範材料。

### B. Read-only live check：用 AWS CLI 補證據

- 用 `aws sts get-caller-identity` 確認目前 profile。
- 用 CloudFormation / Step Functions read-only 指令查 `cathay-techintel-v3-cfn` 與 `company-cfn-001`。
- 不建立 support case、不改資源、不讀 secret value。
- 把 read-only 結果合併到 evidence packet。

### C. 完整 Kiro CLI / MCP 路線

- 需要先安裝 Kiro CLI 與 `uv/uvx`。
- 設定 CloudWatch MCP Server、AWS MCP Server、AWS Support MCP Server。
- 僅在明確確認後才建立或更新 AWS Support case。
- 這條最接近 AWS blog，但今天的 setup 風險和時間較高。

## 可直接引用的資料來源

- AWS Cloud Operations Blog：<https://aws.amazon.com/tw/blogs/mt/transform-aws-support-case-workflows-with-kiro-cli/>
- AWS News Blog：<https://aws.amazon.com/blogs/aws/the-aws-mcp-server-is-now-generally-available/>
- AWS Machine Learning Blog：<https://aws.amazon.com/blogs/machine-learning/build-an-ai-powered-aws-support-companion-with-amazon-bedrock-agentcore/>
- AWS Machine Learning Blog：<https://aws.amazon.com/blogs/machine-learning/agentops-operationalize-agentic-ai-at-scale-with-amazon-bedrock-agentcore/>
- AWS News Blog：<https://aws.amazon.com/blogs/aws/announcing-web-search-on-amazon-bedrock-agentcore-ground-your-ai-agents-in-current-accurate-web-knowledge/>
- AWS Database Blog：<https://aws.amazon.com/blogs/database/amazon-rds-log-analysis-natural-language-queries-with-kiro-and-mcp/>
- AWS Containers Blog：<https://aws.amazon.com/blogs/containers/migrate-amazon-ec2-to-eks-auto-mode-using-kiro-cli-and-mcp-servers/>
