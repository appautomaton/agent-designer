<!-- Issue-Driven Development — append to your project's AGENTS.md -->
<!-- Usage: ask your agent to "apply AGENTS.issues.template.md on top of AGENTS.md" -->

## E2E loop
E2E loop = plan → issues → implement → test → review → commit → regression.

## Plan & issue generation
- Use the `issue-driven-workflow` skill for plan and Issue CSV generation.
- Plans must include: steps, tests, risks, and rollback/safety notes.

## Issue CSV guidelines
- Every row must include: ID, Title, Description, Acceptance, Test_Method, Tools, Dev_Status, Review1_Status, Regression_Status, Files, Dependencies, Notes.
- Status values: TODO | DOING | DONE (never percentages).
- If a task lacks a test method, add one or flag it as a risk.
- One plan maps to one Issue CSV unless explicitly split.
- See the `issue-driven-workflow` skill references for column definitions and testing policy.

## Tool usage
- When a matching MCP tool exists, use it; do not guess or simulate results.
- Prefer the tool specified in the Issue CSV `Tools` column.
- If a tool is unavailable or fails, note it and proceed with the safest alternative.
- Use available MCP tools in `server:tool` format, or `manual`/`none`.
