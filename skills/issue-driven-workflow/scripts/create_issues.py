#!/usr/bin/env python3
"""Create the Issue CSV paired with a plan file.

Derives issues/<timestamp>-<slug>.csv from the plan filename so the naming
contract holds automatically. Row content comes from --rows-file or stdin,
must start with the canonical header, and is fully validated before anything
is written.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from issue_utils import (
    REQUIRED_COLUMNS,
    read_issues_text,
    validate_issues,
    write_issues,
)
from plan_utils import validate_plan_filename


def read_rows_text(args: argparse.Namespace) -> str | None:
    if args.rows_file:
        return Path(args.rows_file).read_text(encoding="utf-8-sig")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create the Issue CSV paired with an existing plan file."
    )
    parser.add_argument(
        "--plan",
        required=True,
        help="Path to the plan markdown file the CSV pairs with.",
    )
    parser.add_argument(
        "--rows-file",
        help="CSV content including the canonical header. If omitted, read stdin.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the issues CSV if it already exists.",
    )
    args = parser.parse_args()

    plan_path = Path(args.plan).expanduser()
    if not plan_path.exists():
        print(f"error: plan not found: {plan_path}", file=sys.stderr)
        return 1
    try:
        validate_plan_filename(plan_path.name)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    text = read_rows_text(args)
    if text is None or not text.strip():
        print(
            "error: provide CSV rows via --rows-file or stdin, starting with "
            "the canonical header.",
            file=sys.stderr,
        )
        return 1

    header, rows, start_lines = read_issues_text(text)
    if header != REQUIRED_COLUMNS:
        print(
            "error: first row must be the canonical header:\n"
            + ",".join(REQUIRED_COLUMNS),
            file=sys.stderr,
        )
        return 1

    errors, warnings = validate_issues(header, rows, start_lines)
    for message in errors:
        print(f"error: {message}", file=sys.stderr)
    for message in warnings:
        print(f"warning: {message}", file=sys.stderr)
    if errors:
        print(f"{len(errors)} error(s), nothing written", file=sys.stderr)
        return 1

    issues_dir = plan_path.resolve().parent.parent / "issues"
    issues_dir.mkdir(parents=True, exist_ok=True)
    csv_path = issues_dir / (plan_path.name[: -len(".md")] + ".csv")

    if csv_path.exists() and not args.overwrite:
        print(
            f"error: issues CSV already exists: {csv_path}. "
            "Use --overwrite to replace.",
            file=sys.stderr,
        )
        return 1

    write_issues(csv_path, rows)
    print(str(csv_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
