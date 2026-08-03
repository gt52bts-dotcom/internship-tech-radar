# 全新 S3 Files PoC stack 驗證紀錄（2026-07-23）

## 範圍

本次驗證使用全新 CloudFormation stack `s3files-poc-20260723-1615`；不引用 2026-07-22 的既有 stack。

## 已驗證

- CloudFormation：stack 與 S3 bucket、S3 Files filesystem、mount target、access point、EC2 均為 `CREATE_COMPLETE`。
- 新 EC2：Systems Manager 為 Online。
- 新 EC2 掛載：`/mnt/s3files` 為 `nfs4`，且初始化掛載檔存在。
- 新 EC2 寫入：Systems Manager 寫入 `new-stack-poc-verify-20260723.txt` 成功。
- S3 API 回讀：同步後在該新 stack 的 bucket `poc/new-stack-poc-verify-20260723.txt` 找到物件，大小為 52 bytes。

## 結論與限制

已完成全新 stack 的「EC2 掛載端寫入 → S3 物件可見」最小 PoC。未進行多台 EC2、容器或 Lambda mount、壓力、長時間穩定性、故障復原與完整成本量測；stack 仍在運行，cleanup 需另行執行。
