# CloudFormation and YAML Note

The deployment source is AWS CDK, which synthesizes CloudFormation templates into `cdk/cdk.out`.

Why YAML matters:

- CloudFormation YAML is a reviewable infrastructure-as-code format.
- It lets supervisors inspect resources, IAM changes, and deployment intent before creation.
- It is more portable than manual AWS Console steps.
- It helps prove that the deployment can be rebuilt, audited, and handed over.

Current project status:

- CDK app source: `cdk/app.py`
- CDK stack source: `cdk/stacks/*.py`
- Synthesized CloudFormation assembly: `cdk/cdk.out`
- Cost estimate YAML: `docs/cost-estimate.yaml`
- Runtime S3 output after S5: `reports/cost-estimate.yaml`

Useful commands:

```powershell
cd cdk
cdk.cmd synth
cdk.cmd deploy --all
cdk.cmd destroy --all
```

The current implementation intentionally excludes Bedrock to keep company-account landing validation within the USD 100 budget.
