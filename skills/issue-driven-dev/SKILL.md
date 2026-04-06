---
name: issue-driven-dev
description: Plan tasks and generate Issue CSVs for structured, autonomous execution. Use when creating plans, generating issue trackers, or executing issue-driven workflows.
metadata:
  short-description: Plan + Issue CSV workflow
---

# Issue-Driven Development

Structure work into a thorough plan and a granular Issue CSV, then execute end-to-end with minimal user interruption.

This workflow applies to any goal-oriented task — software development, research, content creation, infrastructure, or autonomous agent actions.

## Philosophy

**Two phases, two modes:**

1. **Planning (interactive)** — invest upfront in understanding. Search the web, read docs, ask clarification questions, gather enough context to make the plan followable and the CSV doable. This is where you front-load the thinking.

2. **Execution (autonomous)** — once the CSV is approved, work through it end-to-end. Update statuses as you go. Use best judgment to resolve ambiguity. Minimize back-and-forth with the user. Only stop for genuinely blocking unknowns.

The goal: a plan thorough enough that the CSV rows are independently actionable, and a CSV granular enough that each row can be completed, tested, and marked DONE without further clarification.

## E2E loop

plan → issues → implement → test → review → commit → regression

## Plan workflow (interactive phase)

1. Restate the task and assumptions.
2. **Gather context** — search the web, read project files, inspect dependencies. Do enough research to make every plan section concrete, not aspirational.
3. Ask up to 2 clarification questions if the task is unclear, then proceed with stated assumptions.
4. Draft the plan body in chat using `assets/_template.md`. Choose complexity (`simple|medium|complex`) — this determines which template sections to fill.
5. Ask: "Reply CONFIRM to write the plan file."
6. On confirmation, write via script:
   ```bash
   python3 .codex/skills/issue-driven-dev/scripts/create_plan.py \
     --task "<short title>" --complexity <simple|medium|complex>
   ```
   Provide body via stdin, `--body-file`, or `--template` for a starter.
7. Do not edit code while planning.

## Issue CSV workflow (interactive → autonomous transition)

**Creating the CSV (still interactive):**

1. Generate the Issue CSV after the plan is reviewed/approved.
2. Break the plan into granular, independently actionable rows. Each row should be completable without needing to ask the user.
3. Use `assets/_template.csv` as the format. Fill **all** required columns — see `references/issue-csv-spec.md`.
4. Order rows by dependency chain. Set the `Dependencies` column so execution order is unambiguous.
5. Populate `Tools` with available MCP tools (`server:tool` format) or use `manual`/`none`.
6. Validate:
   ```bash
   python3 .codex/skills/issue-driven-dev/scripts/validate_issues_csv.py <issues.csv>
   ```
7. Fix and re-validate until it passes.

**Executing the CSV (autonomous):**

1. Work through rows in dependency order. Set `Dev_Status = DOING` when starting a row.
2. Use best judgment to complete each row. Search for information, read files, write code, run tests — do whatever the row requires.
3. When the row's `Acceptance` criteria are met and `Test_Method` passes, set `Dev_Status = DONE`.
4. Run `Review1_Status` verification. Mark `DONE` when it passes.
5. After all rows are `DONE`, run the regression pass. Mark `Regression_Status = DONE` per row.
6. **Only stop to ask the user** when you encounter a genuinely blocking unknown that changes correctness, safety, or an irreversible action. Do not stop for routine decisions.

## Scripts

| Script | Purpose |
|---|---|
| `create_plan.py` | Create a plan file with YAML frontmatter under `plan/` |
| `list_plans.py` | List existing plans by frontmatter (supports `--query`, `--json`) |
| `read_plan_frontmatter.py` | Read a single plan's metadata |
| `validate_issues_csv.py` | Validate Issue CSV schema, required fields, and status values |
| `plan_utils.py` | Shared utilities (slug, timestamp, path helpers) |

Run any script with `--help` first. Scripts live in `scripts/` relative to this skill.

## Naming conventions

- Plans: `plan/YYYY-MM-DD_HH-mm-ss-<slug>.md`
- Issue CSVs: `issues/YYYY-MM-DD_HH-mm-ss-<slug>.csv`
- Plan and Issue CSV share the same timestamp/slug.

## References

- [Issue CSV spec](references/issue-csv-spec.md) — column definitions, status values, sentinel values, test method guidance. **Read when creating or validating Issue CSVs.**
- [Testing policy](references/testing-policy.md) — test layers, minimum expectations by change type, regression policy. **Read when filling `Test_Method` column.**
- [Plan template](assets/_template.md) — plan structure with complexity tiers and examples.
- [Issue CSV template](assets/_template.csv) — example rows showing plan-to-CSV mapping.
