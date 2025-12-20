#!/usr/bin/env python3
"""Shared helpers for repo-local plan scripts."""

from __future__ import annotations

import re
from pathlib import Path
from datetime import datetime

_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_FILENAME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$"
)
_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$")


def get_repo_root(start: Path | None = None) -> Path:
    """Find the repo root by walking up to .git or AGENTS.md."""
    path = (start or Path.cwd()).resolve()
    for candidate in [path, *path.parents]:
        if (candidate / ".git").exists() or (candidate / "AGENTS.md").exists():
            return candidate
    return path


def get_plans_dir() -> Path:
    return get_repo_root() / "plan"


def get_issues_dir() -> Path:
    return get_repo_root() / "issues"


def get_assets_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "assets"


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug or "plan"


def validate_slug(slug: str) -> None:
    if not slug or not _NAME_RE.match(slug):
        raise ValueError(
            "Invalid slug. Use short, lower-case, hyphen-delimited names "
            "(e.g., update-login-flow)."
        )


def validate_timestamp(timestamp: str) -> None:
    if not _TIMESTAMP_RE.match(timestamp):
        raise ValueError("Timestamp must be in YYYY-MM-DD_HH-mm-ss format.")


def build_plan_filename(timestamp: str, slug: str) -> str:
    validate_timestamp(timestamp)
    validate_slug(slug)
    return f"{timestamp}-{slug}.md"


def format_yaml_value(value: str) -> str:
    if value is None:
        return ""
    needs_quotes = (
        not value
        or value.strip() != value
        or "\n" in value
        or any(ch in value for ch in (":", "#", "{", "}", "[", "]", ","))
    )
    if needs_quotes:
        escaped = value.replace('"', "\\\"")
        return f'"{escaped}"'
    return value


def replace_placeholders(body: str, timestamp: str, slug: str) -> str:
    body = body.replace("issues/<YYYY-MM-DD_HH-mm-ss>-<slug>.csv", f"issues/{timestamp}-{slug}.csv")
    body = body.replace("<YYYY-MM-DD_HH-mm-ss>", timestamp)
    body = body.replace("<slug>", slug)
    return body


def validate_plan_filename(filename: str) -> None:
    if not _FILENAME_RE.match(filename):
        raise ValueError(
            "Invalid plan filename. Expected YYYY-MM-DD_HH-mm-ss-<slug>.md."
        )


def parse_frontmatter(path: Path) -> dict:
    """Parse YAML frontmatter from a markdown file without reading the body."""
    with path.open("r", encoding="utf-8") as handle:
        first = handle.readline()
        if first.strip() != "---":
            raise ValueError("Frontmatter must start with '---'.")

        data: dict[str, str] = {}
        for line in handle:
            stripped = line.strip()
            if stripped == "---":
                return data
            if not stripped or stripped.startswith("#"):
                continue
            if ":" not in line:
                raise ValueError(f"Invalid frontmatter line: {line.rstrip()}")
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value and len(value) >= 2 and value[0] == value[-1] and value[0] in ("\"", "'"):
                value = value[1:-1]
            data[key] = value

    raise ValueError("Frontmatter must end with '---'.")


def now_timestamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")
