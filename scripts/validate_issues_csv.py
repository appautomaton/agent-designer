#!/usr/bin/env python3
"""Validate issues CSV schema and required fields."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "ID",
    "Title",
    "Description",
    "Acceptance",
    "Test_Method",
    "Tools",
    "Dev_Status",
    "Review1_Status",
    "Regression_Status",
    "Files",
    "Dependencies",
    "Notes",
]

STATUS_FIELDS = {"Dev_Status", "Review1_Status", "Regression_Status"}
ALLOWED_STATUS = {"TODO", "DOING", "DONE"}


def fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def main() -> int:
    if len(sys.argv) != 2:
        return fail("usage: validate_issues_csv.py <issues.csv>")

    path = Path(sys.argv[1])
    if not path.exists():
        return fail(f"file not found: {path}")

    rows = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if any(cell.strip() for cell in row):
                rows.append(row)

    if not rows:
        return fail("csv is empty")

    header = rows[0]
    if header != REQUIRED_COLUMNS:
        return fail(
            "invalid header. expected: "
            + ",".join(REQUIRED_COLUMNS)
            + " | got: "
            + ",".join(header)
        )

    seen_ids: set[str] = set()
    for idx, row in enumerate(rows[1:], start=2):
        if len(row) != len(REQUIRED_COLUMNS):
            return fail(f"row {idx}: expected {len(REQUIRED_COLUMNS)} columns, got {len(row)}")

        row_data = dict(zip(REQUIRED_COLUMNS, row))
        for col, value in row_data.items():
            if not value.strip():
                return fail(f"row {idx}: '{col}' is empty")
            if col in STATUS_FIELDS and value.strip() not in ALLOWED_STATUS:
                return fail(
                    f"row {idx}: '{col}' must be one of {sorted(ALLOWED_STATUS)}, got '{value}'"
                )

        issue_id = row_data["ID"].strip()
        if issue_id in seen_ids:
            return fail(f"row {idx}: duplicate ID '{issue_id}'")
        seen_ids.add(issue_id)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
