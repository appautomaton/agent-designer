---
name: plan
description: Draft a repo-local plan using plan/_template.md and optionally save it.
metadata:
  short-description: Repo plan + issues contract
---

# Plan (Repo)

Draft structured plans for this repository and optionally save them to `plan/`.

## Core rules
- Use `plan/_template.md` as the structure and fill every section.
- Do not edit code while planning.
- Draft the plan in chat first; ask for confirmation before writing a plan file.
- Save plans to the repo `plan/` directory, not `~/.codex/plans`.
- Use the naming pattern: `plan/YYYY-MM-DD_HH-mm-ss-<slug>.md`.
- The plan must include a matching Issue CSV path: `issues/YYYY-MM-DD_HH-mm-ss-<slug>.csv`.

## Plan workflow
1) Restate the task and assumptions.
2) Draft the plan body in chat (no frontmatter) using the template.
3) Ask: "Reply CONFIRM to write the plan file."
4) On confirmation, write the plan file with frontmatter and the correct name.

## Issue CSV (only if asked)
- Use `issues/_template.csv` and fill **all** required fields.
- Follow `issues/README.md` for column meanings and CSV formatting.
- Validate with: `python3 scripts/validate_issues_csv.py <issues.csv>`.
- If validation fails, fix and re-run until it passes.

## Clarifications
- Ask up to 2 questions if the task is unclear; otherwise state assumptions and proceed.
