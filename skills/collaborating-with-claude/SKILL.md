---
name: collaborating-with-claude
description: Delegate tasks to Claude Code CLI for prototyping, debugging, and code review. Supports multi-turn sessions via SESSION_ID.
metadata:
  short-description: Delegate to Claude Code CLI
---

# Collaborating with Claude Code

Drive Claude Code headlessly as an independent collaborator while the calling agent stays responsible for verification, synthesis, and final user-facing decisions.

The bridge (`scripts/claude_bridge.py`) wraps `claude --print`, streams progress to stderr, returns structured JSON with telemetry, and manages multi-turn continuity via `SESSION_ID`. Always go through the bridge — don't invoke `claude` directly — so output parsing and session handling stay consistent.

In Claude Code, run non-trivial calls in the background and watch the stderr progress:

```text
Bash tool call:
  command: python3 skills/collaborating-with-claude/scripts/claude_bridge.py --cd "/project" --PROMPT "Analyze auth flow in src/auth/"
  run_in_background: true
```

`run_in_background` is a host tool parameter, not a shell argument. Use the task-output view to monitor timestamped stderr progress (session, responses, tools, cost) and the final JSON result.

## Safety

Default to read-only delegation: `--permission-mode plan` (analyze, no edits/commands) or `--tools "Read,Glob,Grep"`. Grant writes only deliberately (`acceptEdits`/`auto`), preferably in an isolated worktree. Do not hand secrets, private keys, or production data to Claude. Full permission-mode set and the worktree pattern: [cli-reference.md](references/cli-reference.md), [handoff-patterns.md](references/handoff-patterns.md).

## When to use / not use

Use for: second opinions on design, edge cases, or test gaps; proposing or reviewing a unified diff; multi-turn analysis while you implement. Skip for: trivial one-shot edits (do them directly); tasks needing authoritative cited facts (Claude may guess); anything touching secrets or prod data.

## Quick start

⚠️ Backticks / `$VARS` in prompts trigger shell expansion — use a single-quoted heredoc, or `--prompt-file` for large/generated prompts. See [shell-quoting.md](references/shell-quoting.md).

```bash
PROMPT="$(cat <<'EOF'
Review src/auth.py around login() and propose fixes.
OUTPUT: Unified Diff Patch ONLY.
EOF
)"
python3 skills/collaborating-with-claude/scripts/claude_bridge.py \
  --cd "." --model sonnet --permission-mode plan --PROMPT "$PROMPT" --output-format stream-json
```

For large or shell-sensitive prompts, write the prompt to a file and pass `--prompt-file /tmp/prompt.md` (piped via stdin — no argv/quoting limits).

**Returns** (stdout JSON): `{ "success": true, "SESSION_ID": "...", "agent_messages": "...", "model": "...", "subtype": "success", "total_cost_usd": 0.03, "usage": {...}, "num_turns": 1 }` — plus `tools_used` / `permission_denials` / `structured_output` / `is_error` when relevant. Progress streams to **stderr**; the bridge exits non-zero on failure.

## Multi-turn sessions

Capture `SESSION_ID` from the first call and pass it back (selectors are mutually exclusive):

```bash
# Turn 1
python3 skills/collaborating-with-claude/scripts/claude_bridge.py \
  --cd "." --model sonnet --PROMPT "Analyze the bug in foo()." --output-format stream-json

# Turn 2 — resume by ID (use the same --cd)
python3 skills/collaborating-with-claude/scripts/claude_bridge.py \
  --cd "." --model sonnet --SESSION_ID "<id>" --PROMPT "Propose a fix." --output-format stream-json

# Or resume the most recent session in this directory
python3 skills/collaborating-with-claude/scripts/claude_bridge.py \
  --cd "." --model sonnet --continue --PROMPT "What about edge cases?" --output-format stream-json
```

Use `stream-json` or `json` output to capture `SESSION_ID`.

## Bridge flags

**Core:** `--PROMPT` (or `--prompt-file`) · `--cd` (required) · `--model` (`sonnet`/`opus`/full id) · `--output-format` (`text`·`json`·`stream-json`, default `stream-json`).

**Sessions** (mutually exclusive): `--SESSION_ID` · `--session-id <uuid>` · `--continue`; plus `--fork-session`, `--no-session-persistence`.

**Permissions:** `--permission-mode` (`default`·`plan`·`acceptEdits`·`auto`·`dontAsk`·`bypassPermissions`) · `--tools` · `--allowed-tools` · `--disallowed-tools`. Footgun: the space in `Bash(git diff *)` is load-bearing.

**Reproducibility & cost:** `--bare` / `--safe-mode` (skip customizations; `--bare` needs `ANTHROPIC_API_KEY`) · `--effort` (`low`→`max`) · `--max-budget-usd` · `--max-turns` · `--timeout <seconds>`.

**Context & advanced:** `--prompt-file` · `--system-prompt[-file]` · `--append-system-prompt[-file]` · `--add-dir` · `--json-schema` · `--mcp-config` · `--settings` · `--agent`/`--agents` · `--return-all-messages` · `--verbose`.

Full semantics in [cli-reference.md](references/cli-reference.md). Set the host's `timeout_ms` to **600000** (10 min) when invoking via a command runner.

## Tune performance

`--model sonnet` for routine work, `--model opus` for hard tasks; `--effort low→max` trades depth for speed/cost; `--max-budget-usd` caps spend. Omit `--model` to use the CLI default.

## Prompting

Quick starters in [prompt-template.md](assets/prompt-template.md); composable XML blocks in [prompt-blocks.md](references/prompt-blocks.md); end-to-end recipes in [prompt-recipes.md](references/prompt-recipes.md); delegation patterns and principles in [patterns.md](references/patterns.md). In short: point (file:line), don't paste; one objective per run; state the output shape; verify Claude's output before acting.

## Verification

- Smoke: `python3 skills/collaborating-with-claude/scripts/claude_bridge.py --help`
- Syntax: `python3 -m py_compile skills/collaborating-with-claude/scripts/claude_bridge.py`
- Session: run a prompt with `--output-format stream-json`; confirm JSON has `success: true`, a `SESSION_ID`, and telemetry (`subtype`/`total_cost_usd`/`usage`/`num_turns`); failures exit non-zero.
- Ensure Claude is logged in (`claude` then `/login`), or set `ANTHROPIC_API_KEY` (required for `--bare`).

## Collaboration State Capsule

Keep this updated across turns (referenced by [handoff-patterns.md](references/handoff-patterns.md)):

```
[Claude Capsule] Goal: | SID: | Model: | PermMode: | Files: | Last: | Next:
```

## References
- [prompt-template.md](assets/prompt-template.md) — quick plain-text starters
- [prompt-blocks.md](references/prompt-blocks.md) — composable XML blocks
- [prompt-recipes.md](references/prompt-recipes.md) — end-to-end templates
- [prompt-antipatterns.md](references/prompt-antipatterns.md) — common mistakes
- [patterns.md](references/patterns.md) — when to delegate + prompt patterns
- [handoff-patterns.md](references/handoff-patterns.md) — read-only / worktree / synthesis
- [parallel.md](references/parallel.md) — parallel runs and worktree isolation
- [cli-reference.md](references/cli-reference.md) — verified Claude CLI flags + event schema
- [shell-quoting.md](references/shell-quoting.md) — safe heredoc prompts
