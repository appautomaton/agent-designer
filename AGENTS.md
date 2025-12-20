# AGENTS

> Purpose: consistent, reliable Codex execution for complex tasks.

## Priorities
1. Correctness and safety over speed.
2. Clear scope and acceptance criteria before changes.
3. Automated verification whenever possible.
4. Small, reviewable commits and recoverable state.

## E2E loop
E2E loop = plan → issues → implement → test → review → commit → regression.
1. **Restate request + assumptions**. Ask only essential clarifying questions.
2. **Plan when scope is medium/complex** (multi-file, design choices, or cross-system). Produce a short plan before editing.
3. **Define task contract** using an Issue CSV (or equivalent): scope, acceptance, test method, and status fields (TODO/DOING/DONE).
4. **Execute per issue**: implement → test → review → commit → mark done.
5. **Regression pass** after all issues; fix failures until acceptance criteria pass.

## Planning rules
- If a plan exists, follow it; propose edits rather than re-plan ad hoc.
- Plans must include: steps, tests, risks, and rollback/safety notes.
- Use `plan/_template.md` to create new plans in `plan/` (timestamped file name).
- Naming: `plan/YYYY-MM-DD_HH-mm-ss-<slug>.md` and `issues/YYYY-MM-DD_HH-mm-ss-<slug>.csv` (same timestamp/slug).

## Issue CSV guidelines
- Every row must include: ID, Title, Description, Acceptance, Test_Method, Tools, Dev_Status, Review1_Status, Regression_Status, Files, Dependencies, Notes.
- Status values are enumerated (TODO/DOING/DONE), never percentages.
- If a task lacks a test method, add one or flag it as a risk.
- Use `issues/_template.csv` for new issue batches in `issues/`.
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

## Safety
- Avoid destructive commands unless explicitly requested.
- Preserve backward compatibility unless asked to break it.
- Never expose secrets; redact if encountered.

## Output style
- Keep responses concise and structured.
- Provide file references with line numbers when editing.
- Always include risks and suggested next steps for non-trivial changes.
