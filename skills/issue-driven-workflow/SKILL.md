---
name: issue-driven-workflow
description: Break down complex tasks into a structured plan and trackable Issue CSV, then execute autonomously. Use when a task has multiple steps, needs research before starting, requires status tracking, or benefits from a structured breakdown before execution.
metadata:
  short-description: Plan → Issue CSV → autonomous execution
---

# Issue-Driven Workflow

## Philosophy

The plan and Issue CSV are a **work amplifier**. Front-load the thinking so the agent has a full plate of actionable work to execute autonomously — more rows means more useful work per run.

1. **Planning (interactive)** — search the web, read docs, ask questions, gather context. A thorough plan means more work the agent can do without stopping.
2. **Execution (autonomous)** — be proactive, not passive. Work through the CSV end-to-end. Maximize useful work per run — don't wait for permission on routine decisions.

The quality bar: every CSV row should be completable, testable, and markable DONE without further clarification.

## E2E loop

plan → issues → implement → test → review

## Planning (interactive)

1. Restate the task and assumptions.
2. **Gather context** — search the web, read project files, inspect dependencies. Make every plan section concrete, not aspirational.
3. Ask up to 2 clarification questions if unclear, then proceed with stated assumptions.
4. Draft the plan in chat using `assets/_template.md`. Choose complexity (`simple|medium|complex`).
5. Ask: "Reply CONFIRM to write the plan file."
6. On confirmation:
   ```bash
   python3 .codex/skills/issue-driven-workflow/scripts/create_plan.py \
     --task "<title>" --complexity <simple|medium|complex>
   ```
7. Do not edit code while planning.

## Creating the CSV (interactive)

1. Generate after the plan is approved.
2. Break the plan into granular, independently actionable rows.
3. Fill **all** required columns — see `references/issue-csv-spec.md`.
4. Order by dependency chain. Set `Dependencies` so execution order is unambiguous.
5. Validate:
   ```bash
   python3 .codex/skills/issue-driven-workflow/scripts/validate_issues_csv.py <issues.csv>
   ```

## Executing the CSV (autonomous)

The CSV is your execution state. Read it to know where you are, update it as you work, keep driving forward.

1. Read the CSV. Find the next `TODO` row in dependency order.
2. Set `Dev_Status = DOING`. Start working.
3. Complete the row — search, read, write, test, whatever it requires.
4. When `Acceptance` is met and `Test_Method` passes, set `Dev_Status = DONE`.
5. Self-review. Mark `Review1_Status = DONE`.
6. **Immediately move to the next row.** Read the CSV again, pick the next `TODO`, keep going.
7. After all rows are `DONE`, regression check. Mark `Regression_Status = DONE` per row.
8. Report progress briefly as you complete rows.
9. Only stop for genuinely blocking unknowns that affect correctness, safety, or irreversible actions.

If a row is too large, split it. If a row fails, fix it or flag it. If in a git repo, commit at natural boundaries. Edit the CSV directly — re-validate after edits.

## Scripts

| Script | Purpose |
|---|---|
| `create_plan.py` | Create a plan file with YAML frontmatter under `plan/` |
| `list_plans.py` | List existing plans (supports `--query`, `--json`) |
| `validate_issues_csv.py` | Validate Issue CSV schema and status values |

Run with `--help` first. Scripts live in `scripts/` relative to this skill.

## Naming

Plans: `plan/YYYY-MM-DD_HH-mm-ss-<slug>.md` — Issue CSVs: `issues/YYYY-MM-DD_HH-mm-ss-<slug>.csv` — same timestamp/slug.

## References

- [Issue CSV spec](references/issue-csv-spec.md) — **read when creating or validating CSVs**
- [Testing policy](references/testing-policy.md) — **read when filling `Test_Method`**
- [Plan template](assets/_template.md) — structure with complexity tiers
- [CSV template](assets/_template.csv) — example rows with plan-to-CSV mapping
