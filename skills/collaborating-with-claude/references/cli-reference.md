# Claude Code CLI Reference

Verified against `claude` (Claude Code) CLI **v2.1.176**. The bridge wraps `claude --print` (headless mode).

## Invocation shape

Claude runs headlessly from the workspace directory (it uses the process cwd; there is no `--cd` flag — the bridge sets cwd for you):

```bash
cd /path/to/repo && claude --print "<prompt>" --output-format stream-json --verbose
```

The prompt is the positional argument, or piped via stdin when the bridge's `--prompt-file` is used.

## Core flags (headless)

| Flag | Purpose |
|---|---|
| `-p`, `--print` | Non-interactive mode (required for everything below) |
| `--output-format` | `text` · `json` (single result object) · `stream-json` (NDJSON events; needs `--verbose`) |
| `--input-format` | `text` (default) · `stream-json` |
| `--include-partial-messages` | Token-level deltas (stream-json only) |
| `--model` | Alias (`haiku`, `sonnet`, `opus`, `fable`) or full id (`claude-opus-4-8`) |
| `--fallback-model` | Comma-separated fallbacks when the primary is overloaded |
| `--effort` | `low` · `medium` · `high` · `xhigh` · `max` (model-dependent) |
| `--max-budget-usd` | Hard USD cap; stops with `subtype: error_max_budget_usd` |
| `--max-turns` | Cap agentic turns; stops with `subtype: error_max_turns` |
| `--json-schema` | Structured-output schema (see caveat below) |

## Permission & tools (single source of truth)

| `--permission-mode` | Behavior |
|---|---|
| `plan` | Read/analyze only; no edits, commands, or network tools (`WebFetch`/`WebSearch` are denied too — verified). |
| `dontAsk` | Denies anything not in `permissions.allow` rules / `--allowedTools`. |
| `default` | Headless (`-p`) cannot prompt: each gated action is denied and recorded in `permission_denials`. |
| `acceptEdits` | Auto-approves file edits. |
| `auto` | Classifier-gated auto-approval; aborts under `-p` if it keeps blocking. |
| `bypassPermissions` | Bypass all checks. Sandboxed/trusted dirs only. (`--dangerously-skip-permissions` is the equivalent raw CLI flag.) |

Headless gating extends to reads: paths outside `--cd` / `--add-dir` are permission-gated and denied under `-p` (verified). Denials also surface as `tool_result` errors, so the bridge's `tools_failed` counts them.

Tool scoping:
- `--tools "Read,Glob,Grep"` — restrict which built-ins exist at all (`""` = none, `"default"` = all).
- `--allowedTools` / `--disallowedTools` — approve/deny by name or rule. **Footgun:** the space in `Bash(git diff *)` is load-bearing — `Bash(git diff*)` would also match `git diff-index`.

Safe read-only review: `--permission-mode plan`, or `--tools "Read,Glob,Grep" --permission-mode dontAsk`.

Network is tool policy, not an OS sandbox: an allowed `Bash` reaches the network freely, and `plan` blocks `WebFetch`/`WebSearch`. For read-only work that needs targeted web access (verified recipe):

```bash
--permission-mode dontAsk --tools "Read,Glob,Grep,WebFetch,WebSearch" \
  --allowedTools "WebFetch(domain:example.com)" --allowedTools "WebSearch"
```

## Reproducibility & context

| Flag | Purpose |
|---|---|
| `--bare` | Skip hooks/skills/plugins/MCP/CLAUDE.md/keychain. Reproducible; **auth must be `ANTHROPIC_API_KEY` or apiKeyHelper** (OAuth/keychain are not read). Slated to become the `-p` default. |
| `--safe-mode` | Disable customizations but keep normal auth/model/permissions (troubleshooting). |
| `--add-dir` | Grant access to extra directories (e.g. CLAUDE.md dirs under `--bare`). |
| `--system-prompt[-file]` | Replace the system prompt (string or file). |
| `--append-system-prompt[-file]` | Append to the system prompt (string or file). |
| `--mcp-config` / `--strict-mcp-config` | Load / restrict MCP servers. |
| `--settings` / `--setting-sources` | Load settings; choose sources (`user`/`project`/`local`). |
| `--agents` / `--agent` | Define / select custom subagents. |

## Sessions

| Flag | Semantics |
|---|---|
| `--resume <id>` | Resume a specific session (bridge `--SESSION_ID`). Requires the same cwd. |
| `--continue` | Resume the most recent session in the cwd. |
| `--session-id <uuid>` | Assign a pre-chosen session UUID. |
| `--fork-session` | With resume/continue, branch to a new session id. |
| `--no-session-persistence` | Don't write the transcript (cannot resume later). |

Transcripts live under `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`; resume needs a matching cwd.

There is **no** local `review` / `apply` / `fork` subcommand (unlike Codex). Use `--fork-session` to branch, pass diffs in the prompt for review, and `git apply` to apply patches. `claude ultrareview` exists but is a cloud-hosted multi-agent review of the current branch/PR, not a local headless run. Native `claude --worktree <name>` creates a session worktree (verify it composes with `--print` before scripting).

## stream-json event schema

With `--output-format stream-json --verbose`, each stdout line is one JSON event:

```jsonc
// session metadata — carries session_id, model, tools, mcp_servers
{"type":"system","subtype":"init","session_id":"…","model":"claude-sonnet-4-6"}
// assistant turn — text + tool_use blocks in message.content[]
{"type":"assistant","message":{"content":[{"type":"text","text":"…"},
  {"type":"tool_use","name":"Read"}]},"session_id":"…"}
// tool results fed back — is_error:true marks failures and permission denials
{"type":"user","message":{"content":[{"type":"tool_result","is_error":true,"content":"…"}]}}
// rate-limit signal
{"type":"rate_limit_event","rate_limit_info":{"status":"allowed"}}
// final, authoritative termination event
{"type":"result","subtype":"success","is_error":false,"result":"…final text…",
  "session_id":"…","total_cost_usd":0.04,"num_turns":2,
  "usage":{"input_tokens":3,"output_tokens":293,"cache_read_input_tokens":40868},
  "modelUsage":{"claude-sonnet-4-6":{"costUSD":0.04}},"permission_denials":[]}
```

`result.subtype` ∈ `success | error_max_turns | error_max_budget_usd | error_during_execution | error_max_structured_output_retries`. The final text (`result.result`) is present only on `success`; a model/auth failure can emit `subtype:"success"` **with `is_error:true`** — always check `is_error`. `--output-format json` emits just this final `result` object.

From these events the bridge derives `tools_used`, per-tool `tool_counts`, and `tools_failed` (count of `tool_result` blocks with `is_error:true` — includes permission denials and ordinary tool errors).

Other system sub-events: `hook_started` / `hook_response` (non-`--bare` only), `api_retry`, `compact_boundary`.

## Caveats

- **`--json-schema`** validates output *after* generation (not constrained decoding) — malformed output is possible; validate independently.
- **stdin** (used by `--prompt-file`) is capped at ~10 MB.
- Background Bash tasks Claude spawns under `-p` are terminated ~5 s after the final result.
- `claude --help` does not list every flag; absence from `--help` does not mean unavailable (`--max-turns`, `--system-prompt-file` are real and verified).
