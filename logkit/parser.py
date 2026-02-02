from __future__ import annotations
from datetime import datetime, timezone

from dataclasses import dataclass
import json
from typing import Iterable, Optional


@dataclass(frozen=True)
class Event:
    """
    Represents a single log event parsed from a JSON log file.

    Immutable data class with the following fields:
    - ts: Timestamp in ISO8601 format (e.g., "2026-01-30T05:00:01Z")
    - level: Log level (e.g., "INFO", "WARN", "ERROR")
    - msg: Log message text content
    - src_ip: Source IP address of the event origin
    """
    ts: str
    level: str
    msg: str
    src_ip: str


def iter_events(
    path: str,
    strict: bool = False,
    since: Optional[str] = None,
    until: Optional[str] = None,
) -> Iterable[Event]:
    """
    Generator function that reads and parses a line-delimited JSON log file.

    Yields Event objects after applying optional timestamp range filters.
    Uses lazy evaluation (generator pattern) for memory efficiency with large files.

    Args:
        path: Path to the log file to parse
        strict: If True, raise ValueError on first malformed JSON. If False, skip bad lines.
        since: Optional ISO8601 timestamp; only yield events at/after this time
        until: Optional ISO8601 timestamp; only yield events at/before this time

    Yields:
        Event objects matching the filter criteria

    Raises:
        ValueError: If strict=True and a line contains invalid JSON
        FileNotFoundError: If the specified log file does not exist

    Example:
        for event in iter_events("logs.jsonl", since="2026-01-30T00:00:00Z"):
            print(f"{event.level}: {event.msg}")
    """
    # ==================== PARSE OPTIONAL TIMESTAMP FILTERS ====================
    # Convert timestamp filter strings to datetime objects for comparison
    since_dt = parse_ts(since) if since else None
    until_dt = parse_ts(until) if until else None

    # ==================== READ LOG FILE ====================
    # Open the log file in UTF-8 encoding for processing
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            # Remove leading/trailing whitespace from line
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # ==================== PARSE JSON LINE ====================
            try:
                # Attempt to parse line as JSON object
                obj = json.loads(line)

                # ==================== EXTRACT EVENT FIELDS ====================
                # Build Event object from JSON fields with fallbacks to empty/default values
                ev = Event(
                    ts=str(obj.get("ts", "")),
                    level=str(obj.get("level", "UNKNOWN")),
                    msg=str(obj.get("msg", "")),
                    src_ip=str(obj.get("src_ip", "")),
                )

                # ==================== APPLY TIMESTAMP RANGE FILTERS ====================
                # If timestamp filters are specified, check if event falls within range
                if since_dt or until_dt:
                    # Skip events without timestamps when filtering by time
                    if not ev.ts:
                        continue

                    # Parse event timestamp for comparison
                    ev_ts = parse_ts(ev.ts)

                    # Skip if event is before the "since" cutoff
                    if since_dt and ev_ts < since_dt:
                        continue

                    # Skip if event is after the "until" cutoff
                    if until_dt and ev_ts > until_dt:
                        continue

                # ==================== YIELD FILTERED EVENT ====================
                # Yield event that passes all filter criteria
                yield ev

            # ==================== ERROR HANDLING ====================
            except json.JSONDecodeError as e:
                # In strict mode, raise an error immediately on malformed JSON
                if strict:
                    raise ValueError(
                        f"Bad JSON on line {line_no}: {e.msg}") from e
                # Otherwise, silently skip the bad line and continue
                continue


def count_by_level(
    events: Iterable[Event],
    src_ip: Optional[str] = None,
    contains: Optional[str] = None,
) -> dict[str, int]:
    """
    Aggregates events by log level, with optional filtering by source IP and message content.

    Consumes the provided event iterable and returns a dictionary mapping each log level
    to the count of events at that level matching the specified filters.

    Args:
        events: Iterable of Event objects to aggregate
        src_ip: Optional source IP address to filter by (exact match)
        contains: Optional substring to search for in message text (case-insensitive)

    Returns:
        Dictionary mapping log level strings to count integers

    Example:
        counts = count_by_level(iter_events("logs.jsonl"), src_ip="10.0.0.5")
        print(f"INFO events: {counts.get('INFO', 0)}")
    """
    """
    Identifies and returns the top N source IP addresses by frequency.
    
    Scans through the event iterable, counts occurrences of each source IP,
    and returns the top N entries sorted by count in descending order.
    
    Args:
        events: Iterable of Event objects to analyze
        n: Number of top IPs to return (default: 5)
        contains: Optional substring filter for message content (case-insensitive)
    
    Returns:
        List of (source_ip, count) tuples sorted by count descending, limited to top N
    
    Example:
        top_5 = top_src_ips(iter_events("logs.jsonl"), n=5)
        for ip, count in top_5:
            print(f"{ip}: {count} events")
    """
    # Pre-process the search string for case-insensitive substring matching
    needle = contains.lower() if contains else None

    # Initialize dictionary to count occurrences of each source IP
    counts: dict[str, int] = {}

    # ==================== ITERATE EVENTS AND COUNT IPs ====================
    for ev in events:
        # ==================== OPTIONAL MESSAGE FILTER ====================
        # Skip events whose messages don't contain the search string
        if needle and needle not in ev.msg.lower():
            continue

        # ==================== INCREMENT IP COUNT ====================
        # Increment counter for this source IP (initialize to 0 if first occurrence)
        counts[ev.src_ip] = counts.get(ev.src_ip, 0) + 1

    # ==================== SORT AND RETURN TOP N ====================
    # Sort all IPs by count (descending) and return only the top N entries
    # sorted() with reverse=True gives highest counts first    # ==================== ITERATE AND FILTER EVENTS ====================
    for ev in events:
        # ==================== SOURCE IP FILTER ====================
        # Skip event if source IP filter is specified and doesn't match
        if src_ip and ev.src_ip != src_ip:
            continue
    """
    Converts an ISO8601 timestamp string to a UTC datetime object.
    
    Handles ISO8601 timestamps with optional 'Z' suffix (Zulu/UTC indicator).
    Converts 'Z' to '+00:00' notation for Python's datetime.fromisoformat() parsing.
    All returned datetime objects are in UTC timezone.
    
    Args:
        ts: ISO8601 timestamp string (e.g., "2026-01-30T05:00:01Z")
    
    Returns:
        datetime object in UTC timezone
    
    Raises:
        ValueError: If timestamp string is not in valid ISO8601 format
    
    Example:
        dt = parse_ts("2026-01-30T05:00:01Z")
        print(dt.isoformat())  # 2026-01-30T05:00:01+00:00
    """
    # ==================== NORMALIZE TIMESTAMP FORMAT ====================
    # Replace trailing 'Z' (UTC indicator) with '+00:00' for datetime.fromisoformat()
    # ISO8601 format allows both representations, but Python's parser expects the latter
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"

    # ==================== PARSE AND RETURN ====================
    # Parse the normalized ISO8601 string and convert to UTC timezone filter is specified and message doesn't contain needle
        if needle and needle not in ev.msg.lower():
            continue

        # ==================== ACCUMULATE COUNT ====================
        # Increment count for this log level (initialize to 0 if first occurrence)
        counts[ev.level] = counts.get(ev.level, 0) + 1

    # ==================== RETURN AGGREGATED COUNTS ====================
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
