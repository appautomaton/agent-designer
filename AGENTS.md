# AGENTS

> Purpose: consistent, reliable Codex execution for complex tasks.

## Priorities
1. Correctness and safety over speed.
2. Clear scope and acceptance criteria before changes.
3. Automated verification whenever possible.
4. Small, reviewable commits and recoverable state.

## E2E loop
E2E loop = plan → issues → implement → test → review → commit → regression.

## Plan & issue generation
- Use the `plan` skill for plan and Issue CSV generation.
- Plans must include: steps, tests, risks, and rollback/safety notes.

## Issue CSV guidelines
- Every row must include: ID, Title, Description, Acceptance, Test_Method, Tools, Dev_Status, Review1_Status, Regression_Status, Files, Dependencies, Notes.
- Status values are enumerated (TODO/DOING/DONE), never percentages.
- If a task lacks a test method, add one or flag it as a risk.
- One plan maps to one issue CSV unless explicitly split.
- Follow `issues/README.md` for column definitions and CSV formatting.

## Tooling and tests
- Prefer local tools first; use MCP only when needed.
- Run the narrowest test that proves the change, then expand if risk is high.
- Do not claim tests ran if they did not.

## Tool usage
- When a matching MCP tool exists, use it; do not guess or simulate results.
- Prefer the tool specified in the Issue CSV `Tools` column.
- If a tool is unavailable or fails, note it and proceed with the safest alternative.

## Testing policy
- Follow `docs/testing-policy.md` for verification requirements and defaults.

## MCP tools catalog
- Follow `docs/mcp-tools.md` for available MCP tool names and usage.

## Safety
- Avoid destructive commands unless explicitly requested.
- Preserve backward compatibility unless asked to break it.
- Never expose secrets; redact if encountered.

## Output style
- Keep responses concise and structured.
- Provide file references with line numbers when editing.
- Always include risks and suggested next steps for non-trivial changes.
