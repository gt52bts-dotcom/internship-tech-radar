# Git 跨電腦同步

目前資料夾已初始化為本機 Git repository；還需要遠端 repository URL 才能完成同步。

## 第一次連接遠端

```powershell
git config user.name "你的 Git 顯示名稱"
git config user.email "你的 Git Email"
git remote add origin <REMOTE_REPOSITORY_URL>
git commit -m "Initialize internship project and persistent context"
git push -u origin main
```

若遠端已經有初始內容，先檢查遠端分支，不要直接強制推送：

```powershell
git fetch origin
git log --oneline --decorate --graph --all -n 20
```

## 另一台電腦

```powershell
git clone <REMOTE_REPOSITORY_URL>
cd <REPOSITORY_FOLDER>
```

進入專案後，Codex 會依 `AGENTS.md` 先讀 `PROJECT_MEMORY.md` 與最新工作日誌，延續專案背景。

## 平常同步

開始工作前：

```powershell
git pull --ff-only
```

完成一個可說明的工作單位後：

```powershell
git status
git add -A
git commit -m "簡短描述本次成果"
git push
```

`.gitignore` 已排除 ZIP、AWS CDK 建置輸出、Python 快取、環境變數與常見金鑰檔案。
