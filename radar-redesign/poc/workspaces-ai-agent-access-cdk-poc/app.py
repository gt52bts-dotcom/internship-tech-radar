import aws_cdk as cdk

from workspaces_ai_agent_access_cdk_poc.stack import WorkSpacesAiAgentAccessPocStack


app = cdk.App()

name_prefix = app.node.try_get_context("namePrefix") or "workspaces-agent-poc"
stack_name = app.node.try_get_context("stackName") or "WorkSpacesAiAgentAccessPocStack"

WorkSpacesAiAgentAccessPocStack(
    app,
    stack_name,
    name_prefix=name_prefix,
    synthesizer=cdk.BootstraplessSynthesizer(),
    env=cdk.Environment(region="ap-southeast-1"),
)

app.synth()
