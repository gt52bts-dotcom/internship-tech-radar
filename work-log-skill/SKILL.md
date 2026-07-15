---
name: work-log
description: Create and push internship work logs to Notion, including detailed daily evidence, non-chronological biweekly summaries, supervisor-ready progress notes, final-presentation growth evidence, and handoff records. Use this skill when the user says 工作日誌, 實習日誌, 今日進度, 主管報告, 日報, 雙週誌, 週報, 交接紀錄, 今天做了什麼, 幫我整理工作內容, 推到 Notion, 照昨天模板, demo 前進度, or needs a concise Chinese work record with completed work, evidence files, blockers, decisions, next steps, and manager-facing wording.
---

# Work Log

Use this skill to turn rough work notes, project files, or conversation context into a clean internship work log. Default to pushing the final log to Notion when the Notion connector is available.

## Output Style

Write in Traditional Chinese by default. Keep the tone professional, concrete, and suitable for a supervisor. Prefer conclusion-first wording:

### Notion Card Naming

- Set the main title (`名稱`) to the date only, using `M/D` such as `7/13`.
- Never put the project name, task name, or result in the main title.
- Write the key daily outcome in `副標題` as one concise summary.
- Prefer a concrete result such as `完成 CDK 骨架＋AWS 個人帳戶部署成功`.
- Keep `日期` populated for filtering and sorting even when it is hidden from gallery cards.
- Keep `Mentor 討論關鍵字` in the database but hide it from gallery cards.
- Display `星期幾` as the final card property.

1. 今日主題
2. 今日完成事項
3. 執行驗證
4. 當日流程圖
5. Mentor 討論筆記
6. 遇到的問題與處理
7. 技術調整紀錄
8. 提醒事項
9. 今日總結

Use bullet points only where they make scanning easier. Avoid vague phrases like "研究了一下" unless paired with a concrete output.

### Two-layer Logging

- Daily/detail layer: preserve implementation details, decisions, evidence paths, verification, and unresolved questions. This layer may be detailed because it is the source material.
- Biweekly layer: synthesize by outcome, contribution, learning, and next step. Do not narrate work day by day and do not list every small action.
- Promote an item into the biweekly log only when it shows a delivered result, an important decision, a solved problem, a capability gained, or a meaningful next step.
- Keep a `成長證據` note when company resources, mentor feedback, review standards, tools, or real project constraints changed how the intern works. These notes feed the final proposal slide about how the company enabled growth.

## Standard Workflow

1. Identify the date, project, and intended audience.
2. Collect raw input from the user or from project files.
3. Use `scripts/worklog.py draft` to create a structured Markdown log when deterministic formatting is useful.
4. Refine the draft into supervisor-ready language.
5. Push the final content to Notion using the work-log template structure.
6. Score the day's evidence across the five independent Skill projects using integer points, then update the Notion Skill score database and embedded dashboard.
7. If the user asks for a biweekly summary, combine daily logs with `scripts/worklog.py biweekly`, then rewrite the draft into outcome-based language.
8. Update `PROJECT_MEMORY.md` when the user states a durable preference, long-term deliverable, or recurring reporting rule.
9. Use `../templates/每日實習日誌模板.md` as the canonical Git copy of the Notion daily template when this skill is inside the internship project.

## Evidence Rules

Prefer concrete evidence:

- File paths for generated packages, reports, docs, or code.
- Test commands and results.
- Architecture decisions and why they changed.
- Blockers with cause and current mitigation.

Do not invent AWS deployment results, GitHub pushes, Notion template matches, or successful tests. If a command was not run or a template/database was not found, state that clearly.

## Notion Output Rule

When the user asks for work logs in this project, create or update a Notion page by default. If a specific Notion database or template page is not known, create a standalone private Notion page using the standard sections below and tell the user the page URL. If the user later provides a database/template URL, use that parent/template for future logs.

For this internship project, the default Notion destination is:

- Database: `2026｜每日規劃庫`
- Data source ID: `cd79d9fb-a316-8208-9d99-073d0ac114e1`
- Main view: `https://app.notion.com/p/de09d9fba31682c0bc34011ff6a2b176?v=1a29d9fba316820ca1a7087650fb2cf5`
- Use properties: `名稱`, `date:日期:start`, `date:日期:is_datetime`, `今日備註與總結`

For July through the end of August 2026, push internship work logs into this database unless the user gives another destination.

### Skill dashboard sync

- Track these five Skills exactly: `掃描 Scan`, `比較 Compare`, `評估 Evaluate`, `驗證 Validate`, and `報告 Report`.
- Use integer points only: `+1～2` preparation, `+3～4` small result, `+5～7` usable delivery, `+8～10` verified milestone. Maximum 10 points per result.
- Score data source: `collection://ed56335a-cd24-4b70-8bf1-6fa25f87d1f0`.
- Dashboard page: `https://app.notion.com/p/39e9d9fba316813c8e68fa80f8f33d08`.
- Update Git and Notion together; never claim either sync until it is verified.

## Script Usage

Create a daily log:

```powershell
python scripts/worklog.py draft `
  --date 2026-07-14 `
  --project "Cathay Tech Intel v3" `
  --done "補齊 CDK Lambda S1-S5" `
  --done "補 Cognito + API Gateway 啟動路徑" `
  --evidence "demo-v03-complete-cdk.zip" `
  --blocker "本機尚未安裝 CDK CLI，未跑 cdk synth" `
  --next "在 AWS 帳號執行 cdk deploy --all"
```

Scan a folder for evidence files:

```powershell
python scripts/worklog.py scan --root C:\Users\youhs\Documents\實習專案 --days 2
```

Create a weekly summary from daily Markdown logs:

```powershell
python scripts/worklog.py weekly --logs logs --output weekly-summary.md
```

Create a biweekly synthesis scaffold:

```powershell
python scripts/worklog.py biweekly --logs logs --output biweekly-summary.md
```

## When To Read References

Read `references/log-format.md` when you need the exact templates for daily logs, weekly reports, handoff notes, or supervisor updates.
