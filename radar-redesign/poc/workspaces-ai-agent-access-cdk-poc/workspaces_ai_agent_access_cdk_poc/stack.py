from aws_cdk import CfnOutput, CfnResource, Fn, Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class WorkSpacesAiAgentAccessPocStack(Stack):
    """Minimal WorkSpaces Applications stack with agent access enabled.

    This PoC validates the managed WorkSpaces Applications agent-access entry
    point. It deliberately avoids custom application images, Bedrock runtime
    deployment, NAT gateways, and S3 screenshot storage so the run stays scoped
    to the infrastructure feature under review.
    """

    def __init__(self, scope: Construct, construct_id: str, *, name_prefix: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.CfnVPC(
            self,
            "Vpc",
            cidr_block="10.82.0.0/16",
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

        subnet_a = ec2.CfnSubnet(
            self,
            "PublicSubnetA",
            availability_zone=Fn.select(0, Fn.get_azs()),
            cidr_block="10.82.1.0/24",
            map_public_ip_on_launch=True,
            vpc_id=vpc.ref,
            tags=[{"key": "Name", "value": f"{name_prefix}-public-a"}],
        )

        subnet_b = ec2.CfnSubnet(
            self,
            "PublicSubnetB",
            availability_zone=Fn.select(1, Fn.get_azs()),
            cidr_block="10.82.2.0/24",
            map_public_ip_on_launch=True,
            vpc_id=vpc.ref,
            tags=[{"key": "Name", "value": f"{name_prefix}-public-b"}],
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
            "PublicSubnetAAssociation",
            route_table_id=route_table.ref,
            subnet_id=subnet_a.ref,
        )

        ec2.CfnSubnetRouteTableAssociation(
            self,
            "PublicSubnetBAssociation",
            route_table_id=route_table.ref,
            subnet_id=subnet_b.ref,
        )

        security_group = ec2.CfnSecurityGroup(
            self,
            "FleetSecurityGroup",
            group_description=f"{name_prefix} WorkSpaces Applications fleet security group",
            vpc_id=vpc.ref,
            security_group_egress=[
                ec2.CfnSecurityGroup.EgressProperty(
                    ip_protocol="-1",
                    cidr_ip="0.0.0.0/0",
                )
            ],
            tags=[{"key": "Name", "value": f"{name_prefix}-fleet-sg"}],
        )

        fleet_name = f"{name_prefix}-fleet"
        stack_name = f"{name_prefix}-stack"

        fleet = CfnResource(
            self,
            "AgentFleet",
            type="AWS::AppStream::Fleet",
            properties={
                "Name": fleet_name,
                "DisplayName": f"{name_prefix} agent fleet",
                "Description": "Run-scoped WorkSpaces Applications fleet for AI agent access PoC.",
                "FleetType": "ON_DEMAND",
                "InstanceType": "stream.standard.medium",
                "ImageName": "Amazon-AppStream2-Sample-Image-06-17-2024",
                "ComputeCapacity": {"DesiredInstances": 1},
                "EnableDefaultInternetAccess": True,
                "MaxUserDurationInSeconds": 3600,
                "DisconnectTimeoutInSeconds": 300,
                "IdleDisconnectTimeoutInSeconds": 300,
                "StreamView": "DESKTOP",
                "VpcConfig": {
                    "SubnetIds": [subnet_a.ref, subnet_b.ref],
                    "SecurityGroupIds": [security_group.ref],
                },
                "Tags": [
                    {"Key": "Project", "Value": name_prefix},
                    {"Key": "ManagedBy", "Value": "CDK-CloudFormation"},
                ],
            },
        )

        app_stack = CfnResource(
            self,
            "AgentStack",
            type="AWS::AppStream::Stack",
            properties={
                "Name": stack_name,
                "DisplayName": f"{name_prefix} agent stack",
                "Description": "WorkSpaces Applications stack with AgentAccessConfig enabled.",
                "AgentAccessConfig": {
                    "Settings": [
                        {"AgentAction": "COMPUTER_VISION", "Permission": "ENABLED"},
                        {"AgentAction": "COMPUTER_INPUT", "Permission": "ENABLED"},
                        {"AgentAction": "FORWARD_MCP_TOOLS", "Permission": "ENABLED"},
                    ],
                    "ScreenResolution": "W_1280xH_720",
                    "ScreenImageFormat": "PNG",
                    "UserControlMode": "VIEW_STOP",
                },
                "Tags": [
                    {"Key": "Project", "Value": name_prefix},
                    {"Key": "ManagedBy", "Value": "CDK-CloudFormation"},
                ],
            },
        )

        association = CfnResource(
            self,
            "AgentStackFleetAssociation",
            type="AWS::AppStream::StackFleetAssociation",
            properties={"FleetName": fleet_name, "StackName": stack_name},
        )
        association.add_dependency(fleet)
        association.add_dependency(app_stack)

        CfnOutput(self, "VpcId", value=vpc.ref)
        CfnOutput(self, "AppStreamFleetName", value=fleet_name)
        CfnOutput(self, "AppStreamStackName", value=stack_name)
        CfnOutput(self, "AgentAccessConfig", value="COMPUTER_VISION,COMPUTER_INPUT,FORWARD_MCP_TOOLS")
        CfnOutput(self, "UserControlMode", value="VIEW_STOP")
        CfnOutput(
            self,
            "StreamingUrlCommand",
            value=Fn.sub(
                "aws appstream create-streaming-url --stack-name ${StackName} --fleet-name ${FleetName} --user-id agentic-radar-s4-agent --validity 600",
                {"StackName": stack_name, "FleetName": fleet_name},
            ),
        )
