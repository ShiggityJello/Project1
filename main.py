from __future__ import annotations

import argparse
from logkit.parser import iter_events, count_by_level


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
    args = ap.parse_args()

    counts = count_by_level(iter_events(args.path, strict=args.strict),
                            src_ip=args.src_ip, contains=args.contains)

    if not counts:
        print("No events matched.")
        return 0

    width = max(len(k) for k in counts)
    for level in sorted(counts):
        print(f"{level:<{width}}  {counts[level]}")

    if args.top_src:
        from logkit.parser import top_src_ips
        print("\nTop source IPs:")
        for ip, c in top_src_ips(iter_events(args.path), n=args.top_src, contains=args.contains):
            print(f"{ip}  {c}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
