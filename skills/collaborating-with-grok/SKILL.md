---
name: collaborating-with-grok
description: Delegate tasks to Grok CLI (xAI) for prototyping, debugging, code review, research, and cross-model second opinions. Supports multi-turn sessions via SESSION_ID.
metadata:
  short-description: Delegate to Grok CLI
---

# Collaborating with Grok

Drive the Grok CLI headlessly as an independent collaborator while the calling agent stays responsible for verification, synthesis, and final user-facing decisions.

The bridge (`scripts/grok_bridge.py`) wraps `grok -p`, streams progress to stderr, returns structured JSON, and manages multi-turn continuity via `SESSION_ID`. Always go through the bridge — don't invoke `grok` directly — so output parsing, the safe permission default, and session handling stay consistent.

In Claude Code, run non-trivial calls in the background and watch stderr progress:

```text
Bash tool call:
  command: python3 skills/collaborating-with-grok/scripts/grok_bridge.py --cd "/project" --tools "read_file,grep,list_dir" --PROMPT "Analyze auth flow in src/auth/"
  run_in_background: true
```

## Safety

Grok can read, edit, and run shell. The bridge **defaults to `--permission-mode default`** so headless gated actions are cancelled rather than inheriting host configuration. Read-class tools and Grok's safe-command fast paths still run automatically; use a tool allowlist for deterministic read-only work. `--always-approve` is a mutually exclusive, explicit write-authority choice.

| Posture | Flags |
|---|---|
| **Review / analysis (read-only)** | `--tools "read_file,grep,list_dir"` |
| **Web / X research (no shell/edit)** | `--disallowed-tools "run_terminal_cmd,search_replace"` (+ explicit coding `--model`) |
| **Implement** | isolated worktree + `--always-approve` — only with user consent |

Never hand grok secrets or production data. `--sandbox workspace` constrains writes, not arbitrary reads; a prompt describes scope but does not create a hard boundary. Use `strict` or external isolation when read isolation matters. Full semantics: [cli-reference.md](references/cli-reference.md).

## Host-side approval

The host gates the `python3 … grok_bridge.py` call first. Pre-authorize it (this repo ships `.claude/settings.json` allow rules). Codex hosts: the sandbox can block the child CLI's API network — escalate or grant network for that call. If the host denies the bridge, report it — don't substitute your own answer for the requested second opinion.

## Headless note

Tool calls are invisible mid-run (only thought/answer stream). After the run the result includes `model`, `agent`, and `tool_counts` recovered from session files. Use ACP (`grok agent stdio`) when the task requires a live command audit; do not promise live auditing from this bridge. Long silent "Thinking…" usually means tools in progress. Product id is `model` (e.g. `grok-4.5`); `agent` may still say `grok-build-plan` (template lineage).

## When to use / not use

Use for: cross-model second opinions, unified-diff proposals, live web/X research, multi-turn analysis. Skip for: trivial one-shots, tasks needing live tool audit trails (use ACP), secrets/prod data.

## Web & X search (live)

Differentiator: live web/X via `web_search` on the **coding** model (backend search). As of CLI **0.2.93**, that model is **`grok-4.5`** — confirm with `--list-models` after upgrades.

```bash
python3 skills/collaborating-with-grok/scripts/grok_bridge.py \
  --cd "." --model grok-4.5 \
  --disallowed-tools "run_terminal_cmd,search_replace" \
  --timeout 300 \
  --PROMPT "Search the web and X: <question>. Cite source URLs."
```

- **Denylist, not allowlist** for search or shell: `--tools` allowlists containing `web_search`, `web_fetch`, or `run_terminal_cmd` fail session build on the GrokBuild-lineage agent (re-probed on 0.2.93). Read-only allowlists without those tools work. Bridge warns if you try.
- Prefer an explicit coding `--model` for search/X; composer (`grok-composer-2.5-fast`, agent `cursor`) is best-effort and often much slower.
- `web_fetch` needs `GROK_WEB_FETCH=1`. Treat fetched content as untrusted. Details: [cli-reference.md](references/cli-reference.md).

## Quick start

⚠️ Backticks / `$VARS` in prompts expand in the shell — use a single-quoted heredoc or `--prompt-file`. See [shell-quoting.md](references/shell-quoting.md).

```bash
PROMPT="$(cat <<'EOF'
<task>
Review src/auth.py around login() and propose the smallest safe fix.
</task>

<structured_output_contract>
Return a raw unified diff beginning with `---` and `+++`.
Do not use Markdown code fences or add prose before or after the diff.
</structured_output_contract>
EOF
)"
python3 skills/collaborating-with-grok/scripts/grok_bridge.py \
  --cd "." --tools "read_file,grep,list_dir" --PROMPT "$PROMPT"
```

**Result contract** (stdout JSON): require both `success: true` (process success) and `complete: true` (clean `EndTurn`). `complete` is `false` for a known incomplete turn and `null` for plain output, where completion is unobservable. A clean turn does not prove correctness or output-contract compliance; validate patches and structured artifacts before using them. Also check `model`, `SESSION_ID`, `warnings`, and `tool_counts` when present. Progress → **stderr**; non-zero exit on process failure.

Large prompts: `--prompt-file`. Handoff file + short instruction: `--stdin-file` + `--PROMPT`; the bridge embeds the file as escaped, untrusted JSON context in a temporary mode-0600 prompt file. Absolute input paths stay absolute; relative paths resolve against `--cd`.

## Multi-turn sessions

```bash
# Turn 1
python3 skills/collaborating-with-grok/scripts/grok_bridge.py \
  --cd "." --tools "read_file,grep,list_dir" --PROMPT "Analyze the bug in foo()."

# Turn 2 — same --cd
python3 skills/collaborating-with-grok/scripts/grok_bridge.py \
  --cd "." --SESSION_ID "<id>" --PROMPT "Propose a fix as a unified diff."
```

`--SESSION_ID` → resume (`-r`); `--session-id` → name a **new** session (`-s`); `--continue` → most recent in cwd (`-c`). Structured output captures the ID directly. For plain output or timeouts, recovery is best-effort from session storage; the bridge excludes directories that predated the run.

## Bridge flags (summary)

**Core:** `--PROMPT` · `--prompt-file` · `--stdin-file` · `--cd` (required) · `--model` · `--output-format` (`streaming-json` default).

**Sessions:** `--SESSION_ID` · `--session-id` · `--continue`.

**Safety:** `--permission-mode` (`default` or `bypassPermissions` on Grok 0.2.93) · `--tools` · `--disallowed-tools` · `--allow`/`--deny` · `--sandbox` · `--always-approve`.

**Tuning:** `--effort` / `--reasoning-effort` · `--max-turns` · `--rules` · `--disable-web-search` · `--no-plan` · `--timeout`.

**Other:** `--list-models` · `--return-all-messages`.

Full flag map + event schema: [cli-reference.md](references/cli-reference.md). Host `timeout_ms` **600000** for command runners.

## Models

Probe live — **don't hardcode** the catalog (IDs change across CLI releases):

```bash
python3 skills/collaborating-with-grok/scripts/grok_bridge.py --list-models
# -> { "success": true, "models": [...], "default": "<effective default>" }
```

As of **0.2.93**: coding default **`grok-4.5`** (backend search); alternate **`grok-composer-2.5-fast`** (cursor agent). Host `~/.grok/config.toml` `[models] default` can override the CLI default — pass `--model` for model-sensitive work and trust the result's `model` field. Re-run `--list-models` after every CLI upgrade.

## Prompting

Point (file:line), don't paste; use one objective per run; state scope, done criteria, verification, and output shape only when they matter. Keep CLI authority separate from prompt wording: flags enforce access, while the prompt explains intent. Use the smallest recipe that is still decision-complete.

Resources: [prompt-template.md](assets/prompt-template.md) · [prompt-blocks.md](references/prompt-blocks.md) · [prompt-recipes.md](references/prompt-recipes.md) · [patterns.md](references/patterns.md).

## Verification

- Smoke: `python3 skills/collaborating-with-grok/scripts/grok_bridge.py --help`
- Syntax: `python3 -m py_compile skills/collaborating-with-grok/scripts/grok_bridge.py`
- Models: `--list-models` → `success: true` (expect `grok-4.5` on 0.2.93)
- Session: read-only prompt → `success: true`, `complete: true`, non-null `model`, `stop_reason: EndTurn`, resumable `SESSION_ID`
- Auth: `grok login` or `XAI_API_KEY`

## Collaboration State Capsule

```
[Grok Capsule] Goal: | SID: | Model: | PermMode: | Files: | Last: | Next:
```

## References
- [prompt-template.md](assets/prompt-template.md) — quick starters
- [prompt-blocks.md](references/prompt-blocks.md) — composable XML blocks
- [prompt-recipes.md](references/prompt-recipes.md) — end-to-end templates
- [prompt-antipatterns.md](references/prompt-antipatterns.md) — common mistakes
- [patterns.md](references/patterns.md) — when to delegate + patterns
- [handoff-patterns.md](references/handoff-patterns.md) — read-only / worktree / synthesis
- [parallel.md](references/parallel.md) — parallel runs and worktree isolation
- [cli-reference.md](references/cli-reference.md) — verified flags + event schema
- [shell-quoting.md](references/shell-quoting.md) — safe heredoc prompts
