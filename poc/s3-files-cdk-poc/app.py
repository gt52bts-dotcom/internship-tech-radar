import aws_cdk as cdk

from s3_files_cdk_poc.stack import S3FilesCdkPocStack


app = cdk.App()

name_prefix = app.node.try_get_context("namePrefix") or "s3files-cdk-poc"
create_test_instance = str(app.node.try_get_context("createTestInstance") or "true").lower() == "true"

S3FilesCdkPocStack(
    app,
    "S3FilesCdkPocStack",
    name_prefix=name_prefix,
    create_test_instance=create_test_instance,
    synthesizer=cdk.BootstraplessSynthesizer(),
    env=cdk.Environment(region="ap-southeast-1"),
)

app.synth()
