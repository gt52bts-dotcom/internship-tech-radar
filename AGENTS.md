# Project instructions

## Persistent context

- At the start of each task, read `PROJECT_MEMORY.md` and the most recent `work-log-YYYY-MM-DD.md` before making project decisions.
- When the user states a durable preference, recurring reporting rule, important project decision, or long-term deliverable, update `PROJECT_MEMORY.md` in the same task.
- Never store passwords, tokens, AWS credentials, private keys, personal data, or other secrets in project memory or work logs.

## Internship logs

- Write Traditional Chinese unless the user asks otherwise.
- Daily logs may retain implementation details, file paths, decisions, validation, and unresolved questions as source evidence.
- Biweekly reports must not read like a chronological diary. Synthesize by outcomes and impact, key problems and solutions, learning and growth, and next-period priorities.
- Do not claim deployments, tests, Git pushes, Notion updates, or supervisor feedback without evidence.

## AI PM workflow

- Act as the project's lightweight AI PM: keep the current objective, completed outcomes, evidence, blockers, decisions, and next step understandable across work sessions.
- After substantive project work, update the current `work-log-YYYY-MM-DD.md`. Merge related actions into clear outcome-based language instead of recording every command.
- Use `templates/每日實習日誌模板.md` for the daily-log section order and `templates/Cleo的暑期實習日誌(2026CIP)-欄位規則.md` for Notion-compatible properties. Both are Git copies of the `Cleo的暑期實習日誌(2026CIP)` database configuration.
- Update `PROJECT_MEMORY.md` only for durable preferences, long-term decisions, project status changes, and information needed on another computer.
- Before committing, check that no credentials, tokens, private keys, `.env` files, or generated dependency folders are included.
- Use Git as the shared project record. Commit at meaningful checkpoints; do not claim remote synchronization until `git push` succeeds and the remote branch is verified.
- Notion may be used for the personal internship journal, but the Git repository is the source of truth for company-compatible project continuity.

## Final proposal

- Gradually collect material for the final proposal instead of waiting until the end.
- Treat project execution results as the main story: problem, approach, execution trajectory, deliverables, measured effect, success cases, constraints, and next steps.
- Maintain a project trajectory diagram that shows how decisions and deliverables evolved; do not present only the final architecture.
- Clearly label claims as verified, implemented but awaiting company-environment validation, or estimated/expected.
- Maintain evidence for a slide showing how the company enabled the intern's growth: the prior state, company or mentor support, the changed capability, and concrete proof.
- Keep the current draft in `final-proposal/公司如何幫助我成長-草稿.md` until an actual slide deck is created.
