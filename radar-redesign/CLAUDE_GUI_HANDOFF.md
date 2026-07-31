# Claude GUI Handoff

## Mission

Improve the visual and interaction design of the web UI without changing the evidence, approval, and deployment contracts in the Python core.

## Read First

1. `design-baseline.md`: end-to-end policy and five-stage workflow.
2. `skills/`: the five current runnable Skill contracts.
3. `docs/s4-完整PoC部署操作.md`: controlled PoC and Console-review commands.
4. `web-demo-cdk/README.md`: AWS deployment and API contract.
5. `sample-artifacts/lambda-self-managed-code-storage/`: a real S1 through S4 runtime evidence set and an S5 report.

## Non-Negotiable Workflow Rules

- S1 retains both URL import and dynamic discovery through AWS Blogs categories, What's New, and public GitHub search.
- S2 treats Region as evidence with a warning state; it does not silently exclude candidates because Singapore evidence is missing.
- Skill 3 stops for a human selection of exactly one candidate. Do not ask for extra environment forms or automatically rank a landscape result into a winner.
- Skill 3 creates the complete non-binding PoC quote before Skill 4. Its static public-rate-card estimate is not an AWS invoice, a sales quote, or actual billing data.
- Skill 4 never auto-starts resources. A real deployment requires `s4-deploy --execute`, named approval, cost ceiling, artifact lineage, Console review, and explicit cleanup.
- After deployment, create `s4-console-review-packet`, use the Playwright Infrastructure Composer capture, show the redacted canvas image to a named human, then run `s4-close --execute` with the packet, evidence JSON, and `--shared-via`. The code validates evidence metadata, not screenshot pixels.
- A timeout abort requires the packet after its `review_deadline`; deployment or normal-close failures may use the cost-control abort path. Skill 5 renders forced cleanup as `final_without_console_review`, never as an actual-PoC final.
- Skill 5 can only state facts present in S1-S4 artifacts. Unknown remains `unknown`; never use generated filler to make a report sound complete.
- Display `gui_model.cost_quote` as a non-binding PoC estimate: quote ID, low/expected/high totals, recommended approval ceiling, validity and official sources. Never label it as an AWS invoice.
- Refer to the project stage as `Skill 3` or `S3 Evaluate`. Refer to the AWS storage service as `Amazon S3` or `S3 bucket`.

## Frontend Contract

The web API returns original stage artifacts. Skill 5 additionally returns `gui_model`; use that structured object rather than parsing the Markdown string.

The initial UI should support:

1. Direct URL run and discovery run.
2. Candidate comparison with source links, evidence gaps, and Region status.
3. Explicit one-candidate human selection form.
4. Fixed Skill 3 rubric results and stop conditions.
5. S4 validation state; make it visually clear that a validation artifact is not a deployed PoC.
6. Skill 5 report with simple conclusion, verification checklist, unknowns, reminders, and evidence ledger.

## Desired Visual Direction

- Make it a dense, quiet operational workspace, not a marketing landing page.
- Use a left stage rail, a readable evidence table, restrained color, and clear state labels.
- Keep the top report conclusion simple. Put unknowns and reminders in their own lower section.
- No decorative gradients, hero cards, fake metrics, or invented scores.

## S4 Full PoC Boundary

The GUI must not receive permissions to deploy arbitrary CloudFormation templates. The included S4 runner has two registered, candidate-specific recipes:

- `s3_files_cdk`
- `lambda_self_managed_s3_code_storage_cdk`

To design a browser-assisted full PoC later, have the GUI create an approval artifact and submit it to a separate controlled execution service. That service must reuse `build_approval_template` and `build_deployment_context`, allow only registered recipes, and preserve the packet-bound Console review and cleanup sequence.
