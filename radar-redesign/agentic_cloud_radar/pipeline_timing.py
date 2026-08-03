"""Per-stage timing for the S1-S5 pipeline.

Total elapsed time is not the useful number.  Almost all of it is a person
deciding something, so a single figure would say the pipeline is slow when the
code ran in seconds.  Each stage therefore records two clocks:

    machine_seconds     the stage's own computation and fetching
    human_wait_seconds  time parked at a human gate

Reporting them apart is what makes the result honest.  If the machine total is
under a minute and the human total is three days, the finding is that the
bottleneck is the approval path, not the tooling — and that is the number a
company actually needs when it estimates adoption effort.

``time_to_first_success`` spans S1's start to the first verified S4 run, giving
one comparable figure for how much friction a candidate carries.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION = "pipeline.timings.v1"
STAGE_ORDER = ("S1", "S2", "S3", "S4", "S5")


def build_stage_timings(
    stages: dict[str, dict[str, Any]] | None,
    first_success_at: str | None = None,
) -> dict[str, Any]:
    """Return the timing block Skill 5 renders.

    ``stages`` maps a stage code to ``started_at``/``ended_at`` ISO timestamps and
    an optional ``human_gate`` name and ``human_wait_seconds``.
    """

    rows: list[dict[str, Any]] = []
    machine_total = 0.0
    human_total = 0.0
    for code in STAGE_ORDER:
        entry = (stages or {}).get(code)
        if not entry:
            rows.append({"stage": code, "status": "not_recorded"})
            continue
        machine = _seconds(entry.get("started_at"), entry.get("ended_at"))
        human = _non_negative(entry.get("human_wait_seconds"))
        machine_total += machine or 0.0
        human_total += human or 0.0
        rows.append(
            {
                "stage": code,
                "status": "recorded",
                "started_at": entry.get("started_at"),
                "ended_at": entry.get("ended_at"),
                "machine_seconds": machine,
                "human_wait_seconds": human,
                "human_gate": entry.get("human_gate"),
            }
        )
    recorded = [row for row in rows if row["status"] == "recorded"]
    started = next((row.get("started_at") for row in recorded if row.get("started_at")), None)
    return {
        "schema_version": SCHEMA_VERSION,
        "rows": rows,
        "machine_seconds_total": round(machine_total, 3),
        "human_wait_seconds_total": round(human_total, 3),
        "human_share": _share(machine_total, human_total),
        "time_to_first_success_seconds": _seconds(started, first_success_at),
        "reading_note": (
            "machine 是程式耗時，human 是卡在人工關卡的等待。兩者分開呈現："
            "若 human 遠大於 machine，瓶頸在決策流程而不在工具。"
        ),
    }


def _seconds(start: str | None, end: str | None) -> float | None:
    first, second = _parse(start), _parse(end)
    if not first or not second:
        return None
    delta = (second - first).total_seconds()
    return round(delta, 3) if delta >= 0 else None


def _share(machine_total: float, human_total: float) -> float | None:
    combined = machine_total + human_total
    if combined <= 0:
        return None
    return round(human_total / combined, 4)


def _non_negative(value: Any) -> float | None:
    if not isinstance(value, (int, float)):
        return None
    return float(value) if value >= 0 else None


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
