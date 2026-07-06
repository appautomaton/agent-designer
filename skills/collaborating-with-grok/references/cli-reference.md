# Grok CLI Reference

Verified for this skill against local `grok` (Grok Build TUI) **v0.2.87** on macOS (2026-07-06). The bridge wraps headless mode (`grok -p`); flags below are the ones it forwards. If grok changes its event schema or flags, update `scripts/grok_bridge.py` and this file together.

## Headless command shape

The bridge builds:

```bash
grok -p "<prompt>" --output-format streaming-json --cwd /path/to/repo --permission-mode default [flags]
```

Or, for resume:

```bash
grok -p "<prompt>" --output-format streaming-json --cwd /path/to/repo -r <sessionId> [flags]
```

| Bridge flag | grok flag | Notes |
|---|---|---|
| `--PROMPT` | `-p, --single <PROMPT>` | The single-turn prompt. Required (or `--prompt-file`). |
| `--prompt-file <PATH>` | `--prompt-file <PATH>` | Read the whole prompt from a file (native; no stdin piping). |
| `--stdin-file <PATH>` | piped to stdin | Context/handoff file piped to grok's stdin alongside `--PROMPT`; grok folds stdin into the prompt as context. Mutually exclusive with `--prompt-file`. |
| `--cd <DIR>` | `--cwd <PATH>` | Workspace root. The bridge also sets the child process cwd. |
| `--model <ID>` | `-m, --model <MODEL>` | e.g. `grok-build`. Discover with `--list-models`. |
| `--output-format` | `--output-format <FMT>` | `plain` · `json` · `streaming-json` (bridge default). |
| `--SESSION_ID <id>` | `-r, --resume <id>` | Resume an existing session; **errors if it does not exist**. |
| `--session-id <id>` | `-s, --session-id <id>` | Name a **new** session: valid unused UUID only; does not resume — use `-r`/`-c` (grok's `--fork-session` names a fork). |
| `--continue` | `-c, --continue` | Continue the most recent session in `--cwd`. |
| `--permission-mode` | `--permission-mode <MODE>` | Default `default`. See Safety. |
| `--always-approve` | `--always-approve` | Auto-approve every tool action. Dangerous. |
| `--sandbox` | `--sandbox <PROFILE>` | OS-level: `off`·`workspace`·`read-only`·`strict`. |
| `--tools` | `--tools <LIST>` | Allowlist of built-in tools (comma-separated). |
| `--disallowed-tools` | `--disallowed-tools <LIST>` | Denylist; supports `Agent`/`Agent(type)`. |
| `--allow` / `--deny` | `--allow` / `--deny` | Repeatable `ToolPrefix(glob)` permission rules. |
| `--effort` | `--effort <LEVEL>` | `low`·`medium`·`high`·`xhigh`·`max` (model-dependent). |
| `--reasoning-effort` | `--reasoning-effort <E>` | Reasoning effort for reasoning models. |
| `--max-turns` | `--max-turns <N>` | Cap agentic turns. Hitting it exits non-zero (see below). |
| `--rules` | `--rules <TEXT>` | Extra rules appended to the system prompt. |
| `--disable-web-search` | `--disable-web-search` | Remove `web_search`/`web_fetch`. |
| `--no-plan` | `--no-plan` | Disable plan mode. |

Bridge-only flags: `--list-models` (parses `grok models` to JSON), `--timeout <s>` (wall-clock kill), `--return-all-messages` (include reasoning + raw events).

## Output formats and event schema

`--output-format streaming-json` emits newline-delimited JSON. Verified event types in headless mode:

```jsonl
{"type":"thought","data":"..."}                                          reasoning tokens
{"type":"text","data":"..."}                                             answer tokens
{"type":"end","stopReason":"EndTurn","sessionId":"019...","requestId":"..."}
```

`--output-format json` emits one object:

```json
{ "text": "...", "stopReason": "EndTurn", "sessionId": "019...", "requestId": "...", "thought": "..." }
```

`--output-format plain` emits human-readable text only (no `sessionId` — multi-turn resume unavailable).

**Tool calls are not surfaced in headless mode.** Even when grok reads files or searches the web, the stream contains only `thought`/`text`/`end` — no tool events. (Rich `tool_call`/`plan` updates exist only in ACP mode, `grok agent stdio`, via `session/update` notifications.) The bridge recovers this **after** the run from the session files (`~/.grok/sessions/<quote(cwd, safe='')>/<session-id>/`): `summary.json` → `model` (`current_model_id`, what actually answered) and `agent`; `updates.jsonl` → `tool_counts`/`tools_used` (count of `sessionUpdate: "tool_call"` entries). Tool failures are still not reported; `updates.jsonl` is the full audit trail.

`sessionId` (and `requestId`) appear only in the terminal `end`/json object — so the bridge captures `SESSION_ID` at the very end of a run. If the run is killed first (bridge `--timeout`), the bridge recovers `SESSION_ID` from the session directory this run created (its name is the session id, matched by mtime) and warns that the id was recovered — a timed-out research loop remains resumable with `-r`.

## Success and completeness signals

- **Exit code is authoritative.** `0` = the bridge reports `success: true`.
- **`stopReason` signals completeness**, not success:
  - `EndTurn` — clean completion.
  - `Cancelled` — either an approval-gated action was skipped (exit `0`), or `--max-turns` truncated the run (exit `1`, with `Error: max turns reached` on stderr). The bridge surfaces `stop_reason` and warns when it is not `EndTurn`.
- grok prints real errors to **stderr** as `Error: ...` / `ERROR` lines (ANSI-coloured); the bridge strips ANSI, forwards them as progress, and folds them into the `error` field on failure.

## Safety model

grok has four independent control surfaces; combine them per task.

**`--permission-mode`** (Claude-Code-style): `default` · `plan` · `acceptEdits` · `auto` · `dontAsk` · `bypassPermissions`.
In headless mode an action that *would* prompt is **cancelled** (never hangs): under `default`, an edit/shell action is skipped with `stopReason: "Cancelled"`, files untouched.
**Footgun:** if no `--permission-mode` is passed, grok inherits `~/.grok/config.toml`, which may be `permission_mode = "always-approve"` — that auto-approves writes. The bridge defaults to `--permission-mode default` to prevent this; pass `--permission-mode ""` only to deliberately inherit the config.

**`--tools` / `--disallowed-tools`** (headless only): allowlist or denylist of built-in tool IDs. The allowlist is deterministic (unlisted tools are absent regardless of permission mode).

| Display | Tool ID | | Display | Tool ID |
|---|---|---|---|---|
| bash | `run_terminal_cmd` | | web_search | `web_search` |
| grep | `grep` | | web_fetch | `web_fetch` |
| read_file | `read_file` | | todo_write | `todo_write` |
| search_replace (edit) | `search_replace` | | task (subagent) | `task` |
| list_dir | `list_dir` | | | |

**`--allow` / `--deny`** rules: `ToolPrefix(glob)` — `Bash(...)`, `Edit(...)`, `Write(...)`, `Read(...)`, `Grep(...)`, `WebFetch(...)`, `MCPTool(...)`. Glob `*`/`**`; deny beats allow; repeatable; work in TUI and headless.

**`--sandbox`** (OS-level, Landlock/Seatbelt): `off` (default), `workspace` (write CWD+`/tmp`+`~/.grok`), `read-only` (no writes outside `~/.grok`, child network blocked), `strict` (CWD only, no child network). Irreversible once applied; the model can't relax it. Note: process-level network for the agent's own LLM/web calls can't be blocked — only child-process (bash) network is.

`~/.ssh`, `~/.aws`, `~/.gnupg`, `~/.grok/auth` are always write-protected.

## Web & X search

grok-build supports **live web + X search** via the `web_search` tool (`supports_backend_search: true`).

- **Pass `--model grok-build` explicitly.** `~/.grok/config.toml` `[models] default` silently overrides the factory default; under composer the run uses the Cursor agent (`agent_name: cursor`) with different tool names (`WebSearch`/`WebFetch`/`Grep`) and multi-minute research loops that look like hangs in the event-free headless stream. Verified: grok-build answered a search prompt with cited `x.ai` URLs in ~36s; composer took >240s on the same prompt while making successful WebSearch/WebFetch calls throughout.
- **Working recipe:** keep the default toolset and remove write/shell with a **denylist**: `--disallowed-tools "run_terminal_cmd,search_replace"`.
- **X (Twitter) search → grok-build.** Only grok-build has xAI's native backend Live Search (`supports_backend_search: true` in `~/.grok/models_cache.json`); it issues explicit X queries (`from:<handle>`, `mode:Latest`) and has returned live @xai posts with exact `x.com/.../status/...` URLs **even with `--disable-web-search`** (i.e. independent of the `web_search` tool). `grok-composer-2.5-fast` has `supports_backend_search: false` yet can still surface X posts via its own web tools — treat composer's X access as best-effort.
- **Allowlists break grok-build search:** a `--tools` allowlist that includes `web_search` fails at session build with `RequirementError { tool: "GrokBuild:run_terminal_cmd", … }`. The bridge warns when it sees `web_search`/`web_fetch` in a `--tools` allowlist. Use the denylist form.
- `web_fetch` (fetch a named URL → markdown) is **disabled unless `GROK_WEB_FETCH=1`**; `web_search` needs no env var. The web-search model is configurable via `[models] web_search` / `GROK_WEB_SEARCH_MODEL`.

## Models

`grok models` (parsed by `--list-models`) is plain text:

```
Default model: <effective default>

Available models:
  * <effective default> (default)
  - …
```

`grok-build` is xAI's coding model (512k context) and the factory default; `grok-composer-2.5-fast` is a faster alternative (200k context, Cursor agent). The reported default is the **effective** one — `~/.grok/config.toml` `[models] default` overrides the factory setting — so check `--list-models`' `default` field and pass `--model grok-build` explicitly when the recipes assume it. The model list is fetched live; under a network-restricted sandbox the fetch falls back to the local `~/.grok/models_cache.json` and may show fewer models.

## Auth, sessions, file locations

- Auth: `grok login` (browser, token in `~/.grok/auth.json`, expires after 7 days) or `XAI_API_KEY`. The bridge preflight warns if neither is present.
- Sessions: `~/.grok/sessions/<encoded-cwd>/<session-id>/` with `summary.json`, `updates.jsonl` (authoritative conversation + tool calls), `chat_history.jsonl`, `plan.json`. Resume needs the same `--cwd`.
- Config: `~/.grok/config.toml` (global), `.grok/config.toml` (project). grok also reads Claude Code config: `.claude/skills`, `CLAUDE.md`, `~/.claude.json` / `.mcp.json` for MCP servers.

## Direct CLI subcommands (outside the bridge)

| Command | Use |
|---|---|
| `grok models` | List models. |
| `grok sessions list` / `grok sessions delete <id>` | Manage saved sessions. |
| `grok export <id>` | Export a session transcript as Markdown. |
| `grok inspect [--json]` | Show config/skills/agents/MCP discovered for the cwd. |
| `grok agent stdio` | ACP (JSON-RPC) mode — rich tool/plan/permission events. |
| `grok worktree` / `-w, --worktree` | Manage / start in a git worktree. |
