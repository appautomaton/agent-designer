---
name: collaborating-with-claude
description: Delegate tasks to Claude Code CLI for prototyping, debugging, and code review. Supports multi-turn sessions via SESSION_ID.
metadata:
  short-description: Delegate to Claude Code CLI
---

# Collaborating with Claude Code

Use Claude Code CLI as a collaborator while Codex remains the primary implementer.

The bridge script (`scripts/claude_bridge.py`) wraps `claude --print`, returns structured JSON, and manages session continuity via `SESSION_ID`.

## Safety

Claude Code can read and edit files by default when run with `--print`. The bridge exposes flags to restrict this:

- `--permission-mode plan` — read-only mode, blocks edits and shell commands. **Recommended for review/consultation tasks.**
- `--disallowed-tools Edit Write Bash` — selectively block specific tools.
- Include `OUTPUT: Unified Diff Patch ONLY. Do not modify any files.` in your prompt for code changes. This is a convention, not enforced.

Always use the bridge script — do not invoke `claude` directly. This keeps output parsing and session handling consistent.

## When to use
- Second opinion on design tradeoffs, edge cases, or test gaps.
- Proposing or reviewing a unified diff.
- Multi-turn back-and-forth while you implement locally.

## When not to use
- Trivial one-shot tasks — do them in Codex directly.
- Tasks requiring authoritative facts with citations (Claude may guess).
- Anything involving secrets, private keys, or prod data.

## Quick start

⚠️ Backticks in prompts trigger shell command substitution — use a heredoc. See `references/shell-quoting.md`.

```bash
PROMPT="$(cat <<'EOF'
Review src/auth.py around login() and propose fixes.
OUTPUT: Unified Diff Patch ONLY.
EOF
)"
python3 .codex/skills/collaborating-with-claude/scripts/claude_bridge.py \
  --cd "." --model sonnet --PROMPT "$PROMPT" --output-format stream-json
```

**Returns:** `{ "success": true, "SESSION_ID": "...", "agent_messages": "..." }`

## Multi-turn sessions

Capture `SESSION_ID` from the first call and pass it back. Session selectors are mutually exclusive — pick one:

```bash
# Turn 1
python3 .codex/skills/collaborating-with-claude/scripts/claude_bridge.py \
  --cd "." --model sonnet --PROMPT "Analyze the bug in foo()." --output-format stream-json

# Turn 2 — resume by ID
python3 .codex/skills/collaborating-with-claude/scripts/claude_bridge.py \
  --cd "." --model sonnet --SESSION_ID "<id>" --PROMPT "Propose a fix." --output-format stream-json

# Or resume the most recent session
python3 .codex/skills/collaborating-with-claude/scripts/claude_bridge.py \
  --cd "." --model sonnet --continue --PROMPT "What about edge cases?" --output-format stream-json
```

Use `stream-json` or `json` output format to capture `SESSION_ID`. The `text` format does not emit one for new sessions.

## Bridge flags

**Core:**

| Flag | Purpose | Default |
|---|---|---|
| `--PROMPT` | Prompt text (required) | — |
| `--cd` | Workspace root (required) | — |
| `--model` | Model alias (`sonnet`, `opus`) or full name | CLI default |
| `--output-format` | `text` · `json` · `stream-json` | `stream-json` |

**Sessions** (mutually exclusive):

| Flag | Purpose |
|---|---|
| `--SESSION_ID` | Resume by session ID |
| `--session-id` | Use a specific UUID |
| `--continue` | Resume the most recent session |
| `--fork-session` | Fork when resuming (new ID, shared history) |

**Safety & permissions:**

| Flag | Purpose |
|---|---|
| `--permission-mode` | `default` · `plan` · `bypassPermissions` |
| `--allowed-tools` | Tools to allow without prompting (repeatable) |
| `--disallowed-tools` | Tools to block entirely (repeatable) |

**Advanced** (use `--help` for full list):
`--fallback-model` · `--max-budget-usd` · `--add-dir` · `--system-prompt` · `--append-system-prompt` · `--mcp-config` · `--json-schema` · `--tools` · `--agent` · `--agents` · `--no-session-persistence` · `--return-all-messages` · `--verbose` · `--include-partial-messages`

Default timeout: set `timeout_ms` to **600000** (10 min) when invoking via Codex command runner.

## Model selection

Use aliases — `--model sonnet` for routine work, `--model opus` for complex tasks. Omit `--model` to use the CLI's configured default. For strict reproducibility, pass a full model name.

## Prompting patterns

Use `assets/prompt-template.md` for structured starters. Key principles:

- **Point, don't paste** — give file paths and line numbers, not code blocks. Use `--cd` (and `--add-dir` if needed) so Claude can read files itself.
- **One objective per prompt** — multiple competing goals produce noisy output.
- **Enforce output format** — append `OUTPUT: Unified Diff Patch ONLY.` for code changes.

## Verification

- Smoke test: `python3 .codex/skills/collaborating-with-claude/scripts/claude_bridge.py --help`
- Session test: run one prompt with `--output-format stream-json`, confirm JSON contains `success: true` and a `SESSION_ID`.
- Ensure Claude Code is logged in (`claude` then `/login`) before headless usage.

## Collaboration State Capsule

Keep this block updated while collaborating:

```
[Claude Capsule] Goal: | SID: | Model: | Files: | Last: | Next:
```

## References
- [Prompt template](assets/prompt-template.md) — structured prompt patterns
- [Shell quoting](references/shell-quoting.md) — heredoc quoting for backticks
