#!/usr/bin/env python3
"""Row-addressable Issue CSV updates. Never string-edit the CSV directly.

Mutation:  update_issue.py issues.csv --id A2 --dev-status DOING
Query:     update_issue.py issues.csv --next
           update_issue.py issues.csv --show A2
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from issue_utils import (
    ALLOWED_STATUS,
    REQUIRED_COLUMNS,
    format_row,
    next_actionable,
    read_issues,
    row_dict,
    validate_issues,
    write_issues,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update or query one row of an Issue CSV by ID."
    )
    parser.add_argument("csv_path", help="Path to the issues CSV file.")
    parser.add_argument("--id", help="Row ID to update, for example A2.")
    parser.add_argument("--dev-status", choices=ALLOWED_STATUS)
    parser.add_argument("--review-status", choices=ALLOWED_STATUS)
    parser.add_argument("--regression-status", choices=ALLOWED_STATUS)
    parser.add_argument(
        "--note",
        help="Append text to the Notes field, replacing a 'none' sentinel.",
    )
    parser.add_argument(
        "--next",
        action="store_true",
        help="Print the first row with Dev_Status TODO whose dependencies are all DONE.",
    )
    parser.add_argument("--show", metavar="ID", help="Print one row by ID.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args()

    changes = {
        "Dev_Status": args.dev_status,
        "Review_Status": args.review_status,
        "Regression_Status": args.regression_status,
    }
    has_changes = any(value for value in changes.values()) or args.note
    modes = sum([bool(args.next), bool(args.show), bool(args.id)])
    if modes != 1:
        parser.error("use exactly one of --id, --next, or --show")
    if args.id and not has_changes:
        parser.error("--id needs at least one of --dev-status, --review-status, "
                     "--regression-status, or --note")
    if has_changes and not args.id:
        parser.error("status and note flags require --id")

    path = Path(args.csv_path)
    if not path.is_file():
        print(f"error: not a file: {path}", file=sys.stderr)
        return 1

    header, rows, start_lines = read_issues(path)
    errors, _ = validate_issues(header, rows, start_lines)
    if errors:
        for message in errors:
            print(f"error: {message}", file=sys.stderr)
        print("error: fix the CSV before querying or updating it", file=sys.stderr)
        return 1

    if args.next:
        data = next_actionable(rows)
        if args.json:
            print(json.dumps({"next": data}))
        elif data is None:
            print("no actionable rows")
        else:
            print(format_row(data))
        return 0

    if args.show:
        for row in rows:
            data = row_dict(row)
            if data["ID"].strip() == args.show:
                print(json.dumps(data) if args.json else format_row(data))
                return 0
        print(f"error: no row with ID '{args.show}'", file=sys.stderr)
        return 1

    updated = None
    new_rows = []
    for row in rows:
        data = row_dict(row)
        if data["ID"].strip() == args.id:
            for col, value in changes.items():
                if value:
                    data[col] = value
            if args.note:
                existing = data["Notes"].strip()
                if not existing or existing.lower() == "none":
                    data["Notes"] = args.note
                else:
                    data["Notes"] = existing + " | " + args.note
            updated = data
        new_rows.append(data)

    if updated is None:
        print(f"error: no row with ID '{args.id}'", file=sys.stderr)
        return 1

    check_rows = [[data[col] for col in REQUIRED_COLUMNS] for data in new_rows]
    errors, warnings = validate_issues(
        list(REQUIRED_COLUMNS), check_rows, list(range(2, 2 + len(check_rows)))
    )
    if errors:
        for message in errors:
            print(f"error: {message}", file=sys.stderr)
        print("error: update rejected, nothing written", file=sys.stderr)
        return 1
    for message in warnings:
        print(f"warning: {message}", file=sys.stderr)

    write_issues(path, new_rows)
    print(json.dumps(updated) if args.json else format_row(updated))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
