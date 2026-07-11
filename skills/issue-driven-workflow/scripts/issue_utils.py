#!/usr/bin/env python3
"""Shared helpers for Issue CSV scripts: read, validate, write, and query."""

from __future__ import annotations

import csv
import io
import os
import re
import tempfile
from pathlib import Path

REQUIRED_COLUMNS = [
    "ID",
    "Title",
    "Description",
    "Acceptance",
    "Test_Method",
    "Tools",
    "Dev_Status",
    "Review_Status",
    "Regression_Status",
    "Files",
    "Dependencies",
    "Notes",
]

STATUS_FIELDS = ("Dev_Status", "Review_Status", "Regression_Status")
ALLOWED_STATUS = ("TODO", "DOING", "DONE")
TOOL_SENTINELS = ("manual", "none")

_ID_RE = re.compile(r"^[A-Z]+[0-9]+$")
_TOOL_RE = re.compile(r"^[\w.-]+:[\w.-]+$")


def read_issues(source):
    """Read an Issue CSV from a path or file object.

    Returns (header, rows, start_lines) where start_lines maps each data row
    to the physical line it starts on, so errors stay accurate when quoted
    fields span multiple lines. Opens files as utf-8-sig to tolerate a BOM.
    """
    if hasattr(source, "read"):
        return _read_issues_handle(source)
    with open(source, newline="", encoding="utf-8-sig") as handle:
        return _read_issues_handle(handle)


def read_issues_text(text):
    """Read an Issue CSV from a string (used for stdin and --rows-file)."""
    return _read_issues_handle(io.StringIO(text.lstrip("﻿")))


def _read_issues_handle(handle):
    reader = csv.reader(handle)
    header = None
    rows = []
    start_lines = []
    prev_line = 0
    for row in reader:
        start = prev_line + 1
        prev_line = reader.line_num
        if not any(cell.strip() for cell in row):
            continue
        if header is None:
            header = row
            continue
        rows.append(row)
        start_lines.append(start)
    return header, rows, start_lines


def parse_dependencies(value):
    """Return the list of dependency tokens, empty for the 'none' sentinel."""
    value = value.strip()
    if not value or value.lower() == "none":
        return []
    return [token.strip() for token in value.split("|") if token.strip()]


def row_dict(row):
    return dict(zip(REQUIRED_COLUMNS, row))


def validate_issues(header, rows, start_lines):
    """Validate schema and semantics. Returns (errors, warnings), all collected."""
    errors = []
    warnings = []

    if header is None:
        errors.append("line 1: file is empty")
        return errors, warnings

    if header != REQUIRED_COLUMNS:
        parts = []
        missing = [c for c in REQUIRED_COLUMNS if c not in header]
        unexpected = [c for c in header if c not in REQUIRED_COLUMNS]
        if missing:
            parts.append("missing columns: " + ", ".join(missing))
        if unexpected:
            parts.append("unexpected columns: " + ", ".join(unexpected))
        if not parts:
            parts.append("columns are out of order")
        for position, (got, want) in enumerate(zip(header, REQUIRED_COLUMNS), start=1):
            if got != want:
                parts.append(
                    f"first mismatch at column {position}: expected {want!r}, got {got!r}"
                )
                break
        errors.append("line 1: invalid header (" + " | ".join(parts) + ")")
        return errors, warnings

    if not rows:
        errors.append("line 1: no data rows (header only)")

    ids = {}
    for row, start in zip(rows, start_lines):
        loc = f"line {start}"
        if len(row) != len(REQUIRED_COLUMNS):
            errors.append(
                f"{loc}: expected {len(REQUIRED_COLUMNS)} columns, got {len(row)}"
            )
            continue
        data = row_dict(row)

        for col, value in data.items():
            if not value.strip():
                errors.append(f"{loc}: '{col}' is empty")

        issue_id = data["ID"].strip()
        if issue_id:
            if not _ID_RE.match(issue_id):
                errors.append(
                    f"{loc}: ID '{issue_id}' must be uppercase letters then digits, like A1"
                )
            if issue_id in ids:
                errors.append(
                    f"{loc}: duplicate ID '{issue_id}' (first used at line {ids[issue_id]})"
                )
            else:
                ids[issue_id] = start

        for col in STATUS_FIELDS:
            value = data[col].strip()
            if value and value not in ALLOWED_STATUS:
                errors.append(
                    f"{loc}: '{col}' must be one of {'/'.join(ALLOWED_STATUS)}, got '{value}'"
                )

        dev = data["Dev_Status"].strip()
        review = data["Review_Status"].strip()
        regression = data["Regression_Status"].strip()
        if review in ("DOING", "DONE") and dev != "DONE":
            errors.append(
                f"{loc}: Review_Status is {review} but Dev_Status is {dev} "
                "(implement before reviewing)"
            )
        if regression in ("DOING", "DONE") and (dev != "DONE" or review != "DONE"):
            errors.append(
                f"{loc}: Regression_Status is {regression} before Dev_Status "
                "and Review_Status are DONE"
            )

        tools = data["Tools"].strip()
        if tools and tools not in TOOL_SENTINELS:
            for token in (t.strip() for t in tools.split("|")):
                if token and not _TOOL_RE.match(token):
                    errors.append(
                        f"{loc}: Tools entry '{token}' is not 'server:tool', "
                        "'manual', or 'none'"
                    )
        if data["Test_Method"].strip().lower().startswith("manual") and tools not in TOOL_SENTINELS:
            warnings.append(
                f"{loc}: Test_Method is manual but Tools names an automation "
                f"tool ('{tools}')"
            )

    graph = {}
    for row, start in zip(rows, start_lines):
        if len(row) != len(REQUIRED_COLUMNS):
            continue
        data = row_dict(row)
        loc = f"line {start}"
        issue_id = data["ID"].strip()
        deps = parse_dependencies(data["Dependencies"])
        known_deps = []
        for dep in deps:
            if not _ID_RE.match(dep):
                errors.append(
                    f"{loc}: Dependencies entry '{dep}' is not a row ID "
                    "(record external dependencies in Notes)"
                )
                continue
            if dep not in ids:
                errors.append(f"{loc}: Dependencies references unknown ID '{dep}'")
                continue
            if dep == issue_id:
                errors.append(f"{loc}: row '{issue_id}' depends on itself")
                continue
            known_deps.append(dep)
        if issue_id:
            graph[issue_id] = known_deps

    cycle = _find_cycle(graph)
    if cycle:
        errors.append("dependency cycle: " + " -> ".join(cycle))

    return errors, warnings


def _find_cycle(graph):
    """Return one dependency cycle as a path list, or None."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}
    stack = []

    def visit(node):
        color[node] = GRAY
        stack.append(node)
        for dep in graph.get(node, []):
            if color.get(dep, WHITE) == GRAY:
                start = stack.index(dep)
                return stack[start:] + [dep]
            if color.get(dep, WHITE) == WHITE:
                found = visit(dep)
                if found:
                    return found
        stack.pop()
        color[node] = BLACK
        return None

    for node in graph:
        if color[node] == WHITE:
            found = visit(node)
            if found:
                return found
    return None


def write_issues(path, rows):
    """Write rows atomically with canonical quoting. Rows are lists or dicts."""
    path = Path(path)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=".issues-", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(REQUIRED_COLUMNS)
            for row in rows:
                if isinstance(row, dict):
                    writer.writerow([row[col] for col in REQUIRED_COLUMNS])
                else:
                    writer.writerow(row)
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def next_actionable(rows):
    """Return the first row dict whose Dev_Status is TODO and whose
    dependencies are all Dev_Status DONE, or None."""
    dev_by_id = {}
    for row in rows:
        data = row_dict(row)
        dev_by_id[data["ID"].strip()] = data["Dev_Status"].strip()
    for row in rows:
        data = row_dict(row)
        if data["Dev_Status"].strip() != "TODO":
            continue
        deps = parse_dependencies(data["Dependencies"])
        if all(dev_by_id.get(dep) == "DONE" for dep in deps):
            return data
    return None


def format_row(data):
    """One-line human-readable rendering of a row dict."""
    return (
        f"{data['ID']}: {data['Title']} "
        f"[Dev={data['Dev_Status']} Review={data['Review_Status']} "
        f"Regression={data['Regression_Status']}] deps={data['Dependencies']}"
    )
