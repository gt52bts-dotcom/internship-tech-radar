import aws_cdk as cdk

from lambda_self_managed_storage_cdk_poc.stack import LambdaSelfManagedStoragePocStack


app = cdk.App()
stack_name = app.node.try_get_context("stackName") or "LambdaSelfManagedStoragePocStack"
name_prefix = app.node.try_get_context("namePrefix") or "lambda-self-managed-poc"

LambdaSelfManagedStoragePocStack(
    app,
    stack_name,
    name_prefix=name_prefix,
    synthesizer=cdk.BootstraplessSynthesizer(),
    env=cdk.Environment(region="ap-southeast-1"),
)

app.synth()
