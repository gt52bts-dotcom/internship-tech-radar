# Agentic Cloud Radar GUI Handoff

This folder is self-contained: it includes the synchronized S1-S5 core, five reusable Skill packages, a deployable AWS web demo, two controlled S4 PoC recipes, redacted artifact examples, Console-review automation, tests, and the GUI contract for Claude.

Start with `CLAUDE_GUI_HANDOFF.md`. Run `python web_demo_local.py` for a local GUI, or deploy from `web-demo-cdk/README.md`.

For the controlled PoC runner, use `skills/validate-cloud-poc/SKILL.md` and the Skill 4 deployment guide in `docs/`. A Console review packet has an explicit deadline; normal cleanup requires packet-bound screenshot evidence, a named human confirmation, and `--shared-via`.

Do not add a browser action that bypasses the S4 approval, cost ceiling, Console review, or cleanup flow.
