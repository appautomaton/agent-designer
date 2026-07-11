---
name: issue-driven-workflow
description: Turn a large task into a persistent plan file and a trackable Issue CSV, then execute the issues autonomously with per-row status updates. Use when work must survive across sessions or hand off between agents, or when you need an auditable record of multi-step execution. Do not use for single-session tasks that your harness's built-in plan or todo tracking already covers.
metadata:
  short-description: Plan file → Issue CSV → tracked autonomous execution
---

# Issue-Driven Workflow

## Philosophy

The plan and Issue CSV are a work amplifier. Front-load the thinking so the agent has a full plate of actionable work to execute autonomously. More rows means more useful work per run.

1. **Planning (interactive)**: search the web, read docs, ask questions, gather context. A thorough plan means more work the agent can do without stopping.
2. **Execution (autonomous)**: be proactive, not passive. Work through the CSV end to end and do not wait for permission on routine decisions.

The quality bar: every CSV row is completable, testable, and markable DONE without further clarification.

## E2E loop

plan → issues → implement → test → review

## Paths

Commands below write `<skill_dir>` for the absolute path of the directory containing this SKILL.md. Your harness reports that path when it loads the skill. Substitute it before running. Artifacts land in the target project at its root: plans in `plans/`, issue CSVs in `issues/`.

## Planning (interactive)

1. Restate the task and assumptions.
2. Gather context: search the web, read project files, inspect dependencies. Make every plan section concrete, not aspirational.
3. Ask up to 2 clarification questions if unclear, then proceed with stated assumptions.
4. Draft the plan body using the structure of `assets/_template.md` and choose a complexity tier.
5. Get the plan approved before writing it. Use the host's plan approval mechanism when one exists. In an interactive session without one, ask once in conversation. In a headless or autonomous run, proceed and record the assumptions in the plan's Assumptions section.
6. Save the drafted body to a temp file, then write the plan:
   ```bash
   python3 <skill_dir>/scripts/create_plan.py \
     --task "<title>" --complexity <simple|medium|complex> --body-file <tmpfile>
   ```
   A single-quoted heredoc piped to stdin also works. Use `--template` only to start from the blank scaffold. The script prints the plan path. Keep it for the next step.
7. Do not edit code while planning.

## Creating the CSV (interactive)

1. Generate after the plan is approved.
2. Break the plan into granular, independently actionable rows. Fill all required columns per `references/issue-csv-spec.md`, order rows by dependency chain, and set `Dependencies` so execution order is unambiguous.
3. Draft the rows, canonical header included, to a temp file, then:
   ```bash
   python3 <skill_dir>/scripts/create_issues.py --plan <plan-path> --rows-file <tmpfile>
   ```
   The script derives `issues/<timestamp>-<slug>.csv` from the plan filename, validates every row, and writes nothing on any error.

## Executing the CSV (autonomous)

The CSV is your execution state. Read it and update it through the scripts, and keep driving forward. Never string-edit the CSV: quoting rules and repeated status cells make hand edits corruption-prone.

1. Pick work: `python3 <skill_dir>/scripts/update_issue.py <csv> --next`
2. Mark it started: `python3 <skill_dir>/scripts/update_issue.py <csv> --id A2 --dev-status DOING`
3. Complete the row. Search, read, write, test, whatever it requires.
4. When `Acceptance` is met and `Test_Method` passes, set `--id A2 --dev-status DONE`.
5. Self-review, then set `--id A2 --review-status DONE`. The script rejects incoherent transitions, for example review marked DONE before implementation.
6. Immediately pick the next row with `--next` and keep going.
7. After all rows are DONE, run the regression pass and set `--regression-status DONE` per row.
8. Report progress briefly as you complete rows.
9. Only stop for genuinely blocking unknowns that affect correctness, safety, or irreversible actions.

If a row is too large, split it. If a row fails, fix it or flag it with `--note`. If in a git repo, commit at natural boundaries.

## Scripts

| Script | Purpose | Key flags |
|---|---|---|
| `create_plan.py` | Write a plan file with frontmatter under `plans/` | `--task`, `--complexity`, `--body-file`, `--template`, `--overwrite` |
| `create_issues.py` | Write the paired Issue CSV, fully validated | `--plan`, `--rows-file`, `--overwrite` |
| `update_issue.py` | Row-addressable status and note updates, plus queries | `--id`, `--dev-status`, `--review-status`, `--regression-status`, `--note`, `--next`, `--show`, `--json` |
| `validate_issues_csv.py` | Validate schema and semantics, all errors in one run | `<csv>` |
| `list_plans.py` | List existing plans | `--query`, `--json` |
| `read_plan_frontmatter.py` | Read one plan's frontmatter | `--json` |

Every script prints usage with `--help`.

## Naming and persistence

Plans: `plans/YYYY-MM-DD_HH-mm-ss-<slug>.md`. Issue CSVs: `issues/YYYY-MM-DD_HH-mm-ss-<slug>.csv` with the same timestamp and slug, enforced by `create_issues.py`. Commit `plans/` and `issues/` in the consuming repo when tracking should survive sessions or hand off between agents. Gitignore them for scratch work.

## References

- [Issue CSV spec](references/issue-csv-spec.md): read when creating or validating CSVs
- [Testing policy](references/testing-policy.md): read when filling `Test_Method`
- [Plan template](assets/_template.md): structure with complexity tiers
- [CSV template](assets/_template.csv): example rows, coherent stack, varied statuses
