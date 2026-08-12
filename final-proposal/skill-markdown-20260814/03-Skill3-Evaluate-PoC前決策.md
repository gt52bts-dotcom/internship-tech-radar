# Skill 3 Evaluate｜PoC 前把價值、成本、風險攤開

## 一句話定位

Skill 3 是 PoC 前的審查報告。它不是寫一段「看起來值得做」的建議，而是把一個候選技術拆成三張主管真正需要看的表：評分表、成本報表、PoC proof question。

## 報告展出順序

1. 先說明新聞前後差異：以前怎麼做、現在改了什麼、為什麼可能有價值。
2. 放最小 PoC 架構圖：主管先看懂這次會驗證哪些資源關係。
3. 放評分表：每個構面有分數、權重、加權分和理由。
4. 放成本報表：低 / 預期 / 高三種情境，列出公式和 AWS 官方 pricing 來源。
5. 放 proof question：這次 PoC 如果成功，會新增哪個決策證據。
6. 最後才給結論：進 Skill 4、補 recipe、或停下來。

## Lambda 成本報表要怎麼展

以 Lambda self-managed S3 code storage 為例，Skill 3 報價不是寫「很便宜」，而是展成這樣：

| 項目 | 預期情境示範 | 公式 | 為什麼要列 |
|---|---:|---|---|
| Lambda requests | 15 requests | request count × USD / request | AWS Lambda 官方 pricing 說 Lambda functions 依 request 數和執行 duration 計價。 |
| Lambda duration | 5 GB-seconds | allocated GB-seconds × USD / GB-second | AWS Lambda 官方 pricing 以 GB-second 計算執行時間；記憶體越大、跑越久，費用越高。 |
| Amazon S3 Standard storage | 約 0.000027 GB-month | artifact GB × hours / 730 × USD / GB-month | 這個案例的程式碼放在自管 Amazon S3 bucket，所以要列 S3 儲存成本。 |
| Amazon S3 PUT / GET | 各 30 requests | request count × USD / request | 上傳部署包、Lambda 讀取物件都會形成 S3 request。 |
| CloudWatch Logs | 0.001 GB ingested | log GB × USD / GB | Lambda invoke 會產生 log；即使金額小，也要讓主管知道沒有漏列。 |

當時 Lambda 預期情境估算約 `USD 0.000749`，高情境約 `USD 0.003387`，建議核准上限取 `USD 0.05`。重點不是金額小，而是「每個數字都知道從哪個 AWS 計價單位來」。

可放在投影片上的一句話：

> Lambda 不是常駐機器；成本主要來自 request 數與執行 duration GB-second。這個 PoC 另外列 Amazon S3 儲存 / request，因為新功能的核心就是從自管 S3 bucket 參照程式碼。

AWS 官方依據：

- [AWS Lambda pricing](https://aws.amazon.com/lambda/pricing/)：Lambda Functions 依 requests 和 execution duration GB-seconds 計價，並提供 request 與 GB-second 的計算範例。
- [Amazon S3 pricing](https://aws.amazon.com/s3/pricing/)：Amazon S3 依 storage、request、資料傳輸等項目計價。

## 評分表要怎麼展

現在版本的 Skill 3 評分不是一個模糊總分，而是五個構面加權：

| 構面 | 權重 | 這一項在問什麼 | 參照概念 |
|---|---:|---|---|
| 技術能力 | 30% | 這項新能力相對現有做法的改善幅度有多大？ | AWS Well-Architected 的 functional requirement、performance / efficiency 思維。 |
| 證據可驗證性 | 20% | 新聞主張能不能被一次小型 PoC 證實或推翻？ | Operational Excellence 強調可觀測、可檢查與持續改善。 |
| 導入前置條件 | 20% | Region、服務、權限、授權、環境準備會不會卡住？ | AWS Well-Architected 的風險辨識與架構評估方式。 |
| 可控制性與停止機制 | 15% | 執行中是否能停，成本或風險是否能控制？ | Cost Optimization 的 expenditure and usage awareness。 |
| 可逆性與 cleanup | 15% | 停止後資源與成本能不能收乾淨？ | Cloud SLA / service termination 的可逆性與終止程序概念。 |

權重設定不是論文硬套，而是配合這個專案的決策目的：Skill 3 要決定「是否值得進受控 PoC」。因此技術價值最高；可驗證性和導入前提次高，因為不能驗證或前提太多都會讓 PoC 沒意義；停止和 cleanup 各 15%，用來避免 WorkSpaces 那種一啟動就可能產生月費、cleanup 也不能退款的題目被硬做。

參考依據：

- [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html)：用一致方法檢視 AWS 架構決策的利弊，對應本專案的「固定 rubric，不按個案調分」。
- [AWS Well-Architected pillars](https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html)：Operational Excellence、Reliability、Performance Efficiency、Cost Optimization 等 pillar 對應可驗證性、導入條件、成本與控制能力。
- [AWS Cost Optimization Pillar](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html)：強調 expenditure and usage awareness，對應 Skill 3 把成本估算前移到 PoC 前。
- [ISO/IEC 19086-1:2016](https://www.iso.org/standard/67545.html)：Cloud SLA framework 的概念可支撐 service termination、可逆性、責任邊界這類評估語言。

## Lambda 評分可以怎麼示範

Lambda self-managed S3 code storage 可以這樣講：

| 構面 | 展示說法 |
|---|---|
| 技術能力 | 官方文章明確說它讓 Lambda 直接參照自管 Amazon S3 bucket，不再建立中繼副本，改善的是 code storage quota 與部署更新流程。 |
| 證據可驗證性 | PoC 能驗證 CloudFormation 是否支援 `S3ObjectStorageMode=REFERENCE`，以及 Lambda invoke 是否成功。 |
| 導入前置條件 | 需要 Amazon S3 bucket、Lambda、IAM permission、CloudFormation recipe；都是可在 sandbox 建立的標準資源。 |
| 可控制性 | 成本主要是 request / GB-second / S3 小量儲存與 request，沒有先觸發不可退款月費。 |
| 可逆性與 cleanup | bucket、Lambda、IAM role、CloudFormation stack 都能用 run-scoped cleanup 回查。 |

## 案例中可以怎麼講

- Lambda 和 S3 Files 是成功案例：Skill 3 能定義清楚 PoC 要驗證的部署與 runtime 行為，因此後面能進 Skill 4。
- WorkSpaces 是停止案例：完整桌面 agent session 可能觸發月費和合規風險，簡略版入口驗證又不能證明真正業務價值，因此不應硬做。
- Quick Suite 是停止案例：即使是 AWS 官方新聞，若內容主要是願景和成效宣稱、缺少實作細節與 recipe，也不應進 Skill 4。

## 這頁真正要讓主管看到的亮點

- 成本報表不是口頭估，而是逐項列公式、用量假設與 AWS pricing source。
- 評分表不是 AI 印象分，而是固定權重與固定準則；每項分數可以被主管挑戰。
- 是否進 PoC 不只看總分，還要看 blocker、recipe、報價狀態和 proof question。
- 停止案例不是失敗，而是 Skill 3 發揮治理價值：它能阻止「為了有 demo 而硬做」。
