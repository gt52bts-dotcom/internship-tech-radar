"""PipelineStack — Lambda × 5 + Step Functions + EventBridge Scheduler

公司帳戶版（ap-southeast-1 only）：
- AI 呼叫走 api.anthropic.com（不透過 Bedrock），只需 secretsmanager:GetSecretValue。
- log_retention 改為明確 LogGroup（避免舊式 custom resource 在受限帳戶失敗）。
- Cognito + API Gateway 改為 context 開關（-c enable_api=true），預設關閉，
  第一次 CLI 部署把失敗面降到最小。
- 每日排程預設 DISABLED（-c schedule_enabled=true 才開），避免部署當天就開始燒 token。
"""
from aws_cdk import Stack, Duration, CfnOutput, RemovalPolicy
from aws_cdk import aws_lambda as lam
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as sfn_tasks
from aws_cdk import aws_scheduler as scheduler
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from constructs import Construct


class PipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *,
                 prefix: str, bucket, table, anthropic_secret, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        enable_api = str(self.node.try_get_context("enable_api")).lower() == "true"
        schedule_enabled = str(self.node.try_get_context("schedule_enabled")).lower() == "true"

        # 五個 Lambda 共用的環境變數
        common_env = {
            "BUCKET_NAME": bucket.bucket_name,
            "PICKS_TABLE": table.table_name,
            "ANTHROPIC_SECRET_ARN": anthropic_secret.secret_arn,
            "EVALUATOR_MODEL": "claude-sonnet-4-5",
            "VALIDATOR_MODEL": "claude-haiku-4-5",
            "USE_ANTHROPIC": "true",
            "MAX_RUN_USD": self.node.try_get_context("max_run_usd") or "0.50",
        }

        # Lambda Layer：anthropic + feedparser（layer_build/python 已預先打包）
        layer = lam.LayerVersion(
            self, "PythonDependencies",
            code=lam.Code.from_asset("layer_build"),
            compatible_runtimes=[lam.Runtime.PYTHON_3_12],
            description="anthropic + feedparser for tech-intel pipeline",
        )

        def make_lambda(name, handler, timeout=120, memory=512):
            log_group = logs.LogGroup(
                self, f"{name}Logs",
                log_group_name=f"/aws/lambda/{prefix}-{name.lower()}",
                retention=logs.RetentionDays.TWO_WEEKS,
                removal_policy=RemovalPolicy.DESTROY,
            )
            fn = lam.Function(
                self, name,
                function_name=f"{prefix}-{name.lower()}",
                runtime=lam.Runtime.PYTHON_3_12,
                code=lam.Code.from_asset("lambda_src"),
                handler=handler,
                timeout=Duration.seconds(timeout),
                memory_size=memory,
                environment=common_env,
                layers=[layer],
                log_group=log_group,
            )
            bucket.grant_read_write(fn)
            table.grant_read_write_data(fn)
            anthropic_secret.grant_read(fn)
            return fn

        s1 = make_lambda("S1Scan",     "s1_scan.handler",     timeout=120)
        s2 = make_lambda("S2Compare",  "s2_compare.handler")
        s2b = make_lambda("S2bQuote",  "s2b_quote.handler",   timeout=60, memory=256)
        s3 = make_lambda("S3Evaluate", "s3_evaluate.handler", timeout=600)  # LLM 呼叫較久
        s4 = make_lambda("S4Validate", "s4_validate.handler", timeout=600)
        s5 = make_lambda("S5Report",   "s5_report.handler")

        # RQ1 盲測：人類 pick 記錄（CLI 直接 invoke，不進 Step Functions）
        human_pick = make_lambda("RecordHumanPick", "record_human_pick.handler", timeout=30, memory=256)
        CfnOutput(
            self, "RecordHumanPickCommand",
            value=(
                f"aws lambda invoke --function-name {prefix}-recordhumanpick "
                "--cli-binary-format raw-in-base64-out --payload file://pick.json "
                "/dev/stdout --region ap-southeast-1"
            ),
            description="盲測人類選擇記錄（payload 格式見 record_human_pick.py 開頭）",
        )

        # Step Functions 定義（CDK 建構器）
        def task(name, fn):
            return sfn_tasks.LambdaInvoke(
                self, f"Task_{name}", lambda_function=fn,
                payload=sfn.TaskInput.from_object({"run_id.$": "$.run_id"}),
                result_path=f"$.{name.lower()}",
                retry_on_service_exceptions=True,
            )

        generate_id = sfn.Pass(
            self, "GenerateRunId",
            parameters={"run_id.$": "$$.Execution.StartTime"},
        )

        # 報價閘門：Choice 讓狀態機圖上直接看得到「報價合理才下去做」
        quote_task = sfn_tasks.LambdaInvoke(
            self, "Task_Quote", lambda_function=s2b,
            payload=sfn.TaskInput.from_object({"run_id.$": "$.run_id"}),
            result_path="$.quote",
            retry_on_service_exceptions=True,
        )
        t3, t4, t5 = task("S3", s3), task("S4", s4), task("S5", s5)
        llm_branch = t3.next(t4).next(t5)
        rubric_note = sfn.Pass(
            self, "OverBudget_RubricMode",
            comment="報價超出 MAX_RUN_USD：S3/S4 改走零 token rubric 模式",
        ).next(llm_branch)

        quote_choice = (
            sfn.Choice(self, "QuoteApproved?")
            .when(
                sfn.Condition.string_equals("$.quote.Payload.decision", "approve"),
                llm_branch,
            )
            .otherwise(rubric_note)
        )

        pipeline_steps = (
            task("S1", s1)
            .next(task("S2", s2))
            .next(quote_task)
            .next(quote_choice)
        )
        chain = (
            sfn.Choice(self, "RunIdProvided?")
            .when(sfn.Condition.is_present("$.run_id"), pipeline_steps)
            .otherwise(generate_id.next(pipeline_steps))
        )

        sfn_log_group = logs.LogGroup(
            self, "SFNLogs",
            log_group_name=f"/aws/vendedlogs/states/{prefix}-pipeline",
            retention=logs.RetentionDays.TWO_WEEKS,
            removal_policy=RemovalPolicy.DESTROY,
        )
        self.state_machine = sfn.StateMachine(
            self, "Pipeline",
            state_machine_name=f"{prefix}-pipeline",
            definition_body=sfn.DefinitionBody.from_chainable(chain),
            logs=sfn.LogOptions(destination=sfn_log_group, level=sfn.LogLevel.ALL),
        )

        # EventBridge Scheduler：每日 08:00 台北時間（預設 DISABLED）
        scheduler_role = iam.Role(
            self, "SchedulerRole",
            assumed_by=iam.ServicePrincipal("scheduler.amazonaws.com"),
        )
        self.state_machine.grant_start_execution(scheduler_role)

        scheduler.CfnSchedule(
            self, "DailySchedule",
            name=f"{prefix}-daily",
            schedule_expression="cron(0 8 * * ? *)",
            schedule_expression_timezone="Asia/Taipei",
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(mode="OFF"),
            target=scheduler.CfnSchedule.TargetProperty(
                arn=self.state_machine.state_machine_arn,
                role_arn=scheduler_role.role_arn,
                input='{"scheduled": true}',
            ),
            state="ENABLED" if schedule_enabled else "DISABLED",
        )

        CfnOutput(self, "StateMachineArn", value=self.state_machine.state_machine_arn)
        CfnOutput(
            self, "StartCommand",
            value=(
                f"aws stepfunctions start-execution --state-machine-arn "
                f"{self.state_machine.state_machine_arn} "
                '--input "{\\"run_id\\": \\"company-landing-001\\"}" --region ap-southeast-1'
            ),
            description="手動觸發一次 pipeline",
        )

        # 選配：Cognito + API Gateway（cdk deploy -c enable_api=true 才建立）
        if enable_api:
            from aws_cdk import aws_apigateway as apigw
            from aws_cdk import aws_cognito as cognito

            user_pool = cognito.UserPool(
                self, "UserPool",
                user_pool_name=f"{prefix}-users",
                self_sign_up_enabled=False,
                sign_in_aliases=cognito.SignInAliases(email=True),
                removal_policy=RemovalPolicy.DESTROY,
            )
            user_pool_client = cognito.UserPoolClient(
                self, "UserPoolClient",
                user_pool=user_pool,
                auth_flows=cognito.AuthFlow(user_password=True, user_srp=True),
            )
            api_start = lam.Function(
                self, "ApiStartPipeline",
                function_name=f"{prefix}-api-start",
                runtime=lam.Runtime.PYTHON_3_12,
                code=lam.Code.from_asset("lambda_src"),
                handler="api_start.handler",
                timeout=Duration.seconds(30),
                memory_size=256,
                environment={"STATE_MACHINE_ARN": self.state_machine.state_machine_arn},
            )
            self.state_machine.grant_start_execution(api_start)
            api = apigw.RestApi(
                self, "ControlApi",
                rest_api_name=f"{prefix}-api",
                deploy_options=apigw.StageOptions(stage_name="prod"),
            )
            authorizer = apigw.CognitoUserPoolsAuthorizer(
                self, "ApiAuthorizer", cognito_user_pools=[user_pool],
            )
            runs = api.root.add_resource("runs")
            runs.add_method(
                "POST",
                apigw.LambdaIntegration(api_start),
                authorization_type=apigw.AuthorizationType.COGNITO,
                authorizer=authorizer,
            )
            CfnOutput(self, "ControlApiUrl", value=api.url)
            CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id)
            CfnOutput(self, "UserPoolClientId", value=user_pool_client.user_pool_client_id)
