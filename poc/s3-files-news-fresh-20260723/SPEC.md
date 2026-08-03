# S3 Files 新聞獨立 PoC 規格

## 唯一輸入

- AWS News Blog：Launching S3 Files, making S3 buckets accessible as file systems。
- 官方文件：S3 Files mount、access point、IAM 與 CloudFormation resource reference。

## 假設與目標

- 假設：既有以檔案系統操作資料的工作負載，需要保留 S3 作為物件資料來源。
- 目標：證明單一 EC2 能透過 access point 掛載 S3 Files 的 `/workspace` 根目錄，將檔案寫入掛載目錄，並同步為 S3 `news-poc/` 前綴的物件。

## 邊界

- 一個 VPC、單一 Availability Zone、單一 EC2、單一 mount target、單一 access point。
- 不使用既有 PoC 的模板、stack、bucket 或其證據。
- 不包含多機、容器／Lambda mount、壓力、長時間穩定性、故障復原或完整成本量測。
- 部署完成後需由 CloudFormation cleanup；測試 bucket 先清空其版本化物件。

## 實作校正

- 首次部署以 `/` 作為 access point 根目錄時，掛載成功但 POSIX 使用者無法寫入。依官方 access point 文件改為 `/workspace` 並提供 creation permissions；此變更會由 CloudFormation replacement 套用。
