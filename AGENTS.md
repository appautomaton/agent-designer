# AGENTS

> Purpose: design and maintain Codex/Claude-style skills, plus supporting docs and MCP tool catalog.

## Priorities
1. Correctness and safety over speed.
2. Clear scope and acceptance criteria before changes.
3. Automated verification whenever possible.
4. Small, reviewable commits and recoverable state.

## Tooling and tests
- Prefer local tools first; use MCP only when needed.
- Run the narrowest test that proves the change, then expand if risk is high.
- Do not claim tests ran if they did not.

## Safety
- Avoid destructive commands unless explicitly requested.
- Preserve backward compatibility unless asked to break it.
- Never expose secrets; redact if encountered.

## Output style
- Keep responses concise and structured.
- Provide file references with line numbers when editing.
- Always include risks and suggested next steps for non-trivial changes.
