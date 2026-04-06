---
name: collaborating-with-codex
description: Delegate tasks to Codex CLI for prototyping, debugging, code review, and implementation. Supports multi-turn sessions via SESSION_ID.
metadata:
  short-description: Delegate to Codex CLI
---

# Collaborating with Codex

Use Codex CLI as a collaborator while your primary agent remains the implementer.

The bridge script (`scripts/codex_bridge.py`) wraps `codex exec` (headless mode), returns structured JSON, and manages session continuity via `SESSION_ID`.

## Safety

Codex runs in a sandbox by default. The bridge defaults to `read-only`:

- `--sandbox read-only` — **(default)** no file writes, no destructive commands. Recommended for review/consultation.
- `--sandbox workspace-write` — can write files in the workspace only.
- `--sandbox danger-full-access` — unrestricted. Use only in externally sandboxed environments.
- `--full-auto` — convenience alias for sandboxed auto-execution (`workspace-write` + auto-approve).

Do not use `--full-auto` or `danger-full-access` unless you understand the implications.

## When to use
- Algorithm implementation, bug analysis, or code generation.
- Code review or adversarial review.
- Second opinion on architecture, edge cases, or test gaps.
- Research or diagnosis with tool use.

## When not to use
- Trivial tasks your primary agent can handle directly.
- Anything involving secrets, private keys, or prod data.

## Quick start

⚠️ Backticks in prompts trigger shell command substitution — use a heredoc. See `references/shell-quoting.md`.

```bash
PROMPT="$(cat <<'EOF'
Review src/auth.py around login() and propose fixes.
OUTPUT: Unified Diff Patch ONLY.
EOF
)"
python3 skills/collaborating-with-codex/scripts/codex_bridge.py \
  --cd "." --PROMPT "$PROMPT"
```

**Returns:** `{ "success": true, "SESSION_ID": "...", "agent_messages": "..." }`

## Multi-turn sessions

Capture `SESSION_ID` from the first call and pass it back:

```bash
# Turn 1
python3 skills/collaborating-with-codex/scripts/codex_bridge.py \
  --cd "." --PROMPT "Analyze the bug in foo()."

# Turn 2 — resume by ID
python3 skills/collaborating-with-codex/scripts/codex_bridge.py \
  --cd "." --SESSION_ID "<id>" --PROMPT "Propose a fix."

# Or resume the most recent session
python3 skills/collaborating-with-codex/scripts/codex_bridge.py \
  --cd "." --last --PROMPT "What about edge cases?"
```

## Bridge flags

| Flag | Purpose | Default |
|---|---|---|
| `--PROMPT` | Prompt text (required) | — |
| `--cd` | Workspace root (required) | — |
| `--SESSION_ID` | Resume a previous session by thread ID | new session |
| `--last` | Resume the most recent session | off |
| `--model` | Override Codex model | CLI default |
| `--sandbox` | `read-only` · `workspace-write` · `danger-full-access` | `read-only` |
| `--full-auto` | Sandboxed auto-execution | off |
| `--image` | Attach image files (repeatable) | none |
| `--add-dir` | Additional writable directories (repeatable) | none |
| `--skip-git-repo-check` | Allow running outside a Git repo | off |
| `--ephemeral` | Don't persist session to disk | off |
| `--return-all-messages` | Include all JSONL events in output | off |

Default timeout: set `timeout_ms` to **600000** (10 min) when invoking via an external command runner.

## Prompting patterns

Use `assets/prompt-template.md` for quick plain-text starters. For complex tasks, use composable XML prompt blocks — see `references/prompt-blocks.md`.

Key principles:

- **Point, don't paste** — give file paths and line numbers, not code blocks.
- **One objective per prompt** — multiple competing goals produce noisy output.
- **State what done looks like** — Codex works best with explicit acceptance criteria.
- **Use prompt blocks** — wrap objectives in `<task>`, add `<verification_loop>` for correctness, `<grounding_rules>` for reviews.
- **Enforce output format** — append `OUTPUT: Unified Diff Patch ONLY.` for code changes when using `read-only` sandbox.

## Verification

- Smoke test: `python3 skills/collaborating-with-codex/scripts/codex_bridge.py --help`
- Session test: run one prompt, confirm JSON contains `success: true` and a `SESSION_ID`.

## Collaboration State Capsule

Keep this block updated while collaborating:

```
[Codex Capsule] Goal: | SID: | Sandbox: | Files: | Last: | Next:
```

## References
- [Prompt template](assets/prompt-template.md) — quick plain-text starters
- [Prompt blocks](references/prompt-blocks.md) — composable XML blocks for structured prompts
- [Prompt recipes](references/prompt-recipes.md) — end-to-end templates (diagnosis, fix, review, research)
- [Prompt anti-patterns](references/prompt-antipatterns.md) — common mistakes to avoid
- [Shell quoting](references/shell-quoting.md) — heredoc quoting for backticks
