"""Authenticated API Lambda: start a pipeline execution."""
import json
import os
from datetime import datetime, timezone

import boto3

STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]
sfn = boto3.client("stepfunctions")


def handler(event, context):
    body = json.loads(event.get("body") or "{}")
    run_id = body.get("run_id") or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    result = sfn.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        input=json.dumps({"run_id": run_id, "source": "api"}),
    )
    return {
        "statusCode": 202,
        "headers": {"content-type": "application/json"},
        "body": json.dumps({"run_id": run_id, "execution_arn": result["executionArn"]}),
    }
