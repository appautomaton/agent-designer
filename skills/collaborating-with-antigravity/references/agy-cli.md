# Antigravity CLI (`agy`) reference

**Verification status:** built and tested against `agy` v1.0.8 on Linux (2026-06-16). The interface is
changing fast; re-check `agy --help` / `agy models` if behavior drifts.

## Install & auth

```bash
curl -fsSL https://antigravity.google/cli/install.sh | bash   # installs `agy` to ~/.local/bin
agy --version                                                  # non-interactive version check
```

Auth is **Google OAuth, no API key**. On first run `agy` opens a browser (or, over SSH, prints a URL +
one-time code) and caches a token at `~/.gemini/antigravity-cli/antigravity-oauth-token`. The bridge
warns if that token is missing.

## Verified flag surface (v1.0.8 `agy --help`)

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
```

Subcommands: `changelog`, `help`, `install`, `models`, `plugin`/`plugins`, `update`.

**Notably absent** (do not assume parity with Gemini CLI):
- No `--output-format` / `--json` → no structured output; the bridge captures and cleans text.
- No `--session-id` / supplied-UUID resume → only `--conversation <id>` (known id) and `-c` (most recent).
- No `--no-color` → the bridge strips ANSI/spinner sequences itself.

## Models (`agy models`)

`Gemini 3.5 Flash (Low)`, `Gemini 3.5 Flash (Medium)`, `Gemini 3.5 Flash (High)`,
`Gemini 3.1 Pro (Low)`, `Gemini 3.1 Pro (High)`, `Claude Sonnet 4.6 (Thinking)`,
`Claude Opus 4.6 (Thinking)`, `GPT-OSS 120B (Medium)`. Pass the exact string to `--model`.

## On-disk layout

```
~/.gemini/antigravity-cli/
├── antigravity-oauth-token                 # auth
├── cache/last_conversations.json           # { "<workspace-abspath>": "<conversation-uuid>" }
└── conversations/<conversation-uuid>.db    # SQLite transcript (tables: steps, gen_metadata, …)
```

The bridge reads `last_conversations.json` keyed by `--cd` (resolved abspath) to recover `SESSION_ID`,
falling back to the newest `*.db` modified since the run began. The `.db` schema is undocumented and
version-volatile, so the bridge does **not** parse it for the answer — it relies on pty-captured stdout.

## Known bugs the bridge works around

1. **Non-TTY stdout hang (issue #76).** `agy -p` writes nothing and hangs indefinitely when stdout is
   not a terminal (pipe/redirect/subprocess); `--print-timeout` is ignored. The bridge allocates a pty
   (`pty.openpty()`), passes the slave as agy's stdout/stderr, reads the master, and enforces a
   wall-clock kill (`--timeout`, default `print-timeout + 120s`). Confirmed locally: a piped run hung
   >11 min with 0 bytes; the same prompt under a pty returned in ~3s.
2. **Conversation ID not surfaced (issue #7).** `agy -p` never prints the conversation ID and there is
   no `--session-id`. The bridge recovers it from `last_conversations.json` after the run.

## Concurrency

`agy` rewrites `last_conversations.json` on every invocation, so two simultaneous runs would race ID
recovery and could attach a resume to the wrong conversation. The bridge serializes runs with an
advisory `flock` on `~/.gemini/antigravity-cli/cache/.agy_bridge.lock`. **Do not run bridge calls
concurrently** for independent threads; run them one at a time.

## Migrating from `collaborating-with-gemini`

| Gemini bridge | Antigravity bridge |
|---|---|
| `gemini -p ... -o stream-json` | `agy -p` under a pty (no JSON output mode) |
| `--resume <SESSION_ID>` | `--SESSION_ID` → `agy --conversation <id>` |
| `--approval-mode {default,auto_edit,yolo,plan}` | gone → `--sandbox` / `--skip-permissions` |
| `session_id` from stream | recovered from `last_conversations.json` |
| `~/.gemini/tmp/<project>/chats/` | `~/.gemini/antigravity-cli/conversations/<id>.db` |

Sources: Google Developers Blog (Gemini CLI → Antigravity CLI transition), antigravity-cli issues #7 and #76.
