---
name: collaborating-with-antigravity
description: Delegate tasks to Google's Antigravity CLI (agy) for prototyping, debugging, code review, and research. Supports multi-turn sessions via SESSION_ID. Replaces the retiring Gemini CLI.
metadata:
  short-description: Delegate to Antigravity CLI (agy)
---

# Collaborating with Antigravity (agy)

Use the Antigravity CLI (`agy`) as a collaborator while Codex remains the primary implementer.
Antigravity CLI is Google's replacement for the **retiring Gemini CLI** (hosted auth shuts off
2026-06-18). If you used `collaborating-with-gemini`, switch to this skill.

The bridge script (`scripts/agy_bridge.py`) wraps `agy -p` (headless print mode), returns structured
JSON, and manages session continuity via `SESSION_ID`. **Always go through the bridge** — invoking
`agy -p` directly is unreliable (see below).

## Why the bridge is mandatory

Two `agy` v1.0.8 quirks make raw `agy -p` unusable from a script; the bridge handles both:

- **It hangs with no output when stdout is a pipe.** `agy -p foo > file` writes nothing and never
  exits — even `--print-timeout` is ignored. The bridge runs `agy` under a pseudo-terminal (pty) so
  its TTY check passes, and enforces its own wall-clock kill. (Upstream issue #76.)
- **It never tells you the conversation ID.** There is no `--session-id`. The bridge recovers the ID
  from `~/.gemini/antigravity-cli/cache/last_conversations.json` (workspace → UUID) and resumes via
  `--conversation`. (Upstream issue #7.) Because `agy` rewrites that cache every run, the bridge takes
  a file lock to serialize calls — **do not run bridge calls concurrently.**

Details and the verified flag surface: [references/agy-cli.md](references/agy-cli.md).

## Safety

`agy` can read and write files and run tools in the workspace. To constrain it:

- `--sandbox` is **on by default** in the bridge — it applies agy's terminal restrictions.
  **Recommended for review/consultation.** Use `--no-sandbox` only when you deliberately want edits/shell.
- Include `OUTPUT: Unified Diff Patch ONLY. Do not modify any files.` in the prompt when requesting
  code changes. This is a convention, not enforced.
- `--skip-permissions` maps to agy's `--dangerously-skip-permissions` (auto-approves every tool). Only
  use it with explicit user consent, ideally in an isolated worktree.
- Never hand `agy` secrets, private keys, or production data.

## When to use
- Second opinion on design tradeoffs, edge cases, or test gaps.
- Web search / research (Antigravity has built-in grounding).
- Reviewing a diff or proposing changes as a unified diff.
- Screenshot / image analysis.

## When not to use
- Trivial one-shot tasks — do them in Codex directly.
- Tasks requiring file edits — Codex edits, agy advises.
- Anything involving secrets, private keys, or prod data.

## Quick start

⚠️ Backticks / `$VARS` in prompts trigger shell expansion — use a single-quoted heredoc, or
`--prompt-file` for large/generated prompts. See [references/shell-quoting.md](references/shell-quoting.md).

```bash
PROMPT="$(cat <<'EOF'
Review src/auth.py around login() and propose fixes.
OUTPUT: Unified Diff Patch ONLY.
EOF
)"
python3 skills/collaborating-with-antigravity/scripts/agy_bridge.py \
  --cd "." --model "Gemini 3.5 Flash (Low)" --PROMPT "$PROMPT"
```

**Returns** (stdout JSON): `{ "success": true, "SESSION_ID": "...", "agent_messages": "...", "model": "...", "warnings": [...] }`.
Live progress streams to **stderr**; the bridge exits non-zero on failure. In Codex, run non-trivial
calls in the background and watch the stderr progress.

## Multi-turn sessions

Capture `SESSION_ID` from the first call and pass it back (use the same `--cd`):

```bash
# Turn 1
python3 skills/collaborating-with-antigravity/scripts/agy_bridge.py \
  --cd "." --PROMPT "Analyze the bug in foo()."

# Turn 2 — resume by ID
python3 skills/collaborating-with-antigravity/scripts/agy_bridge.py \
  --cd "." --SESSION_ID "<id>" --PROMPT "Propose a fix as a unified diff."

# Or continue the most recent conversation
python3 skills/collaborating-with-antigravity/scripts/agy_bridge.py \
  --cd "." --continue --PROMPT "What about edge cases?"
```

`--SESSION_ID` and `--continue` are mutually exclusive. Sessions persist as SQLite under
`~/.gemini/antigravity-cli/conversations/<id>.db`; the bridge surfaces the ID — the caller stores and reuses it.

## Bridge flags

| Flag | Purpose | Default |
|---|---|---|
| `--PROMPT` / `--prompt-file` | Prompt text, or read it from a file (mutually exclusive) | — |
| `--cd` | Workspace root (required) | — |
| `--SESSION_ID` | Resume a conversation by ID (→ `agy --conversation`) | new conversation |
| `--continue` | Continue the most recent conversation (→ `agy -c`) | off |
| `--model` | Model from `agy models`, e.g. `"Gemini 3.5 Flash (Low)"`, `"Claude Sonnet 4.6 (Thinking)"` | CLI default |
| `--sandbox` / `--no-sandbox` | agy terminal restrictions | **on** |
| `--skip-permissions` | Auto-approve all tools (`--dangerously-skip-permissions`) | off |
| `--add-dir` | Additional workspace dir (repeatable) | none |
| `--print-timeout` | agy print wait, e.g. `5m`/`90s` (agy may ignore it) | `5m` |
| `--timeout` | Bridge wall-clock kill, seconds (the real cap) | print-timeout + 120s |
| `--log-file` | Override agy's log path | none |
| `--return-all-messages` | Include `raw_output` and the conversation `.db` path | off |

Set the host's `timeout_ms` to **600000** (10 min) when invoking via a command runner.

## Models

From `agy models`: `Gemini 3.5 Flash (Low|Medium|High)`, `Gemini 3.1 Pro (Low|High)`,
`Claude Sonnet 4.6 (Thinking)`, `Claude Opus 4.6 (Thinking)`, `GPT-OSS 120B (Medium)`. Pass the exact
human-readable string to `--model`. Use Flash (Low) for quick checks, Pro / Claude for hard tasks.

## Prompting

Use [assets/prompt-template.md](assets/prompt-template.md) for structured starters. Key principles:

- **Point, don't paste** — give file paths and line numbers, not code blocks.
- **One objective per prompt** — competing goals produce noisy output.
- **Enforce output format** — append `OUTPUT: Unified Diff Patch ONLY.` for code changes.
- **Leverage grounding** — agy can search the web; ask for research when needed.

### Screenshots

agy reads files inside the workspace. Copy clipboard PNGs in first, then reference the path:

```bash
mkdir -p .codex_uploads && cp "${TMPDIR:-/tmp}"/codex-clipboard-*.png .codex_uploads/
```

Delete screenshots when done.

## Verification

- Smoke: `python3 skills/collaborating-with-antigravity/scripts/agy_bridge.py --help`
- Syntax: `python3 -m py_compile skills/collaborating-with-antigravity/scripts/agy_bridge.py`
- Auth: run `agy` once and sign in with Google (token at `~/.gemini/antigravity-cli/`).
- Session test: run one prompt; confirm JSON has `success: true` and a `SESSION_ID`, then resume with
  `--SESSION_ID` and confirm continuity.

## Collaboration State Capsule

Keep this block updated while collaborating:

```
[Antigravity Capsule] Goal: | SID: | Model: | Sandbox: | Files: | Last: | Next:
```

## References
- [references/agy-cli.md](references/agy-cli.md) — verified `agy` v1.0.8 flags, models, file layout, known bugs
- [assets/prompt-template.md](assets/prompt-template.md) — structured prompt patterns
- [references/shell-quoting.md](references/shell-quoting.md) — heredoc quoting for backticks
