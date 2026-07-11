# Grok CLI Reference

Verified for this skill against local `grok` (Grok Build TUI) **v0.2.93 stable** on macOS (2026-07-11). The bridge wraps headless mode (`grok -p`); flags below are the ones it forwards. If grok changes its event schema or flags, update `scripts/grok_bridge.py` and this file together.

## Headless command shape

The bridge builds:

```bash
grok -p "<prompt>" --output-format streaming-json --cwd /path/to/repo --permission-mode default [flags]
```

Or, for resume:

```bash
grok -p "<prompt>" --output-format streaming-json --cwd /path/to/repo -r <sessionId> [flags]
```

For explicitly authorized writes, `--always-approve` replaces the default permission flag; the bridge never sends both:

```bash
grok -p "<prompt>" --output-format streaming-json --cwd /isolated/worktree --always-approve [flags]
```

| Bridge flag | grok flag | Notes |
|---|---|---|
| `--PROMPT` | `-p, --single <PROMPT>` | The single-turn prompt. Required (or `--prompt-file`). |
| `--prompt-file <PATH>` | `--prompt-file <PATH>` | Read the whole prompt from a file (native; no stdin piping). Relative paths resolve against `--cd`; absolute paths are unchanged. |
| `--stdin-file <PATH>` | temporary `--prompt-file` | Bridge compatibility name for a context/handoff file combined with `--PROMPT` as escaped, untrusted JSON data in a mode-0600 temporary native prompt file, removed after the run. Grok 0.2.93 ignores stdin when `-p` is present. Relative paths resolve against `--cd`; mutually exclusive with `--prompt-file`. |
| `--cd <DIR>` | `--cwd <PATH>` | Workspace root. The bridge also sets the child process cwd. |
| `--model <ID>` | `-m, --model <MODEL>` | e.g. `grok-4.5` (as of 0.2.93). Discover with `--list-models` — do not hardcode. |
| `--output-format` | `--output-format <FMT>` | `plain` · `json` · `streaming-json` (bridge default). |
| `--SESSION_ID <id>` | `-r, --resume <id>` | Resume an existing session; **errors if it does not exist**. |
| `--session-id <id>` | `-s, --session-id <id>` | Name a **new** session: valid unused UUID only; does not resume — use `-r`/`-c` (grok's `--fork-session` names a fork). |
| `--continue` | `-c, --continue` | Continue the most recent session in `--cwd`. |
| `--permission-mode` | `--permission-mode <MODE>` | Omit for the bridge's gated `default`; pass an explicit empty string to inherit host config. On 0.2.93 the bridge accepts only CLI-enforced `default`/`bypassPermissions` and fails closed for parsed-but-unwired modes. Mutually exclusive with `--always-approve`. |
| `--always-approve` | `--always-approve` | Auto-approve every tool action. Dangerous and mutually exclusive with `--permission-mode`. |
| `--sandbox` | `--sandbox <PROFILE>` | OS-level built-ins: `off`·`workspace`·`devbox`·`read-only`·`strict`; custom names resolve from sandbox.toml and are validated by Grok. |
| `--tools` | `--tools <LIST>` | Allowlist of built-in tools (comma-separated). |
| `--disallowed-tools` | `--disallowed-tools <LIST>` | Denylist; supports `Agent`/`Agent(type)`. |
| `--allow` / `--deny` | `--allow` / `--deny` | Repeatable `ToolPrefix(glob)` permission rules. |
| `--effort` | `--effort <LEVEL>` | Alias of `--reasoning-effort` on current CLI (`none`·`minimal`·`low`·`medium`·`high`·`xhigh`·`max`; model-dependent, `max` aliases `xhigh`). |
| `--reasoning-effort` | `--reasoning-effort <E>` | Reasoning effort for models that support it (e.g. grok-4.5). |
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

`--output-format plain` emits human-readable text only (no emitted `sessionId` or `stopReason`). Bridge `complete` is therefore `null`; `SESSION_ID` may be recovered from session storage for best-effort resume.

**Tool calls are not surfaced in headless mode.** Even when grok reads files or searches the web, the stream contains only `thought`/`text`/`end` — no tool events. (Rich `tool_call`/`plan` updates exist only in ACP mode, `grok agent stdio`, via `session/update` notifications.) The bridge recovers this **after** the run from the session files (`~/.grok/sessions/<quote(resolved-cwd, safe='')>/<session-id>/`): `summary.json` → `model` (`current_model_id`, product id) and `agent` (`agent_name`, template lineage — may still be `grok-build-plan` when `model` is `grok-4.5`); `updates.jsonl` → `tool_counts`/`tools_used`. The bridge tries both `resolve()` and `absolute()` encodings so macOS `/tmp` → `/private/tmp` still matches. Tool failures are still not reported; `updates.jsonl` is the full audit trail.

`sessionId` (and `requestId`) appear only in the terminal `end`/json object. For plain or interrupted runs, the bridge snapshots existing session directories before launch and considers only newly created directories during mtime-based recovery. Explicit `--SESSION_ID`/`--session-id` values are deterministic hints; concurrent unnamed runs in the same cwd remain best-effort.

## Success and completeness signals

- **Exit code is authoritative for process success.** `0` = bridge `success: true`.
- **`complete` is the caller-facing turn signal.** Require `success: true` and `complete: true` before treating a turn as delivered. It is `null` for plain output because completion is unobservable. It does not prove correctness or exact output-contract compliance; validate machine-consumed artifacts separately.
- **`stopReason` supplies structured completion evidence:**
  - `EndTurn` — clean completion.
  - `Cancelled` — either an approval-gated action was skipped (exit `0`), or `--max-turns` truncated the run (exit `1`, with `Error: max turns reached` on stderr). The bridge reports `complete: false`, surfaces `stop_reason`, and warns.
- grok prints real errors to **stderr** as `Error: ...` / `ERROR` lines (ANSI-coloured); the bridge strips ANSI, forwards them as progress, and folds them into the `error` field on failure.

## Safety model

grok has four independent control surfaces; combine them per task.

**`--permission-mode`**: Grok 0.2.93 parses `default` · `plan` · `acceptEdits` · `auto` · `dontAsk` · `bypassPermissions`, but its bundled permission guide says the CLI flag currently enforces only `default` and `bypassPermissions`/always-approve. The bridge therefore fails closed for `plan`, `acceptEdits`, `auto`, and `dontAsk` instead of promising a policy Grok will ignore. Configure supported `defaultMode` values in the applicable `.claude/settings.json`, or use explicit `--allow`/`--deny` rules, when those policies are required.

Under `default`, an edit or non-safe shell action that would prompt is **cancelled** in headless mode (`stopReason: "Cancelled"`, files untouched). Read-class tools, grep, and Grok's curated safe shell commands remain fast-path approved. Use `--tools "read_file,grep,list_dir"` for deterministic read-only analysis.

The bridge emits `--permission-mode default` when neither authority flag is supplied. Pass `--permission-mode ""` only to deliberately inherit host config. `--always-approve` is a separate, mutually exclusive authority choice; verified on 0.2.93 to execute headless tools when passed alone.

**`--tools` / `--disallowed-tools`** (headless only): allowlist or denylist of built-in tool IDs. The allowlist is deterministic (unlisted tools are absent regardless of permission mode).

| Display | Tool ID | | Display | Tool ID |
|---|---|---|---|---|
| bash | `run_terminal_cmd` | | web_search | `web_search` |
| grep | `grep` | | web_fetch | `web_fetch` |
| read_file | `read_file` | | todo_write | `todo_write` |
| search_replace (edit) | `search_replace` | | task (subagent) | `task` |
| list_dir | `list_dir` | | | |

**`--allow` / `--deny`** rules: `ToolPrefix(glob)` — `Bash(...)`, `Edit(...)`, `Write(...)`, `Read(...)`, `Grep(...)`, `WebFetch(...)`, `MCPTool(...)`. Glob `*`/`**`; deny beats allow; repeatable; work in TUI and headless.

**`--sandbox`** (OS-level, Landlock/Seatbelt): `off` (default); `workspace` (read everywhere, write CWD+temp+`~/.grok`); `devbox` (broad writes for disposable VMs); `read-only` (read everywhere, write temp+`~/.grok`); `strict` (read CWD+system paths, write CWD+temp+`~/.grok`). Custom sandbox.toml profiles can add read/write paths and kernel-enforced deny rules. Child-network blocking applies on Linux; it is a no-op on macOS, while Grok's in-process web/LLM access remains available. Profiles are irreversible for a session. `workspace` is Grok's name (`workspace-write` is a Codex term and the bridge rejects it with a targeted hint).

`workspace` is not a hard read boundary. Grok may read other paths and may discover instructions/configuration from an ancestor Git repository before tool execution. The bridge warns when `--cd` is nested below a Git root. Use a standalone directory plus `strict`, a container, or another external boundary when read isolation matters. Prompt wording states intended scope; it does not enforce filesystem access.

Profiles do not block the agent's in-process LLM/web calls. Child-process network blocking applies only on Linux; on macOS it is currently a no-op.

`~/.ssh`, `~/.aws`, `~/.gnupg`, `~/.grok/auth` are always write-protected.

## Web & X search

The **GrokBuild-lineage coding model** supports live web + X search via `web_search` (`supports_backend_search: true` in `~/.grok/models_cache.json`). As of CLI **0.2.93** that product id is **`grok-4.5`** (agent template may still report `grok-build-plan`). The old product id `grok-build` is **gone** — passing it fails with `unknown model id`.

- **Pass an explicit coding `--model` for search.** Host `~/.grok/config.toml` `[models] default` may select composer. Under composer (`grok-composer-2.5-fast`, `agent_name: cursor`) tool names differ (`WebSearch`/`WebFetch`/`Grep`) and research loops can take minutes in the event-free headless stream.
- **Working recipe:** keep the default toolset and remove write/shell with a **denylist**: `--disallowed-tools "run_terminal_cmd,search_replace"` (plus `--model grok-4.5` or whatever `--list-models` marks as the coding default).
- **X (Twitter) search → coding / backend-search model.** Prefer `supports_backend_search: true`. Composer reports `supports_backend_search: false` but may still surface X via its own web tools — best-effort only.
- **Terminal/web allowlists fail on the coding agent — still true on 0.2.93.** A `--tools` allowlist containing `run_terminal_cmd`, `web_search`, or `web_fetch` fails session build with `RequirementError { tool: "GrokBuild:run_terminal_cmd", message: "auto_background_on_timeout requires enabled_background to be true", … }`. Re-probed with `run_terminal_cmd` and `read_file,web_search` on 2026-07-11. A read-only allowlist such as `read_file,grep,list_dir` works; otherwise keep the default toolset and remove unwanted tools with `--disallowed-tools`.
- `web_fetch` is **disabled unless `GROK_WEB_FETCH=1`**; `web_search` needs no env var. The web-search model is configurable via `[models] web_search` / `GROK_WEB_SEARCH_MODEL`.

## Models

`grok models` (parsed by `--list-models`) is plain text:

```
Default model: <effective default>

Available models:
  * <effective default> (default)
  - …
```

**As of 0.2.93:** `grok-4.5` is the coding default (~500k context, backend search, reasoning effort supported); `grok-composer-2.5-fast` is the Cursor-agent alternate (~200k). Probe live — do not hardcode the catalog across CLI upgrades. The reported default is the **effective** one when config and CLI agree; always check the result's `model` field after a run. Under a network-restricted sandbox the list may fall back to `~/.grok/models_cache.json` and show fewer models.

Other headless flags exist on the CLI (`--best-of-n`, `--check`, `--json-schema`, `--prompt-json`, …) but are not forwarded by the bridge unless added deliberately.

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
