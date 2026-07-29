from aws_cdk import Aws, CfnOutput, CfnResource, Fn, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_s3 as s3
from constructs import Construct


class LambdaSelfManagedStoragePocStack(Stack):
    """Deploy one Lambda function whose .zip code is referenced from S3.

    CDK's current L1 ``CodeProperty`` does not expose the new
    ``S3ObjectStorageMode`` property yet, so the target Lambda resource uses
    ``CfnResource`` to preserve the exact CloudFormation contract published by
    AWS. The tiny inline custom-resource provider creates a non-sensitive .zip
    in the versioned bucket before the target function is created.
    """

    def __init__(self, scope: Construct, construct_id: str, *, name_prefix: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.CfnBucket(
            self,
            "DataBucket",
            bucket_name=Fn.sub(f"{name_prefix}-${{AWS::AccountId}}-${{AWS::Region}}"),
            versioning_configuration=s3.CfnBucket.VersioningConfigurationProperty(status="Enabled"),
            bucket_encryption=s3.CfnBucket.BucketEncryptionProperty(
                server_side_encryption_configuration=[
                    s3.CfnBucket.ServerSideEncryptionRuleProperty(
                        server_side_encryption_by_default=s3.CfnBucket.ServerSideEncryptionByDefaultProperty(
                            sse_algorithm="AES256"
                        )
                    )
                ]
            ),
            public_access_block_configuration=s3.CfnBucket.PublicAccessBlockConfigurationProperty(
                block_public_acls=True,
                block_public_policy=True,
                ignore_public_acls=True,
                restrict_public_buckets=True,
            ),
            tags=[
                {"key": "Project", "value": name_prefix},
                {"key": "ManagedBy", "value": "CDK-CloudFormation"},
            ],
        )

        provider_role = iam.CfnRole(
            self,
            "CodeUploaderRole",
            assume_role_policy_document={
                "Version": "2012-10-17",
                "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}],
            },
            managed_policy_arns=[Fn.sub("arn:${AWS::Partition}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole")],
            policies=[
                iam.CfnRole.PolicyProperty(
                    policy_name="upload-self-managed-code",
                    policy_document={
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": ["s3:PutObject", "s3:PutObjectVersion"],
                                "Resource": Fn.sub(f"${{{bucket.logical_id}.Arn}}/artifacts/function.zip"),
                            }
                        ],
                    },
                )
            ],
        )

        uploader = lambda_.CfnFunction(
            self,
            "CodeArtifactUploader",
            runtime="python3.12",
            handler="index.handler",
            role=provider_role.attr_arn,
            timeout=60,
            code=lambda_.CfnFunction.CodeProperty(zip_file=_UPLOADER_CODE),
        )
        uploader.add_dependency(provider_role)
        uploader.add_dependency(bucket)

        code_artifact = CfnResource(
            self,
            "CodeArtifact",
            type="Custom::S4LambdaCodeArtifact",
            properties={
                "ServiceToken": uploader.attr_arn,
                "Bucket": bucket.ref,
                "Key": "artifacts/function.zip",
                "BodyVersion": "v1",
            },
        )
        code_artifact.add_dependency(uploader)

        execution_role = iam.CfnRole(
            self,
            "FunctionExecutionRole",
            assume_role_policy_document={
                "Version": "2012-10-17",
                "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}],
            },
            managed_policy_arns=[Fn.sub("arn:${AWS::Partition}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole")],
        )

        function_name = f"{name_prefix}-function"
        function = CfnResource(
            self,
            "SelfManagedFunction",
            type="AWS::Lambda::Function",
            properties={
                "FunctionName": function_name,
                "Runtime": "python3.12",
                "Handler": "lambda_function.lambda_handler",
                "Role": execution_role.attr_arn,
                "MemorySize": 128,
                "Timeout": 10,
                "Code": {
                    "S3Bucket": bucket.ref,
                    "S3Key": "artifacts/function.zip",
                    "S3ObjectVersion": code_artifact.get_att("VersionId").to_string(),
                    "S3ObjectStorageMode": "REFERENCE",
                },
                "Tags": [
                    {"Key": "Project", "Value": name_prefix},
                    {"Key": "ManagedBy", "Value": "CDK-CloudFormation"},
                ],
            },
        )

        bucket_policy = s3.CfnBucketPolicy(
            self,
            "LambdaCodeReadPolicy",
            bucket=bucket.ref,
            policy_document={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "LambdaSelfManagedCodeAccess",
                        "Effect": "Allow",
                        "Principal": {"Service": "lambda.amazonaws.com"},
                        "Action": ["s3:GetObject", "s3:GetObjectVersion"],
                        "Resource": Fn.sub(f"${{{bucket.logical_id}.Arn}}/artifacts/function.zip"),
                        "Condition": {
                            "StringEquals": {"aws:SourceAccount": Aws.ACCOUNT_ID},
                            "ArnLike": {
                                "aws:SourceArn": Fn.sub(
                                    "arn:${AWS::Partition}:lambda:${AWS::Region}:${AWS::AccountId}:function:${FunctionName}",
                                    {"FunctionName": function_name},
                                )
                            },
                        },
                    }
                ],
            },
        )
        function.add_dependency(code_artifact)
        function.add_dependency(execution_role)
        function.add_dependency(bucket_policy)

        CfnOutput(self, "BucketName", value=bucket.ref)
        CfnOutput(self, "FunctionName", value=function.ref)
        CfnOutput(self, "CodeObjectVersion", value=code_artifact.get_att("VersionId").to_string())
        CfnOutput(self, "CodeStorageMode", value="REFERENCE")


_UPLOADER_CODE = r'''
import io
import zipfile

import boto3
import cfnresponse


FUNCTION_SOURCE = b"""def lambda_handler(event, context):
    return {\"status\": \"ok\", \"storage_mode\": \"REFERENCE\", \"run_id\": event.get(\"run_id\")}
"""


def handler(event, context):
    try:
        if event["RequestType"] == "Delete":
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {}, "s4-lambda-code-artifact")
            return
        body = io.BytesIO()
        with zipfile.ZipFile(body, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("lambda_function.py", FUNCTION_SOURCE)
        response = boto3.client("s3").put_object(
            Bucket=event["ResourceProperties"]["Bucket"],
            Key=event["ResourceProperties"]["Key"],
            Body=body.getvalue(),
            ContentType="application/zip",
        )
        cfnresponse.send(event, context, cfnresponse.SUCCESS, {"VersionId": response["VersionId"]}, "s4-lambda-code-artifact")
    except Exception as error:
        cfnresponse.send(event, context, cfnresponse.FAILED, {"Error": str(error)}, "s4-lambda-code-artifact")
'''
