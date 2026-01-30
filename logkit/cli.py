from __future__ import annotations
import json
import argparse
from logkit.parser import iter_events, count_by_level, top_src_ips
from pathlib import Path
from typing import Optional
import csv


def emit(text: str, out_path: Optional[str]) -> None:
    if out_path:
        Path(out_path).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Count log events by level (line-delimited JSON).")
    ap.add_argument("path", help="Path to log file")
    ap.add_argument(
        "--src-ip", help="Filter to a single source IP", default=None)
    ap.add_argument(
        "--contains", help="Only include events whose message contains this text", default=None)
    ap.add_argument("--top-src", type=int, default=0,
                    help="Show top N source IPs (0 disables)")
    ap.add_argument("--strict", action="store_true",
                    help="Fail on the first bad JSON line")
    ap.add_argument(
        "--since",
        default=None,
        help="Only include events at/after this timestamp (ISO8601, e.g. 2026-01-30T05:00:03Z)",
    )
    ap.add_argument(
        "--until",
        default=None,
        help="Only include events at/before this timestamp (ISO8601, e.g. 2026-01-30T05:00:04Z)",
    )
    ap.add_argument("--json", action="store_true",
                    help="Output results as JSON")
    ap.add_argument("--out", default=None,
                    help="Write output to this file instead of stdout")
    ap.add_argument("--top-src-csv", default=None,
                    help="Write top source IPs as CSV to this file")
    ap.add_argument("--quiet", action="store_true",
                    help="Do not print text output (useful when writing files)")

    args = ap.parse_args()
    if args.top_src_csv and args.top_src == 0:
        args.top_src = 5

    # 1) compute counts
    counts = count_by_level(iter_events(args.path, strict=args.strict, since=args.since, until=args.until),
                            src_ip=args.src_ip, contains=args.contains)

    if not counts:
        print("No events matched.")
        return 0

    # 2) build result object here for JSON output
    result = {
        "path": args.path,
        "filters": {
            "src_ip": args.src_ip,
            "contains": args.contains,
            "since": args.since,
            "until": args.until,
            "strict": args.strict,
        },
        "counts_by_level": counts,
    }

    if args.top_src:
        result["top_src_ips"] = [
            {"src_ip": ip, "count": c}
            for ip, c in top_src_ips(
                iter_events(args.path, strict=args.strict,
                            since=args.since, until=args.until),
                n=args.top_src,
                contains=args.contains,
            )
        ]
        if args.top_src_csv:
            with open(args.top_src_csv, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["src_ip", "count"])
                w.writeheader()
                w.writerows(result.get("top_src_ips", []))

    # 3) JSON mode output HERE (before text printing)
    if args.json:
        emit(json.dumps(result, indent=2, sort_keys=True), args.out)
        return 0

    # 4) existing text output continues below
    lines: list[str] = []
    width = max(len(k) for k in counts)
    for level in sorted(counts):
        lines.append(f"{level:<{width}}  {counts[level]}")

    if args.top_src:
        lines.append("")
        lines.append("Top source IPs:")
        for row in result["top_src_ips"]:
            lines.append(f'{row["src_ip"]}  {row["count"]}')

    text_output = "\n".join(lines)

    # Always write to file if requested
    if args.out:
        emit(text_output, args.out)

    # Only print to stdout if not quiet AND not writing to a file
    if (not args.quiet) and (not args.out):
        emit(text_output, None)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
