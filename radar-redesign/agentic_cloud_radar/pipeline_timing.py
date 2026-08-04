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
import hashlib
import platform
from typing import Any


SCHEMA_VERSION = "pipeline.timings.v1"
STAGE_ORDER = ("S1", "S2", "S3", "S4", "S5")

# Which CLI command belongs to which stage. Several S4 commands run minutes or
# days apart, so the stage keeps the first start and the last end and counts the
# attempts rather than pretending it was one continuous run.
STAGE_FOR_COMMAND = {
    "s1": "S1",
    "s1-url": "S1",
    "s2": "S2",
    "s3": "S3",
    "s4": "S4",
    "s4-approval-template": "S4",
    "s4-deploy": "S4",
    "s4-console-review-packet": "S4",
    "s4-console-review": "S4",
    "s4-cleanup": "S4",
    "s4-close": "S4",
    "s4-abort": "S4",
    "s5": "S5",
}


def now_iso() -> str:
    """Timezone-aware UTC timestamp. Naive datetimes break cross-process spans."""

    return datetime.now(timezone.utc).isoformat()


def host_fingerprint() -> str:
    """Short non-identifying host hash.

    A run can move between machines mid-pipeline, and their clocks may disagree.
    Recording which host produced each span lets the report flag a cross-host
    interval instead of presenting it as if it were precise.
    """

    raw = f"{platform.node()}|{platform.system()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8]


def merge_stage_record(
    upstream: dict[str, dict[str, Any]] | None,
    stage: str,
    started_at: str,
    ended_at: str,
    command: str = "",
) -> dict[str, dict[str, Any]]:
    """Fold one command's span into the accumulated per-stage record.

    Timings travel inside the artifacts themselves, so no extra state file is
    needed and a run survives being resumed on another machine. A rerun of the
    same stage replaces the end time and increments ``attempt_count`` — taking the
    last attempt rather than summing overlapping spans.
    """

    merged = {k: dict(v) for k, v in (upstream or {}).items()}
    entry = merged.get(stage, {})
    host = host_fingerprint()

    if not entry.get("started_at"):
        entry["started_at"] = started_at
    entry["ended_at"] = ended_at
    entry["attempt_count"] = int(entry.get("attempt_count", 0)) + 1
    hosts = set(entry.get("recorded_on") or [])
    hosts.add(host)
    entry["recorded_on"] = sorted(hosts)
    commands = list(entry.get("commands") or [])
    if command and command not in commands:
        commands.append(command)
    entry["commands"] = commands
    merged[stage] = entry
    return merged


def set_human_wait(
    timings: dict[str, dict[str, Any]] | None,
    stage: str,
    gate_name: str,
    decided_at: str | None,
) -> dict[str, dict[str, Any]]:
    """Derive a stage's human wait from when its gate was actually decided.

    The wait is computed, never typed in. Asking a person to record how long they
    took would be exactly the extra work this pipeline exists to avoid, and a
    self-reported number would not be evidence.
    """

    merged = {k: dict(v) for k, v in (timings or {}).items()}
    entry = merged.get(stage)
    if not entry or not decided_at:
        return merged
    seconds = _seconds(entry.get("ended_at"), decided_at)
    if seconds is None:
        return merged
    entry["human_wait_seconds"] = seconds
    entry["human_gate"] = gate_name
    entry["gate_decided_at"] = decided_at
    merged[stage] = entry
    return merged


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
                "attempt_count": entry.get("attempt_count"),
                "recorded_on": entry.get("recorded_on") or [],
                "cross_host": len(entry.get("recorded_on") or []) > 1,
            }
        )
    recorded = [row for row in rows if row["status"] == "recorded"]
    cross_host = [row["stage"] for row in recorded if row.get("cross_host")]
    started = next((row.get("started_at") for row in recorded if row.get("started_at")), None)
    return {
        "schema_version": SCHEMA_VERSION,
        "rows": rows,
        "machine_seconds_total": round(machine_total, 3),
        "human_wait_seconds_total": round(human_total, 3),
        "human_share": _share(machine_total, human_total),
        "time_to_first_success_seconds": _seconds(started, first_success_at),
        "cross_host_stages": cross_host,
        "measurement_note": (
            "跨主機的區間可能受時鐘差異影響，僅供參考。" if cross_host else ""
        ),
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
