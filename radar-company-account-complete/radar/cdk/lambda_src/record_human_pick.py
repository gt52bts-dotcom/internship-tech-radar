"""RQ1 盲測：記錄人類的獨立選擇（在看到 AI 結果「之前」填寫）。

用 CLI 直接 invoke，不經過 Step Functions：

  aws lambda invoke --function-name cathay-techintel-v3-recordhumanpick \
    --cli-binary-format raw-in-base64-out \
    --payload '{
      "run_id": "company-landing-001",
      "picked_ids": ["A03"],
      "reviewer": "grace",
      "human_minutes": 18,
      "blind": true,
      "note": "選 S3 conditional writes，理由：..."
    }' /dev/stdout --region ap-southeast-1

欄位說明：
- picked_ids: 人類選出的候選 id（盲測協議：AI 出 3、人先獨立選，不可先看 AI 結果）
- human_minutes: 人類從開始閱讀到做出決定的總分鐘數（RQ2 分子）
- blind: 是否符合盲測（若已先看過 AI 結果請誠實填 false，該筆不計入 RQ1）
- judgment_correct 預設 pending，事後回填 correct / incorrect / high_risk_miss（RQ3 閘門統計）
"""
from decimal import Decimal

from common import log_pick


def handler(event, context):
    required = ["run_id", "picked_ids", "reviewer"]
    missing = [f for f in required if not event.get(f)]
    if missing:
        return {"statusCode": 400, "error": f"missing fields: {missing}"}

    item = log_pick(event["run_id"], "human", {
        "picked_ids": list(event["picked_ids"]),
        "reviewer": str(event["reviewer"]),
        "human_minutes": Decimal(str(event.get("human_minutes", 0))),
        "blind": bool(event.get("blind", True)),
        "judgment_correct": "pending",
        "note": str(event.get("note", "")),
    })
    return {"statusCode": 200, "recorded": {k: str(v) for k, v in item.items()}}
