#!/usr/bin/env python3
"""Read plan frontmatter without loading the full markdown body."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from plan_utils import parse_frontmatter

REQUIRED_KEYS = {"task", "created_at", "complexity", "mode"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Read frontmatter from a plan markdown file.")
    parser.add_argument("plan_path", help="Path to the plan markdown file.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args()

    path = Path(args.plan_path).expanduser()
    if not path.exists():
        raise SystemExit(f"Plan not found: {path}")

    data = parse_frontmatter(path)
    if not REQUIRED_KEYS.issubset(data.keys()):
        missing = sorted(REQUIRED_KEYS - set(data.keys()))
        raise SystemExit(f"Frontmatter missing required fields: {', '.join(missing)}")

    payload = {
        "mode": data.get("mode"),
        "task": data.get("task"),
        "created_at": data.get("created_at"),
        "complexity": data.get("complexity"),
        "path": str(path),
    }

    if args.json:
        print(json.dumps(payload))
    else:
        for key in ("mode", "task", "created_at", "complexity", "path"):
            print(f"{key}: {payload[key]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
