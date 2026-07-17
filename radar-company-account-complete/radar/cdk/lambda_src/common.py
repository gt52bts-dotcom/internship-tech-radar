"""Shared Lambda utilities for the v3 tech-intel pipeline."""
import json
import os
from decimal import Decimal
from functools import lru_cache

import boto3

BUCKET = os.environ["BUCKET_NAME"]
PICKS_TABLE = os.environ.get("PICKS_TABLE", "")
ANTHROPIC_SECRET_ARN = os.environ.get("ANTHROPIC_SECRET_ARN", "")
EVALUATOR_MODEL = os.environ.get("EVALUATOR_MODEL", "claude-sonnet-4-5")
VALIDATOR_MODEL = os.environ.get("VALIDATOR_MODEL", "claude-haiku-4-5")
USE_ANTHROPIC = os.environ.get("USE_ANTHROPIC", "true").lower() == "true"
REGION = os.environ.get("AWS_REGION", "ap-southeast-1")

s3 = boto3.client("s3", region_name=REGION)
sm = boto3.client("secretsmanager", region_name=REGION)
ddb = boto3.resource("dynamodb", region_name=REGION)


def _plain_value(value):
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, list):
        return [_plain_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _plain_value(item) for key, item in value.items()}
    return value


def log_pick(run_id, actor, payload, ttl_days=365):
    """把一筆 pick 寫進 DynamoDB（RQ1 盲測資料來源）。

    actor: "ai" 或 "human"。expire_at 觸發 TTL，一年後自動清除。
    """
    from datetime import datetime, timedelta, timezone

    if not PICKS_TABLE:
        return None
    now = datetime.now(timezone.utc)
    item = {
        "run_id": run_id,
        "pick_time": now.isoformat(timespec="seconds"),
        "actor": actor,
        "expire_at": int((now + timedelta(days=ttl_days)).timestamp()),
        **payload,
    }
    ddb.Table(PICKS_TABLE).put_item(Item=item)
    return item


def read_pick_logs(limit=500):
    """Read recent AI/human pick logs for lightweight feedback statistics."""
    if not PICKS_TABLE:
        return []
    table = ddb.Table(PICKS_TABLE)
    items = []
    scan_kwargs = {"Limit": min(limit, 500)}
    while True:
        response = table.scan(**scan_kwargs)
        items.extend(response.get("Items", []))
        if len(items) >= limit or "LastEvaluatedKey" not in response:
            break
        scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
    return [_plain_value(item) for item in items[:limit]]


def presigned_url(s3_key, expires_seconds=43200):
    """產生報表 presigned URL（取代 CloudFront；有效期受 Lambda 角色 session 限制）。"""
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET, "Key": s3_key},
        ExpiresIn=expires_seconds,
    )


def run_id_from_event(event):
    run_id = event.get("run_id")
    if run_id:
        return str(run_id).replace(":", "-")
    # Step Functions scheduler passes execution start time through GenerateRunId.
    return event.get("time", "manual-run").replace(":", "-")


def key(run_id, name):
    return f"runs/{run_id}/{name}"


def read_json(s3_key):
    obj = s3.get_object(Bucket=BUCKET, Key=s3_key)
    return json.loads(obj["Body"].read().decode("utf-8"))


def write_json(s3_key, data):
    body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    s3.put_object(
        Bucket=BUCKET,
        Key=s3_key,
        Body=body,
        ContentType="application/json; charset=utf-8",
    )
    return {"bucket": BUCKET, "key": s3_key, "uri": f"s3://{BUCKET}/{s3_key}"}


def write_html(s3_key, html):
    s3.put_object(
        Bucket=BUCKET,
        Key=s3_key,
        Body=html.encode("utf-8"),
        ContentType="text/html; charset=utf-8",
    )
    return {"bucket": BUCKET, "key": s3_key, "uri": f"s3://{BUCKET}/{s3_key}"}


def write_text(s3_key, text, content_type="text/plain; charset=utf-8"):
    s3.put_object(
        Bucket=BUCKET,
        Key=s3_key,
        Body=text.encode("utf-8"),
        ContentType=content_type,
    )
    return {"bucket": BUCKET, "key": s3_key, "uri": f"s3://{BUCKET}/{s3_key}"}


@lru_cache(maxsize=1)
def anthropic_key():
    if not ANTHROPIC_SECRET_ARN:
        return ""
    value = sm.get_secret_value(SecretId=ANTHROPIC_SECRET_ARN)["SecretString"].strip()
    placeholders = {"", "REPLACE_AFTER_DEPLOY", "PLACEHOLDER", "TODO", "changeme"}
    return "" if value in placeholders else value


@lru_cache(maxsize=1)
def anthropic_client():
    import anthropic

    return anthropic.Anthropic(api_key=anthropic_key())


# 每次 Lambda 執行內累積的 LLM 用量（RQ2：推論時間 + token 都要留痕）
LLM_USAGE = {
    "calls": 0,
    "input_tokens": 0,
    "output_tokens": 0,
    "inference_seconds": 0.0,
    "fallback_count": 0,
    "fallback_errors": [],
}


def reset_llm_usage():
    LLM_USAGE.update(
        calls=0,
        input_tokens=0,
        output_tokens=0,
        inference_seconds=0.0,
        fallback_count=0,
        fallback_errors=[],
    )


def _record_llm_fallback(error):
    LLM_USAGE["fallback_count"] += 1
    message = str(error).replace("\n", " ")
    if len(message) > 240:
        message = message[:237] + "..."
    if len(LLM_USAGE["fallback_errors"]) < 5:
        LLM_USAGE["fallback_errors"].append(message)


def llm_mode_label(llm_approved):
    if not llm_approved:
        return "rubric-only (quote gate: over budget)"
    if not USE_ANTHROPIC:
        return "rubric-only (USE_ANTHROPIC=false)"
    if LLM_USAGE["calls"] and LLM_USAGE["fallback_count"]:
        return "api.anthropic.com-partial-with-rubric-fallback"
    if LLM_USAGE["calls"]:
        return "api.anthropic.com"
    if LLM_USAGE["fallback_count"]:
        return "rubric-only (anthropic failed; fallback used)"
    if not anthropic_key():
        return "rubric-only (missing or placeholder Anthropic key)"
    return "api.anthropic.com-with-rubric-fallback"


def call_anthropic(model, prompt, max_tokens=700):
    if not USE_ANTHROPIC or not anthropic_key():
        return None
    if LLM_USAGE["fallback_count"]:
        return None
    import time

    start = time.monotonic()
    try:
        response = anthropic_client().messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:
        _record_llm_fallback(exc)
        # A rotated or corrected secret should be picked up by the next invocation.
        anthropic_key.cache_clear()
        anthropic_client.cache_clear()
        return None
    LLM_USAGE["calls"] += 1
    LLM_USAGE["inference_seconds"] = round(LLM_USAGE["inference_seconds"] + time.monotonic() - start, 2)
    usage = getattr(response, "usage", None)
    if usage:
        LLM_USAGE["input_tokens"] += getattr(usage, "input_tokens", 0)
        LLM_USAGE["output_tokens"] += getattr(usage, "output_tokens", 0)
    return response.content[0].text


def assert_role_separation():
    """憲法條款：建置者不得驗證自己的輸出 — 程式碼層強制，模型相同直接中止。"""
    if EVALUATOR_MODEL == VALIDATOR_MODEL:
        raise RuntimeError(
            f"Constitution violation: evaluator and validator must be different models "
            f"(both are {EVALUATOR_MODEL}). Fix EVALUATOR_MODEL / VALIDATOR_MODEL env vars."
        )


def step_timer():
    """回傳 (start, finish) 計時器：finish() 給出該步 wall-clock 秒數與 LLM 用量快照。"""
    import time

    reset_llm_usage()
    start = time.monotonic()

    def finish():
        return {
            "step_wall_seconds": round(time.monotonic() - start, 2),
            "llm_usage": dict(LLM_USAGE),
        }

    return finish


def response(run_id, step, output_key, extra=None):
    payload = {"run_id": run_id, "step": step, "output_key": output_key}
    if extra:
        payload.update(extra)
    return payload
