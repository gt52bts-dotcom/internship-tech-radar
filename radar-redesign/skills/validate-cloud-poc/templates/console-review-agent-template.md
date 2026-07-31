# Skill 4 Console Review Agent Template

Use this template after `s4-deploy --execute` has produced an S4 runtime artifact with status `awaiting_console_review`.

## Inputs

- S4 runtime artifact path.
- Active, authenticated AWS Console browser session.
- A named human who can approve cleanup.

## Required sequence

1. Create the run-specific checklist:

   ```powershell
   python -m agentic_cloud_radar.cli s4-console-review-packet `
     --input .\out\run\s4-runtime.json `
     --output .\out\run\s4-console-review-packet.json
   ```

2. In AWS Console, open the runtime's CloudFormation stack in its recorded Region. Open **Infrastructure Composer** and inspect the resource relationship canvas. Confirm visually that it is the run-derived stack and the displayed resources match the recorded recipe.
3. Capture a PNG screenshot of Infrastructure Composer. Optionally capture the stack Resources page or service-specific resource page as `resource_inventory`.
4. Show the screenshot image in the authenticated GUI or this conversation. State only the observable result and ask one explicit question: `是否確認依此 Console 截圖清除這次 PoC？`
5. Stop and wait. A prior deployment approval is not cleanup approval.
6. After an explicit named-human confirmation, create a local evidence JSON based on `samples/s4-console-review-evidence.example.json`. Screenshot files stay outside Git and the JSON must use a non-secret local or protected-storage reference plus the SHA-256 of each image.
7. Run the single close command:

   ```powershell
   python -m agentic_cloud_radar.cli s4-close `
     --input .\out\run\s4-runtime.json `
     --review-evidence .\out\run\s4-console-review-evidence.json `
     --confirmed-by "<named-human>" `
     --notes "Infrastructure Composer screenshot reviewed; cleanup approved." `
     --output .\out\run\s4-runtime-cleaned.json `
     --execute
   ```

8. Only when the output status is `cleanup_verified`, invoke Skill 5 with that runtime. It will emit the actual-PoC final conclusion and retain screenshot metadata in the evidence ledger.

## Non-negotiable guardrails

- Do not clean any resource before the screenshot has been shown and the human has explicitly approved cleanup.
- Do not click broad Console deletion actions or delete resources outside the runtime-derived stack. `s4-close` uses the scoped AWS API / CloudFormation cleanup and verifies the outcome.
- Never commit screenshots, Console session data, account IDs, unredacted URLs, credentials, or private network details.
- A screenshot is visual evidence of this PoC run only. It is not billing evidence and does not replace the Cost Explorer, Billing, or CUR artifact required for actual cost.
