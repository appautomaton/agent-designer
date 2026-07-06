# Antigravity CLI (`agy`) reference

**Verification status:** verified against `agy` v1.0.16 on macOS (2026-07-06). The interface is
changing fast; re-check `agy --help` / `agy models` if behavior drifts. Project scoping
(`--project`/`--new-project`) drops a `.antigravitycli/<project-uuid>.json` symlink in the
workspace — gitignore it.

## Install & auth

```bash
curl -fsSL https://antigravity.google/cli/install.sh | bash   # installs `agy` to ~/.local/bin
agy --version                                                  # non-interactive version check
```

Auth is **Google OAuth, no API key**. On first run `agy` opens a browser (or, over SSH, prints a URL +
one-time code) and caches credentials under `~/.gemini/antigravity-cli/` (the exact artifact varies by
version). The bridge warns if agy has never run on the host.

## Verified flag surface (`agy --help`)

```
--add-dir                       Add a directory to the workspace (repeatable)
-c, --continue                  Continue the most recent conversation
--conversation <id>             Resume a previous conversation by ID
--dangerously-skip-permissions  Auto-approve all tool permission requests
-i, --prompt-interactive        Run an initial prompt, then stay interactive
--log-file <path>               Override CLI log file path
--model <name>                  Model for the session (see `agy models`)
-p, --print, --prompt <text>    Run a single prompt non-interactively
--print-timeout <dur>           Print-mode wait (default 5m0s)
--sandbox                       Run with terminal restrictions enabled
--project <id>                  Project ID for the session
--new-project                   Create a new project for this session
```

Subcommands: `changelog`, `help`, `install`, `models`, `plugin`/`plugins`, `update`.

**Notably absent** (do not assume parity with Gemini CLI):
- No `--output-format` / `--json` → no structured output; the bridge captures and cleans text.
- No `--session-id` / supplied-UUID resume → only `--conversation <id>` (known id) and `-c` (most recent).
- No `--no-color` → the bridge strips ANSI/spinner sequences itself.

## Models (`agy models`)

Probe the live set with `agy models` (or `agy_bridge.py --list-models`). Snapshot:
`Gemini 3.5 Flash (Low)`, `Gemini 3.5 Flash (Medium)`, `Gemini 3.5 Flash (High)`,
`Gemini 3.1 Pro (Low)`, `Gemini 3.1 Pro (High)`, `Claude Sonnet 4.6 (Thinking)`,
`Claude Opus 4.6 (Thinking)`, `GPT-OSS 120B (Medium)`. Pass the exact string to `--model`.

⚠️ agy does **not** validate `--model`: an unknown/misspelled name silently falls back to the default
(no error), and agy never reports which model actually answered. The bridge guards this by validating
`--model` against `agy models` and erroring on an unknown name.

## On-disk layout

```
~/.gemini/antigravity-cli/
├── cache/last_conversations.json           # { "<workspace-abspath>": "<conversation-uuid>" }
├── conversations/<conversation-uuid>.db    # SQLite transcript (tables: steps, gen_metadata, …)
└── …                                       # auth credentials, logs, settings (layout varies by version)
```

The bridge reads `last_conversations.json` keyed by `--cd` (resolved abspath) to recover `SESSION_ID`,
falling back to the newest `*.db` modified since the run began. The `.db` schema is undocumented and
version-volatile, so the bridge does **not** parse it for the answer — it relies on pty-captured stdout.

## Quirks the bridge works around

1. **Conversation ID not surfaced (issue #7).** `agy -p` never prints the conversation ID and there is
   no `--session-id`. The bridge recovers it from `last_conversations.json` after the run.
2. **No structured output.** The bridge captures agy's plain text, strips ANSI/spinner sequences, and
   returns JSON with a wall-clock kill (`--timeout`, default `print-timeout + 120s`) as the real cap.

The bridge runs agy under a pty (`pty.openpty()`): the non-TTY stdout hang (issue #76) is fixed
upstream — a piped `agy -p` now returns normally (verified) — and the pty is kept as cheap insurance
against TTY-dependent regressions.

## Concurrency

`agy` rewrites `last_conversations.json` on every invocation, so two simultaneous runs would race ID
recovery and could attach a resume to the wrong conversation. The bridge serializes runs with an
advisory `flock` on `~/.gemini/antigravity-cli/cache/.agy_bridge.lock`. **Do not run bridge calls
concurrently** for independent threads; run them one at a time.

## Migrating from Gemini CLI workflows

The Gemini CLI (and this repo's former `collaborating-with-gemini` skill, removed 2026-07-06) map to `agy` as follows:

| Gemini bridge | Antigravity bridge |
|---|---|
| `gemini -p ... -o stream-json` | `agy -p` under a pty (no JSON output mode) |
| `--resume <SESSION_ID>` | `--SESSION_ID` → `agy --conversation <id>` |
| `--approval-mode {default,auto_edit,yolo,plan}` | gone → `--sandbox` / `--skip-permissions` |
| `session_id` from stream | recovered from `last_conversations.json` |
| `~/.gemini/tmp/<project>/chats/` | `~/.gemini/antigravity-cli/conversations/<id>.db` |

Sources: Google Developers Blog (Gemini CLI → Antigravity CLI transition), antigravity-cli issues #7 and #76.
