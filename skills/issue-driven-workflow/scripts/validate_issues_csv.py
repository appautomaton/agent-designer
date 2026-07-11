#!/usr/bin/env python3
"""Validate an Issue CSV: schema, statuses, dependencies, and coherence.

Reports every problem in one run, with physical line numbers that stay
accurate when quoted fields span multiple lines.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from issue_utils import read_issues, validate_issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate an Issue CSV against the column spec and semantic rules."
    )
    parser.add_argument("csv_path", help="Path to the issues CSV file.")
    args = parser.parse_args()

    path = Path(args.csv_path)
    if not path.is_file():
        print(f"error: not a file: {path}", file=sys.stderr)
        return 1

    header, rows, start_lines = read_issues(path)
    errors, warnings = validate_issues(header, rows, start_lines)

    for message in errors:
        print(f"error: {message}", file=sys.stderr)
    for message in warnings:
        print(f"warning: {message}", file=sys.stderr)
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)

    if errors:
        return 1
    print(f"ok: {path} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
