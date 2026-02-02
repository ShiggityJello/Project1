from __future__ import annotations
import json
import argparse
from logkit.parser import iter_events, count_by_level, top_src_ips
from pathlib import Path
from typing import Optional
import csv


def emit(text: str, out_path: Optional[str]) -> None:
    """
    Output helper function that writes text to either a file or stdout.
    
    Args:
        text: The text content to output
        out_path: File path to write to, or None to print to stdout
    """
    if out_path:
        # Write to file
        Path(out_path).write_text(text + "\n", encoding="utf-8")
    else:
        # Print to stdout
        print(text)


def main() -> int:
    """
    Main entry point for the LogKit CLI application.
    
    Responsibilities:
    1. Parse and validate command-line arguments
    2. Load and filter log events from the specified file
    3. Aggregate log counts by level and optionally by source IP
    4. Generate output in requested format (text, JSON, or CSV)
    5. Write to file or stdout as specified
    
    Returns:
        0 on success, non-zero on error
    """
    # ==================== ARGUMENT PARSING ====================
    # Configure command-line argument parser with all available options
    ap = argparse.ArgumentParser(
        description="Count log events by level (line-delimited JSON).")
    
    # Positional argument: path to log file
    ap.add_argument("path", help="Path to log file")
    
    # Optional filtering arguments
    ap.add_argument(
        "--src-ip", help="Filter to a single source IP", default=None)
    ap.add_argument(
        "--contains", help="Only include events whose message contains this text", default=None)
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
    
    # Output format and destination arguments
    ap.add_argument("--json", action="store_true",
                    help="Output results as JSON")
    ap.add_argument("--out", default=None,
                    help="Write output to this file instead of stdout")
    ap.add_argument("--quiet", action="store_true",
                    help="Do not print text output (useful when writing files)")
    
    # Top source IPs arguments
    ap.add_argument("--top-src", type=int, default=0,
                    help="Show top N source IPs (0 disables)")
    ap.add_argument("--top-src-csv", default=None,
                    help="Write top source IPs as CSV to this file")

    # Parse arguments from command line
    args = ap.parse_args()
    
    # ==================== ARGUMENT VALIDATION ====================
    # If CSV output is requested but no top-src count specified, default to 5
    if args.top_src_csv and args.top_src == 0:
        args.top_src = 5

    # ==================== STEP 1: COMPUTE COUNTS ====================
    # Load log events from file with specified filters
    # Apply source IP filter and message content filter
    counts = count_by_level(
        iter_events(
            args.path,
            strict=args.strict,
            since=args.since,
            until=args.until
        ),
        src_ip=args.src_ip,
        contains=args.contains
    )

    # Handle case where no events match the filters
    if not counts:
        print("No events matched.")
        return 0

    # ==================== STEP 2: BUILD RESULT OBJECT ====================
    # Create result dictionary with aggregated counts and metadata
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

    # ==================== STEP 3: COMPUTE TOP SOURCE IPs (IF REQUESTED) ====================
    if args.top_src:
        # Query for top N source IPs from the logs
        result["top_src_ips"] = [
            {"src_ip": ip, "count": c}
            for ip, c in top_src_ips(
                iter_events(
                    args.path,
                    strict=args.strict,
                    since=args.since,
                    until=args.until
                ),
                n=args.top_src,
                contains=args.contains,
            )
        ]
        
        # If CSV output requested, write top source IPs to CSV file
        if args.top_src_csv:
            with open(args.top_src_csv, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["src_ip", "count"])
                w.writeheader()
                w.writerows(result.get("top_src_ips", []))

    # ==================== STEP 4: JSON OUTPUT MODE ====================
    # Output results as JSON and exit early (JSON output is mutually exclusive with text)
    if args.json:
        emit(json.dumps(result, indent=2, sort_keys=True), args.out)
        return 0

    # ==================== STEP 5: TEXT OUTPUT MODE ====================
    # Format results as human-readable text output
    lines: list[str] = []
    
    # Calculate column width for alignment based on longest log level name
    width = max(len(k) for k in counts)
    
    # Build text lines with log levels and their counts, sorted alphabetically
    for level in sorted(counts):
        lines.append(f"{level:<{width}}  {counts[level]}")

    # ==================== STEP 6: APPEND TOP SOURCE IPs (IF APPLICABLE) ====================
    if args.top_src:
        lines.append("")
        lines.append("Top source IPs:")
        for row in result["top_src_ips"]:
            lines.append(f'{row["src_ip"]}  {row["count"]}')

    # Combine all text lines into single output string
    text_output = "\n".join(lines)

    # ==================== STEP 7: OUTPUT HANDLING ====================
    # Write to file if --out is specified
    if args.out:
        emit(text_output, args.out)

    # Print to stdout unless --quiet is set or output is going to file
    if (not args.quiet) and (not args.out):
        emit(text_output, None)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
