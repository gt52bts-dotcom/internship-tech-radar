from aws_cdk import CfnOutput, CfnParameter, CfnResource, Fn, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from constructs import Construct


class S3FilesCdkPocStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        name_prefix: str,
        create_test_instance: bool,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        latest_ami_id = CfnParameter(
            self,
            "LatestAmiId",
            type="AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>",
            default="/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64",
            description="Latest Amazon Linux 2023 x86_64 AMI.",
        )

        vpc = ec2.CfnVPC(
            self,
            "Vpc",
            cidr_block="10.78.0.0/16",
            enable_dns_hostnames=True,
            enable_dns_support=True,
            tags=[{"key": "Name", "value": f"{name_prefix}-vpc"}],
        )

        internet_gateway = ec2.CfnInternetGateway(
            self,
            "InternetGateway",
            tags=[{"key": "Name", "value": f"{name_prefix}-igw"}],
        )

        ec2.CfnVPCGatewayAttachment(
            self,
            "VpcGatewayAttachment",
            internet_gateway_id=internet_gateway.ref,
            vpc_id=vpc.ref,
        )

        subnet = ec2.CfnSubnet(
            self,
            "PublicSubnet",
            availability_zone=Fn.select(0, Fn.get_azs()),
            cidr_block="10.78.1.0/24",
            map_public_ip_on_launch=True,
            vpc_id=vpc.ref,
            tags=[{"key": "Name", "value": f"{name_prefix}-public-subnet"}],
        )

        route_table = ec2.CfnRouteTable(
            self,
            "PublicRouteTable",
            vpc_id=vpc.ref,
            tags=[{"key": "Name", "value": f"{name_prefix}-public-rt"}],
        )

        public_route = ec2.CfnRoute(
            self,
            "PublicRoute",
            destination_cidr_block="0.0.0.0/0",
            gateway_id=internet_gateway.ref,
            route_table_id=route_table.ref,
        )
        public_route.add_dependency(internet_gateway)

        ec2.CfnSubnetRouteTableAssociation(
            self,
            "PublicSubnetRouteTableAssociation",
            route_table_id=route_table.ref,
            subnet_id=subnet.ref,
        )

        bucket = s3.CfnBucket(
            self,
            "DataBucket",
            bucket_name=Fn.sub(f"{name_prefix}-${{AWS::AccountId}}-${{AWS::Region}}"),
            versioning_configuration=s3.CfnBucket.VersioningConfigurationProperty(
                status="Enabled"
            ),
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

        s3files_role = iam.CfnRole(
            self,
            "S3FilesBucketAccessRole",
            assume_role_policy_document={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "AllowS3FilesAssumeRole",
                        "Effect": "Allow",
                        "Principal": {"Service": "elasticfilesystem.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                        "Condition": {
                            "StringEquals": {"aws:SourceAccount": self.account},
                            "ArnLike": {
                                "aws:SourceArn": Fn.sub(
                                    "arn:${AWS::Partition}:s3files:${AWS::Region}:${AWS::AccountId}:file-system/*"
                                )
                            },
                        },
                    }
                ],
            },
            policies=[
                iam.CfnRole.PolicyProperty(
                    policy_name="s3files-bucket-sync",
                    policy_document={
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Sid": "S3BucketPermissions",
                                "Effect": "Allow",
                                "Action": ["s3:ListBucket", "s3:ListBucketVersions"],
                                "Resource": Fn.get_att(bucket.logical_id, "Arn").to_string(),
                            },
                            {
                                "Sid": "S3ObjectPermissions",
                                "Effect": "Allow",
                                "Action": [
                                    "s3:AbortMultipartUpload",
                                    "s3:DeleteObject*",
                                    "s3:GetObject*",
                                    "s3:List*",
                                    "s3:PutObject*",
                                ],
                                "Resource": Fn.sub(f"${{{bucket.logical_id}.Arn}}/*"),
                            },
                            {
                                "Sid": "EventBridgeManage",
                                "Effect": "Allow",
                                "Action": [
                                    "events:DeleteRule",
                                    "events:DisableRule",
                                    "events:EnableRule",
                                    "events:PutRule",
                                    "events:PutTargets",
                                    "events:RemoveTargets",
                                ],
                                "Resource": Fn.sub(
                                    "arn:${AWS::Partition}:events:*:*:rule/DO-NOT-DELETE-S3-Files*"
                                ),
                                "Condition": {
                                    "StringEquals": {
                                        "events:ManagedBy": "elasticfilesystem.amazonaws.com"
                                    }
                                },
                            },
                            {
                                "Sid": "EventBridgeRead",
                                "Effect": "Allow",
                                "Action": [
                                    "events:DescribeRule",
                                    "events:ListRuleNamesByTarget",
                                    "events:ListRules",
                                    "events:ListTargetsByRule",
                                ],
                                "Resource": Fn.sub(
                                    "arn:${AWS::Partition}:events:*:*:rule/*"
                                ),
                            },
                        ],
                    },
                )
            ],
        )

        file_system = self._cfn_resource(
            "S3FileSystem",
            "AWS::S3Files::FileSystem",
            {
                "AcceptBucketWarning": True,
                "Bucket": Fn.get_att(bucket.logical_id, "Arn").to_string(),
                "Prefix": "poc/",
                "RoleArn": Fn.get_att(s3files_role.logical_id, "Arn").to_string(),
                "Tags": [
                    {"Key": "Name", "Value": f"{name_prefix}-fs"},
                    {"Key": "Project", "Value": name_prefix},
                ],
            },
        )

        client_sg = ec2.CfnSecurityGroup(
            self,
            "ClientSecurityGroup",
            group_description=f"{name_prefix} S3 Files client security group",
            vpc_id=vpc.ref,
            security_group_egress=[
                ec2.CfnSecurityGroup.EgressProperty(
                    ip_protocol="-1",
                    cidr_ip="0.0.0.0/0",
                )
            ],
            tags=[{"key": "Name", "value": f"{name_prefix}-client-sg"}],
        )

        mount_sg = ec2.CfnSecurityGroup(
            self,
            "MountTargetSecurityGroup",
            group_description=f"{name_prefix} S3 Files mount target security group",
            vpc_id=vpc.ref,
            security_group_ingress=[
                ec2.CfnSecurityGroup.IngressProperty(
                    ip_protocol="tcp",
                    from_port=2049,
                    to_port=2049,
                    source_security_group_id=client_sg.ref,
                    description="Allow NFS traffic from the client security group.",
                )
            ],
            security_group_egress=[
                ec2.CfnSecurityGroup.EgressProperty(
                    ip_protocol="-1",
                    cidr_ip="0.0.0.0/0",
                )
            ],
            tags=[{"key": "Name", "value": f"{name_prefix}-mount-target-sg"}],
        )

        mount_target = self._cfn_resource(
            "S3FilesMountTarget",
            "AWS::S3Files::MountTarget",
            {
                "FileSystemId": file_system.get_att("FileSystemId").to_string(),
                "IpAddressType": "IPV4_ONLY",
                "SecurityGroups": [mount_sg.ref],
                "SubnetId": subnet.ref,
            },
        )

        access_point = self._cfn_resource(
            "S3FilesAccessPoint",
            "AWS::S3Files::AccessPoint",
            {
                "FileSystemId": file_system.get_att("FileSystemId").to_string(),
                "PosixUser": {"Uid": "1000", "Gid": "1000"},
                "RootDirectory": {
                    "Path": "/",
                    "CreationPermissions": {
                        "OwnerUid": "1000",
                        "OwnerGid": "1000",
                        "Permissions": "0775",
                    },
                },
                "Tags": [
                    {"Key": "Name", "Value": f"{name_prefix}-access-point"},
                    {"Key": "Project", "Value": name_prefix},
                ],
            },
        )

        client_role = iam.CfnRole(
            self,
            "ClientInstanceRole",
            assume_role_policy_document={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "ec2.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            },
            managed_policy_arns=[
                Fn.sub("arn:${AWS::Partition}:iam::aws:policy/AmazonSSMManagedInstanceCore"),
                Fn.sub("arn:${AWS::Partition}:iam::aws:policy/AmazonS3FilesClientFullAccess"),
            ],
            policies=[
                iam.CfnRole.PolicyProperty(
                    policy_name="s3files-client-bucket-read",
                    policy_document={
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Sid": "S3DirectReadOptimization",
                                "Effect": "Allow",
                                "Action": ["s3:GetObject", "s3:GetObjectVersion"],
                                "Resource": Fn.sub(f"${{{bucket.logical_id}.Arn}}/*"),
                            },
                            {
                                "Sid": "S3BucketListAccess",
                                "Effect": "Allow",
                                "Action": "s3:ListBucket",
                                "Resource": Fn.get_att(bucket.logical_id, "Arn").to_string(),
                            },
                        ],
                    },
                )
            ],
        )

        instance_profile = iam.CfnInstanceProfile(
            self,
            "ClientInstanceProfile",
            roles=[client_role.ref],
        )

        file_system_policy = self._cfn_resource(
            "S3FilesFileSystemPolicy",
            "AWS::S3Files::FileSystemPolicy",
            {
                "FileSystemId": file_system.get_att("FileSystemId").to_string(),
                "Policy": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "AllowClientViaAccessPoint",
                            "Effect": "Allow",
                            "Principal": {
                                "AWS": Fn.get_att(client_role.logical_id, "Arn").to_string()
                            },
                            "Action": ["s3files:ClientMount", "s3files:ClientWrite"],
                            "Condition": {
                                "StringEquals": {
                                    "s3files:AccessPointArn": access_point.get_att(
                                        "AccessPointArn"
                                    ).to_string()
                                }
                            },
                        }
                    ],
                },
            },
        )

        test_instance = None
        if create_test_instance:
            user_data = Fn.sub(
                """#!/bin/bash
set -euxo pipefail
dnf -y update
dnf -y install amazon-efs-utils python3-pip
python3 -m pip install --user botocore || true
mkdir -p /mnt/s3files
for i in $(seq 1 20); do
  if mount -t s3files ${FileSystemId}:/ /mnt/s3files; then
    echo "mounted by cdk userdata at $(date -Iseconds)" > /mnt/s3files/cdk-userdata-mounted.txt
    sync
    break
  fi
  sleep 30
done
findmnt -T /mnt/s3files || true
""",
                {"FileSystemId": file_system.get_att("FileSystemId").to_string()},
            )

            test_instance = ec2.CfnInstance(
                self,
                "TestInstance",
                iam_instance_profile=instance_profile.ref,
                image_id=latest_ami_id.value_as_string,
                instance_type="t3.micro",
                network_interfaces=[
                    ec2.CfnInstance.NetworkInterfaceProperty(
                        associate_public_ip_address=True,
                        device_index="0",
                        group_set=[client_sg.ref],
                        subnet_id=subnet.ref,
                    )
                ],
                tags=[{"key": "Name", "value": f"{name_prefix}-test-client"}],
                user_data=Fn.base64(user_data),
            )
            test_instance.add_dependency(mount_target)
            test_instance.add_dependency(access_point)
            test_instance.add_dependency(file_system_policy)

        CfnOutput(self, "BucketName", value=bucket.ref)
        CfnOutput(self, "VpcId", value=vpc.ref)
        CfnOutput(self, "PublicSubnetId", value=subnet.ref)
        CfnOutput(self, "ClientSecurityGroupId", value=client_sg.ref)
        CfnOutput(
            self,
            "FileSystemId",
            value=file_system.get_att("FileSystemId").to_string(),
        )
        CfnOutput(
            self,
            "MountTargetId",
            value=mount_target.get_att("MountTargetId").to_string(),
        )
        CfnOutput(
            self,
            "AccessPointId",
            value=access_point.get_att("AccessPointId").to_string(),
        )
        CfnOutput(
            self,
            "MountCommand",
            value=Fn.sub(
                "sudo mkdir -p /mnt/s3files && sudo mount -t s3files ${FileSystemId}:/ /mnt/s3files",
                {"FileSystemId": file_system.get_att("FileSystemId").to_string()},
            ),
        )
        if test_instance is not None:
            CfnOutput(self, "TestInstanceId", value=test_instance.ref)

    def _cfn_resource(self, logical_id: str, resource_type: str, properties: dict):
        return CfnResource(
            self,
            logical_id,
            type=resource_type,
            properties=properties,
        )
