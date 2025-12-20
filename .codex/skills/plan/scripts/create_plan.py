#!/usr/bin/env python3
"""Create a repo-local plan markdown file under ./plan."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from plan_utils import (
    build_plan_filename,
    format_yaml_value,
    get_assets_dir,
    get_plans_dir,
    now_iso,
    now_timestamp,
    replace_placeholders,
    slugify,
    validate_slug,
)

ALLOWED_COMPLEXITY = {"simple", "medium", "complex"}


def read_body(args: argparse.Namespace) -> str | None:
    if args.template:
        template_path = get_assets_dir() / "_template.md"
        return template_path.read_text(encoding="utf-8")
    if args.body_file:
        return Path(args.body_file).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a plan file under ./plan.")
    parser.add_argument("--task", required=True, help="Short task/title for the plan.")
    parser.add_argument(
        "--complexity",
        default="medium",
        choices=sorted(ALLOWED_COMPLEXITY),
        help="Plan complexity: simple|medium|complex.",
    )
    parser.add_argument(
        "--slug",
        help="Optional slug override for the plan filename (lower-case, hyphen-delimited).",
    )
    parser.add_argument(
        "--timestamp",
        help="Override timestamp for the filename (YYYY-MM-DD_HH-mm-ss).",
    )
    parser.add_argument(
        "--created-at",
        dest="created_at",
        help="Override created_at frontmatter (ISO8601).",
    )
    parser.add_argument(
        "--body-file",
        help="Path to markdown body (without frontmatter). If omitted, read from stdin.",
    )
    parser.add_argument(
        "--template",
        action="store_true",
        help="Use the skill's plan template instead of stdin or --body-file.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the plan file if it already exists.",
    )
    args = parser.parse_args()

    task = args.task.strip()
    if not task or "\n" in task:
        raise SystemExit("Task must be a single line.")

    slug = args.slug.strip() if args.slug else slugify(task)
    validate_slug(slug)

    timestamp = args.timestamp.strip() if args.timestamp else now_timestamp()
    filename = build_plan_filename(timestamp, slug)

    created_at = args.created_at.strip() if args.created_at else now_iso()

    body = read_body(args)
    if body is None:
        raise SystemExit("Provide --body-file, stdin, or --template to supply plan content.")

    body = body.strip()
    if not body:
        raise SystemExit("Plan body cannot be empty.")
    if body.lstrip().startswith("---"):
        raise SystemExit("Plan body should not include frontmatter.")

    body = replace_placeholders(body, timestamp, slug)

    plans_dir = get_plans_dir()
    plans_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plans_dir / filename

    if plan_path.exists() and not args.overwrite:
        raise SystemExit(f"Plan already exists: {plan_path}. Use --overwrite to replace.")

    frontmatter = (
        "---\n"
        f"mode: {format_yaml_value('plan')}\n"
        f"task: {format_yaml_value(task)}\n"
        f"created_at: {format_yaml_value(created_at)}\n"
        f"complexity: {format_yaml_value(args.complexity)}\n"
        "---\n\n"
    )

    plan_path.write_text(frontmatter + body + "\n", encoding="utf-8")
    print(str(plan_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
