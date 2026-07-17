"""RQ1 盲測 / human review gate：記錄人類的獨立選擇與審查決策。

用 CLI 直接 invoke，不經過 Step Functions：

  aws lambda invoke --function-name cathay-techintel-v3-recordhumanpick \
    --cli-binary-format raw-in-base64-out \
    --payload '{
      "run_id": "company-landing-001",
      "decision": "override",
      "picked_ids": ["A03"],
      "reviewer": "grace",
      "human_minutes": 18,
      "blind": true,
      "note": "選 S3 conditional writes，理由：..."
    }' /dev/stdout --region ap-southeast-1

欄位說明：
- picked_ids: 人類選出的候選 id（盲測協議：AI 出 3、人先獨立選，不可先看 AI 結果）
- decision: approve / reject / override / comment；盲測時可省略，預設 comment
- human_minutes: 人類從開始閱讀到做出決定的總分鐘數（RQ2 分子）
- blind: 是否符合盲測（若已先看過 AI 結果請誠實填 false，該筆不計入 RQ1）
- judgment_correct 預設 pending，事後回填 correct / incorrect / high_risk_miss（RQ3 閘門統計）
"""
from decimal import Decimal

from common import log_pick

ALLOWED_DECISIONS = {"approve", "reject", "override", "comment"}


def handler(event, context):
    required = ["run_id", "reviewer"]
    missing = [f for f in required if not event.get(f)]
    if missing:
        return {"statusCode": 400, "error": f"missing fields: {missing}"}
    decision = str(event.get("decision", "comment")).lower()
    if decision not in ALLOWED_DECISIONS:
        return {"statusCode": 400, "error": f"decision must be one of {sorted(ALLOWED_DECISIONS)}"}
    picked_ids = list(event.get("picked_ids", []))
    if decision in {"approve", "override"} and not picked_ids:
        return {"statusCode": 400, "error": "picked_ids is required for approve or override"}

    item = log_pick(event["run_id"], "human", {
        "decision": decision,
        "picked_ids": picked_ids,
        "approved": decision == "approve",
        "rejected": decision == "reject",
        "override": decision == "override",
        "review_status": "complete" if decision in {"approve", "reject", "override"} else "comment_only",
        "reviewer": str(event["reviewer"]),
        "human_minutes": Decimal(str(event.get("human_minutes", 0))),
        "blind": bool(event.get("blind", True)),
        "judgment_correct": "pending",
        "review_packet_key": str(event.get("review_packet_key", "")),
        "evidence_ledger_key": str(event.get("evidence_ledger_key", "")),
        "rationale": str(event.get("rationale", event.get("note", ""))),
        "note": str(event.get("note", "")),
    })
    return {"statusCode": 200, "recorded": {k: str(v) for k, v in item.items()}}
