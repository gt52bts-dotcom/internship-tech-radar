"""Minimal HTTP API for the AWS-hosted radar demo.

The API invokes the same S1-S5 Python functions used by the CLI and stores
each result as an immutable JSON artifact in a private S3 bucket.  It never
starts an S4 PoC deployment: that remains the separate approval + explicit
CLI runner in ``agentic_cloud_radar.s4_deployer``.
"""

from __future__ import annotations

import base64
import json
import os
from typing import Any

import boto3

from agentic_cloud_radar.s1 import build_direct_url_scan, build_scan
from agentic_cloud_radar.s2 import build_compare
from agentic_cloud_radar.s3 import build_evaluate
from agentic_cloud_radar.s4 import build_validate
from agentic_cloud_radar.s5 import build_report


BUCKET = os.environ["ARTIFACT_BUCKET"]
S3 = boto3.client("s3")


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Route API Gateway requests without any framework dependency."""

    try:
        method = str(event.get("httpMethod") or "GET").upper()
        path = str(event.get("path") or "/").rstrip("/") or "/"
        if method == "GET" and path == "/health":
            return _response(200, {"status": "ok"})
        if method == "POST" and path == "/runs/url":
            return _start_url_run(_body(event))
        if method == "POST" and path == "/runs/discovery":
            return _start_discovery_run(_body(event))
        parts = [part for part in path.split("/") if part]
        if len(parts) == 4 and parts[0] == "runs" and parts[2] == "artifacts" and method == "GET":
            return _response(200, _load(parts[1], parts[3]))
        if len(parts) == 3 and parts[0] == "runs" and method == "POST":
            return _advance_run(parts[1], parts[2], _body(event))
        return _response(404, {"message": "Unknown route."})
    except KeyError as error:
        return _response(404, {"message": f"Artifact not found: {error}"})
    except (TypeError, ValueError) as error:
        return _response(400, {"message": str(error)})
    except Exception as error:  # API callers receive no internal implementation details.
        return _response(500, {"message": "Radar run could not be completed.", "error_type": type(error).__name__})


def _start_url_run(payload: dict[str, Any]) -> dict[str, Any]:
    url = str(payload.get("url") or "").strip()
    if not url:
        raise ValueError("url is required")
    scan = build_direct_url_scan(url).to_dict()
    _save(scan["run_id"], "s1", scan)
    compare = build_compare(scan).to_dict()
    _save(scan["run_id"], "s2", compare)
    return _response(201, {"run_id": scan["run_id"], "s1": scan, "s2": compare})


def _start_discovery_run(payload: dict[str, Any]) -> dict[str, Any]:
    scan = build_scan(payload).to_dict()
    _save(scan["run_id"], "s1", scan)
    compare = build_compare(scan).to_dict()
    _save(scan["run_id"], "s2", compare)
    return _response(201, {"run_id": scan["run_id"], "s1": scan, "s2": compare})


def _advance_run(run_id: str, action: str, payload: dict[str, Any]) -> dict[str, Any]:
    if action == "shortlist":
        result = build_evaluate(_load(run_id, "s2"), payload).to_dict()
        _save(run_id, "s3", result)
        return _response(201, result)
    if action == "validate":
        result = build_validate(_load(run_id, "s3"), payload or None).to_dict()
        _save(run_id, "s4", result)
        return _response(201, result)
    if action == "report":
        result = build_report(
            _load(run_id, "s1"),
            _load_optional(run_id, "s2"),
            _load_optional(run_id, "s3"),
            _load_optional(run_id, "s4"),
            _load_optional(run_id, "s4-runtime"),
        )
        _save(run_id, "s5", result)
        return _response(201, result)
    raise ValueError("Action must be shortlist, validate, or report.")


def _key(run_id: str, stage: str) -> str:
    safe_run = "".join(char for char in run_id if char.isalnum() or char in "-_")
    safe_stage = "".join(char for char in stage if char.isalnum() or char in "-_")
    if not safe_run or not safe_stage:
        raise ValueError("Invalid artifact identity.")
    return f"runs/{safe_run}/{safe_stage}.json"


def _save(run_id: str, stage: str, artifact: dict[str, Any]) -> None:
    S3.put_object(
        Bucket=BUCKET,
        Key=_key(run_id, stage),
        Body=(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        ContentType="application/json; charset=utf-8",
        ServerSideEncryption="AES256",
    )


def _load(run_id: str, stage: str) -> dict[str, Any]:
    response = S3.get_object(Bucket=BUCKET, Key=_key(run_id, stage))
    return json.loads(response["Body"].read().decode("utf-8"))


def _load_optional(run_id: str, stage: str) -> dict[str, Any] | None:
    try:
        return _load(run_id, stage)
    except S3.exceptions.NoSuchKey:
        return None


def _body(event: dict[str, Any]) -> dict[str, Any]:
    body = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")
    parsed = json.loads(body)
    if not isinstance(parsed, dict):
        raise ValueError("Request body must be a JSON object.")
    return parsed


def _response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json; charset=utf-8", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body, ensure_ascii=False),
    }
