# Claude GUI Handoff

## Mission

Improve the visual and interaction design of the web UI without changing the evidence, approval, and deployment contracts in the Python core.

## Read First

1. `design-baseline.md`: end-to-end policy and five-stage workflow.
2. `docs/s1-s4-程式碼導讀與註解.md`: core implementation guide.
3. `web-demo-cdk/README.md`: AWS deployment and API contract.
4. `sample-artifacts/lambda-self-managed-code-storage/`: a real S1 through S4 runtime evidence set and an S5 report.

## Non-Negotiable Workflow Rules

- S1 retains both URL import and dynamic discovery through AWS Blogs categories, What's New, and public GitHub search.
- S2 treats Region as evidence with a warning state; it does not silently exclude candidates because Singapore evidence is missing.
- Skill 3 must stop for a human shortlist and its three context fields. Do not automatically rank a landscape result into a winner.
- Skill 4 validation never auto-starts resources. A real deployment requires the existing `s4-deploy --execute` process plus a named approval, cost ceiling, artifact lineage, Console review, and explicit cleanup.
- Skill 5 can only state facts present in S1-S4 artifacts. Unknown remains `unknown`; never use generated filler to make a report sound complete.
- Refer to the project stage as `Skill 3` or `S3 Evaluate`. Refer to the AWS storage service as `Amazon S3` or `S3 bucket`.

## Frontend Contract

The web API returns original stage artifacts. Skill 5 additionally returns `gui_model`; use that structured object rather than parsing the Markdown string.

The initial UI should support:

1. Direct URL run and discovery run.
2. Candidate comparison with source links, evidence gaps, and Region status.
3. Explicit human shortlist form.
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

To design a browser-assisted full PoC later, have the GUI create an approval artifact and submit it to a separate controlled execution service. That service must reuse `build_deployment_context`, allow only registered recipes, and preserve the current Console review and cleanup sequence.
