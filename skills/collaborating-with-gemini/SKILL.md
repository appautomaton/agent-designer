---
name: collaborating-with-gemini
description: Delegate tasks to Gemini CLI for prototyping, debugging, code review, and web search. Supports multi-turn sessions via SESSION_ID.
metadata:
  short-description: Delegate to Gemini CLI
---

# Collaborating with Gemini

Use Gemini CLI as a collaborator while Codex remains the primary implementer.

The bridge script (`scripts/gemini_bridge.py`) wraps `gemini -p` (headless mode), returns structured JSON, and manages session continuity via `SESSION_ID`.

## Safety

Gemini can read and write files in the workspace by default. The bridge does **not** restrict this.

To limit what Gemini can do:
- `--sandbox` — blocks shell commands and file writes. **Recommended for review/consultation tasks.**
- Include `OUTPUT: Unified Diff Patch ONLY. Do not modify any files.` in your prompt when requesting code changes. This is a convention, not enforced.

⚠️ `--approval-mode plan` does NOT reliably prevent writes — Gemini may self-approve plans and use shell commands to bypass file-write restrictions. Do not rely on it for safety.

## When to use
- Second opinion on design tradeoffs, edge cases, or test gaps.
- Web search and research (Gemini has built-in grounding).
- Reviewing a diff or proposing changes as unified diff.
- Screenshot / image analysis.

## When not to use
- Trivial one-shot tasks — do them in Codex directly.
- Tasks requiring file edits — Codex edits, Gemini advises.
- Anything involving secrets, private keys, or prod data.

## Quick start

⚠️ Backticks in prompts trigger shell command substitution — use a heredoc. See `references/shell-quoting.md`.

```bash
PROMPT="$(cat <<'EOF'
Review src/auth.py around login() and propose fixes.
OUTPUT: Unified Diff Patch ONLY.
EOF
)"
python3 .codex/skills/collaborating-with-gemini/scripts/gemini_bridge.py \
  --cd "." --PROMPT "$PROMPT"
```

**Returns:** `{ "success": true, "SESSION_ID": "...", "agent_messages": "..." }`

## Multi-turn sessions

Capture `SESSION_ID` from the first call and pass it back:

```bash
# Turn 1
python3 .codex/skills/collaborating-with-gemini/scripts/gemini_bridge.py \
  --cd "." --PROMPT "Analyze the bug in foo()."

# Turn 2 — resume
python3 .codex/skills/collaborating-with-gemini/scripts/gemini_bridge.py \
  --cd "." --SESSION_ID "<id>" --PROMPT "Propose a fix as unified diff."
```

Sessions are persisted by the Gemini CLI at `~/.gemini/tmp/<project>/chats/`. The bridge captures and returns the ID — the caller is responsible for storing and reusing it.

## Bridge flags

| Flag | Purpose | Default |
|---|---|---|
| `--PROMPT` | Prompt text (required) | — |
| `--cd` | Workspace root (required) | — |
| `--SESSION_ID` | Resume a previous session | new session |
| `--model` | Override Gemini model | CLI default |
| `--sandbox` | Block shell and file writes | off |
| `--approval-mode` | `default` · `auto_edit` · `yolo` · `plan` | CLI default |
| `--include-directories` | Additional workspace dirs (repeatable) | none |
| `--return-all-messages` | Include tool calls and traces in output | off |

Default timeout: set `timeout_ms` to **600000** (10 min) when invoking via Codex command runner.

## Prompting patterns

Use `assets/prompt-template.md` for structured starters. Key principles:

- **Point, don't paste** — give file paths and line numbers, not code blocks.
- **One objective per prompt** — multiple competing goals produce noisy output.
- **Enforce output format** — append `OUTPUT: Unified Diff Patch ONLY.` for code changes.
- **Leverage grounding** — Gemini can search the web; ask for research when needed.

### Screenshots

Gemini can only read files inside the workspace. Copy clipboard PNGs into `.codex_uploads/` first:

```bash
mkdir -p .codex_uploads && cp "${TMPDIR:-/tmp}"/codex-clipboard-*.png .codex_uploads/
```

Do **not** add `.codex_uploads/` to `.gitignore` — Gemini refuses to read ignored paths. Delete screenshots when done.

## Verification

- Smoke test: `python3 .codex/skills/collaborating-with-gemini/scripts/gemini_bridge.py --help`
- Session test: run one prompt, confirm JSON contains `success: true` and a `SESSION_ID`.

## Collaboration State Capsule

Keep this block updated while collaborating:

```
[Gemini Capsule] Goal: | SID: | Files: | Last: | Next:
```

## References
- [Prompt template](assets/prompt-template.md) — structured prompt patterns
- [Shell quoting](references/shell-quoting.md) — heredoc quoting for backticks
