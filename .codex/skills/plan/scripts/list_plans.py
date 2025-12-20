#!/usr/bin/env python3
"""List repo-local plan summaries by reading frontmatter only."""

from __future__ import annotations

import argparse
import json

from plan_utils import get_plans_dir, parse_frontmatter


REQUIRED_KEYS = {"task", "created_at", "complexity"}


def main() -> int:
    parser = argparse.ArgumentParser(description="List plan summaries from ./plan.")
    parser.add_argument("--query", help="Case-insensitive substring to filter task/path.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args()

    plans_dir = get_plans_dir()
    if not plans_dir.exists():
        raise SystemExit(f"Plans directory not found: {plans_dir}")

    query = args.query.lower() if args.query else None
    items = []
    for path in sorted(plans_dir.glob("*.md")):
        try:
            data = parse_frontmatter(path)
        except ValueError:
            continue
        if not REQUIRED_KEYS.issubset(data.keys()):
            continue
        task = data.get("task", "")
        created_at = data.get("created_at", "")
        complexity = data.get("complexity", "")
        if query:
            haystack = f"{task} {path}".lower()
            if query not in haystack:
                continue
        items.append(
            {
                "task": task,
                "created_at": created_at,
                "complexity": complexity,
                "path": str(path),
            }
        )

    if args.json:
        print(json.dumps(items))
    else:
        for item in items:
            print(
                f"{item['task']}\t{item['created_at']}\t{item['complexity']}\t{item['path']}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
