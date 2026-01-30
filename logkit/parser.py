from __future__ import annotations
from datetime import datetime, timezone

from dataclasses import dataclass
import json
from typing import Iterable, Optional


@dataclass(frozen=True)
class Event:
    ts: str
    level: str
    msg: str
    src_ip: str


def iter_events(path: str, strict: bool = False, since: Optional[str] = None, until: Optional[str] = None,) -> Iterable[Event]:

    since_dt = parse_ts(since) if since else None
    until_dt = parse_ts(until) if until else None

    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)

                ev = Event(
                    ts=str(obj.get("ts", "")),
                    level=str(obj.get("level", "UNKNOWN")),
                    msg=str(obj.get("msg", "")),
                    src_ip=str(obj.get("src_ip", "")),
                )
                if since_dt or until_dt:
                    if not ev.ts:
                        continue
                    ev_ts = parse_ts(ev.ts)
                    if since_dt and ev_ts < since_dt:
                        continue
                    if until_dt and ev_ts > until_dt:
                        continue

                yield ev
            except json.JSONDecodeError as e:
                if strict:
                    raise ValueError(
                        f"Bad JSON on line {line_no}: {e.msg}") from e
                continue


def count_by_level(
    events: Iterable[Event],
    src_ip: Optional[str] = None,
    contains: Optional[str] = None,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    needle = contains.lower() if contains else None

    for ev in events:
        if src_ip and ev.src_ip != src_ip:
            continue
        if needle and needle not in ev.msg.lower():
            continue
        counts[ev.level] = counts.get(ev.level, 0) + 1

    return counts


def top_src_ips(
    events: Iterable[Event],
    n: int = 5,
    contains: Optional[str] = None,
) -> list[tuple[str, int]]:
    needle = contains.lower() if contains else None
    counts: dict[str, int] = {}

    for ev in events:
        if needle and needle not in ev.msg.lower():
            continue
        counts[ev.src_ip] = counts.get(ev.src_ip, 0) + 1

    return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:n]


def parse_ts(ts: str) -> datetime:
    # expects ISO8601 like 2026-01-30T05:00:01Z
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts).astimezone(timezone.utc)
