---
name: collaborating-with-claude
description: Delegate coding tasks to Claude Code CLI for prototyping, debugging, and code review. Supports multi-turn sessions via SESSION_ID. Optimized for low-token, file/line-based handoff.
metadata:
  short-description: Delegate to Claude Code CLI
---

# Collaborating with Claude Code (Codex)

Use Claude Code CLI as a collaborator while keeping Codex as the primary implementer.

This skill provides a lightweight bridge script that returns structured JSON and supports multi-turn sessions via `SESSION_ID`.

## Core rules
- Claude is a collaborator; you own the final result and must verify changes locally.
- Do not invoke `claude` directly; always use the bridge script (`scripts/claude_bridge.py`) so output/session handling stays consistent.
- Prefer file/line references over pasting snippets. Run the bridge with `--cd` set to the repo root (it sets the `claude` process working directory); use `--add-dir` when Claude needs access to additional directories.
- For code changes, request **Unified Diff Patch ONLY** and forbid direct file modification.
- Always run the bridge script with `--help` first if you are unsure of parameters.
- Always capture `SESSION_ID` and reuse it for follow-ups to keep the collaboration conversation-aware.
- For automation, prefer `--SESSION_ID` (resume). Session selectors are mutually exclusive: choose one of `--SESSION_ID`, `--continue`, or `--session-id`.
- Keep a short **Collaboration State Capsule** updated while this skill is active.
- Default timeout: when invoking via the Codex command runner, set `timeout_ms` to **600000 (10 minutes)** unless a shorter/longer timeout is explicitly required.
- Default model: prefer `sonnet` for routine work; use `opus` only for complex tasks or when explicitly requested.
- Ensure Claude Code is logged in before running headless commands (run `claude` and `/login` once if needed).
- Streamed JSON requires `--verbose`; the bridge enables this automatically.

## Model selection

Claude Code supports model aliases, so you can use `--model sonnet` / `--model opus` instead of hard-coding versioned model IDs.

- If you omit `--model`, Claude Code uses its configured default (typically from `~/.claude/settings.json`, optionally overridden by `.claude/settings.json` and `.claude/settings.local.json`).
- If you need strict reproducibility, pass a full model name via `--model <full-name>`.

## Quick start

```bash
python3 .codex/skills/collaborating-with-claude/scripts/claude_bridge.py --cd "." --PROMPT "Review src/auth.py around login() and propose fixes. OUTPUT: Unified Diff Patch ONLY."
```

**Output:** JSON with `success`, `SESSION_ID`, `agent_messages`, and optional `error` / `all_messages`.

## Multi-turn sessions

```bash
# Start a session
python3 .codex/skills/collaborating-with-claude/scripts/claude_bridge.py --cd "." --PROMPT "Analyze the bug in foo(). Keep it short."

# Continue the same session
python3 .codex/skills/collaborating-with-claude/scripts/claude_bridge.py --cd "." --SESSION_ID "<SESSION_ID>" --PROMPT "Now propose a minimal fix as Unified Diff Patch ONLY."
```

## Prompting patterns (token efficient)

Use `assets/prompt-template.md` as a starter when crafting `--PROMPT`.

### 1) Ask Claude to open files itself
Provide:
- Entry file(s) and approximate line numbers
- Objective and constraints
- Output format (diff vs analysis)

Avoid:
- Pasting large code blocks
- Multiple competing objectives in one request

### 2) Enforce safe output for code changes
Append this to prompts when requesting code:
- `OUTPUT: Unified Diff Patch ONLY. Strictly prohibit any actual modifications.`

### 3) Use Claude for what it’s good at
- Alternative solution paths and edge cases
- UI/UX and readability feedback
- Review of a proposed patch (risk spotting, missing tests)

## Collaboration State Capsule
Keep this short block updated near the end of your reply while collaborating:

```text
[Claude Collaboration Capsule]
Goal:
Claude SESSION_ID:
Files/lines handed off:
Last ask:
Claude summary:
Next ask:
```
