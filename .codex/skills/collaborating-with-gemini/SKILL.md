---
name: collaborating-with-gemini
description: Delegate coding tasks to Gemini CLI for prototyping, debugging, and code review. Supports multi-turn sessions via SESSION_ID. Optimized for low-token, file/line-based handoff.
metadata:
  short-description: Delegate to Gemini CLI
---

# Collaborating with Gemini (Codex)

Use Gemini CLI as a collaborator while keeping Codex as the primary implementer.

This skill provides a lightweight bridge script that returns structured JSON and supports multi-turn sessions via `SESSION_ID`.

## Core rules
- Gemini is a collaborator; you own the final result and must verify changes locally.
- Prefer file/line references over pasting snippets. Let Gemini read the repo via `--cd`.
- For code changes, request **Unified Diff Patch ONLY** and forbid direct file modification.
- Always capture `SESSION_ID` and reuse it for follow-ups to keep the collaboration conversation-aware.
- Keep a short **Collaboration State Capsule** updated while this skill is active.
- Default timeout: when invoking via the Codex command runner, set `timeout_ms` to **600000 (10 minutes)** unless a shorter/longer timeout is explicitly required.

## Quick start

```bash
python .codex/skills/collaborating-with-gemini/scripts/gemini_bridge.py --cd "." --PROMPT "Review src/auth.py around login() and propose fixes. OUTPUT: Unified Diff Patch ONLY."
```

**Output:** JSON with `success`, `SESSION_ID`, `agent_messages`, and optional `error` / `all_messages`.

## Multi-turn sessions

```bash
# Start a session
python .codex/skills/collaborating-with-gemini/scripts/gemini_bridge.py --cd "." --PROMPT "Analyze the bug in foo(). Keep it short."

# Continue the same session
python .codex/skills/collaborating-with-gemini/scripts/gemini_bridge.py --cd "." --SESSION_ID "<SESSION_ID>" --PROMPT "Now propose a minimal fix as Unified Diff Patch ONLY."
```

## Prompting patterns (token efficient)

Use `assets/prompt-template.md` as a starter when crafting `--PROMPT`.

### 1) Ask Gemini to open files itself
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

### 3) Use Gemini for what it’s good at
- Alternative solution paths and edge cases
- UI/UX and readability feedback
- Review of a proposed patch (risk spotting, missing tests)

## Collaboration State Capsule
Keep this short block updated near the end of your reply while collaborating:

```text
[Gemini Collaboration Capsule]
Goal:
Gemini SESSION_ID:
Files/lines handed off:
Last ask:
Gemini summary:
Next ask:
```
