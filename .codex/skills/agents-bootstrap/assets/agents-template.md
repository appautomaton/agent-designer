# AGENTS

> Purpose: <one-line purpose for this project>

## Role & objective
- Role: <role>
- Objective: <objective>

## Constraints (non-negotiable)
- <constraint>

## Tech & data
- <frameworks/tools>
- <data sources>

## E2E loop
E2E loop = plan → issues → implement → test → review → commit → regression.
 
## Plan & issue generation
- Use the `plan` skill for plan and Issue CSV generation.
- Plans must include: steps, tests, risks, and rollback/safety notes.

## Issue CSV guidelines
- Required columns: ID, Title, Description, Acceptance, Test_Method, Tools, Dev_Status, Review1_Status, Regression_Status, Files, Dependencies, Notes.
- Status values: TODO | DOING | DONE.
- Follow `issues/README.md`.

## Tool usage
- When a matching MCP tool exists, use it; do not guess or simulate results.
- Prefer the tool specified in the Issue CSV `Tools` column.
- If a tool is unavailable or fails, note it and proceed with the safest alternative.

## Testing policy
- Follow `docs/testing-policy.md` for verification requirements and defaults.

## Safety
- Avoid destructive commands unless explicitly requested.
- Preserve backward compatibility unless asked to break it.
- Never expose secrets; redact if encountered.

## Output style
- Keep responses concise and structured.
- Provide file references with line numbers when editing.
- Always include risks and suggested next steps for non-trivial changes.
