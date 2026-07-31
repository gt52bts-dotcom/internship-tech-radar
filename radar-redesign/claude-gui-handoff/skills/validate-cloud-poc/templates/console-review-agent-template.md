# Skill 4 Console Review Agent Template

Use this template after `s4-deploy --execute` has produced an S4 runtime artifact with status `awaiting_console_review`.

Keep the packet, evidence JSON, and screenshot in the same run folder under `./out/run/`; do not create a parallel artifact layout.

## Inputs

- S4 runtime artifact path.
- Active, authenticated AWS Console browser session.
- A named human who can approve cleanup.

## Required sequence

1. Create the run-specific checklist:

   ```powershell
   python -m agentic_cloud_radar.cli s4-console-review-packet `
     --input .\out\run\s4-runtime.json `
     --review-timeout-minutes 60 `
     --output .\out\run\s4-console-review-packet.json
   ```

   The packet records `review_deadline`. That timestamp is the only objective definition of a review timeout.

2. Run the Playwright capture command recorded in the packet. It opens a visible browser, uses an existing AWS Console session or waits for manual login, navigates to CloudFormation / **Infrastructure Composer**, hides Console chrome, and captures the center canvas as a redacted PNG:

   ```powershell
   node .\scripts\s4-capture-infrastructure-composer.mjs `
     --runtime .\out\run\s4-runtime.json `
     --packet .\out\run\s4-console-review-packet.json `
     --output-dir .\out\run\s4-console-review `
     --evidence-output .\out\run\s4-console-review-evidence.json `
     --shared-via conversation
   ```

3. Inspect the PNG before showing it. Confirm visually that it is the run-derived stack and the displayed resources match the recorded recipe. If the canvas is blank, logged out, cropped incorrectly, shows account details, or is not the reviewed stack, rerun the capture.
4. Show the screenshot image in the authenticated GUI or this conversation. State only the observable result and ask one explicit question: `是否確認依此 Console 截圖清除這次 PoC？`
5. Stop and wait. A prior deployment approval is not cleanup approval.
6. After an explicit named-human confirmation, use the local evidence JSON created by the Playwright script. Screenshot files stay outside Git and the JSON must use a non-secret local or protected-storage reference plus the SHA-256 of each redacted image. The code validates metadata, run ID, stack name, Region, packet-required views, and the redact-before-hash contract; it does not understand the screenshot pixels.
7. Run the single close command. `--shared-via` records the channel where the human actually saw the image and becomes `display_channel_confirmed`:

   ```powershell
  python -m agentic_cloud_radar.cli s4-close `
    --input .\out\run\s4-runtime.json `
    --packet .\out\run\s4-console-review-packet.json `
    --review-evidence .\out\run\s4-console-review-evidence.json `
    --confirmed-by "<named-human>" `
    --shared-via conversation `
     --notes "Infrastructure Composer screenshot reviewed; cleanup approved." `
     --output .\out\run\s4-runtime-cleaned.json `
     --execute
   ```

8. Only when the output status is `cleanup_verified`, invoke Skill 5 with `--runtime .\out\run\s4-runtime-cleaned.json`. New v3 runtime needs screenshot metadata and `display_channel_confirmed` to become `final`; abort cleanup is reported as `final_without_console_review`, never as an actual-PoC final.

## Timeout / Abort

Use this only after `review_deadline`, deployment failure, or normal-close failure. For a review timeout, include the packet so the CLI can verify the deadline:

```powershell
python -m agentic_cloud_radar.cli s4-abort `
  --input .\out\run\s4-runtime.json `
  --packet .\out\run\s4-console-review-packet.json `
  --confirmed-by "<named-human>" `
  --reason "Console review timed out; emergency cleanup approved for cost control." `
  --output .\out\run\s4-runtime-aborted.json `
  --execute
```

Do not call this a successful Console-reviewed PoC. Skill 5 should show that cleanup was forced without screenshot-backed confirmation.

## Non-negotiable guardrails

- Do not clean any resource before the screenshot has been shown and the human has explicitly approved cleanup.
- Exception: use `s4-abort --execute` only after the packet deadline, a failed deployment, or a failed normal close; record the named approver and reason.
- Do not click broad Console deletion actions or delete resources outside the runtime-derived stack. `s4-close` uses the scoped AWS API / CloudFormation cleanup and verifies the outcome.
- Never commit screenshots, Console session data, account IDs, unredacted URLs, credentials, or private network details.
- A screenshot is visual evidence of this PoC run only. It is not billing evidence and does not replace the Cost Explorer, Billing, or CUR artifact required for actual cost.
