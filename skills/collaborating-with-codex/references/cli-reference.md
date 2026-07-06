# Codex CLI Reference

Verified for this skill against local `codex-cli 0.142.5` (2026-07-06).

## Commands

| Command | Use |
|---|---|
| `codex exec` | Non-interactive execution used by the bridge |
| `codex exec resume` | Continue a saved exec session |
| `codex exec review` | Built-in non-interactive code review |
| `codex review` | Top-level review alias |
| `codex apply <TASK_ID>` | Apply the latest diff produced by a Codex agent |
| `codex fork [SESSION_ID]` | Fork an interactive session |
| `codex mcp list/add/remove` | Manage Codex MCP servers |
| `codex features list` | Inspect feature flags |
| `codex sandbox -- <cmd>` | Run a command under the Codex sandbox; `codex sandbox -- true` probes sandbox health |
| `codex doctor` | Diagnose install, auth, config, and sandbox status |
| `codex debug models` | Render the model catalog (slugs and reasoning levels) as JSON |

## `codex exec`

Use this shape for bridge calls:

```bash
codex exec --json -C /path/to/repo -s read-only -- "Prompt text"
```

For live web search or explicit approval policy, place the global flags before `exec`:

```bash
codex --search -a never exec --json -C /path/to/repo -s read-only -- "Prompt text"
```

Supported options used by the bridge:

| Flag | Use |
|---|---|
| `--json` | Emit JSONL events to stdout |
| `-C`, `--cd <DIR>` | Set the working root |
| `-s`, `--sandbox <MODE>` | `read-only`, `workspace-write`, or `danger-full-access` |
| `--search` | Top-level flag before `exec`; enables live web search |
| `-a`, `--ask-for-approval <POLICY>` | Top-level flag before `exec`; `untrusted`, `on-request`, `never`, or deprecated `on-failure` |
| `--add-dir <DIR>` | Add writable directories |
| `-m`, `--model <MODEL>` | Override model |
| `-p`, `--profile <PROFILE>` | Load a Codex config profile |
| `--oss` | Use open-source provider mode |
| `--local-provider <PROVIDER>` | Select `lmstudio` or `ollama` for OSS mode |
| `-c`, `--config <key=value>` | Override config values |
| `--enable <FEATURE>` | Enable a feature flag |
| `--disable <FEATURE>` | Disable a feature flag |
| `-i`, `--image <FILE>` | Attach image files |
| `--skip-git-repo-check` | Allow running outside a Git repo |
| `--ephemeral` | Do not persist session files |
| `--ignore-user-config` | Do not load `$CODEX_HOME/config.toml` |
| `--ignore-rules` | Do not load execpolicy `.rules` files |
| `--strict-config` | Error on unrecognized config fields |
| `--dangerously-bypass-approvals-and-sandbox` | Skip approvals and sandboxing; dangerous |
| `--dangerously-bypass-hook-trust` | Run hooks without persisted hook trust; dangerous |
| `-o`, `--output-last-message <FILE>` | Write final agent message to a file; direct CLI only |
| `--output-schema <FILE>` | Enforce JSON Schema response shape; direct CLI only |
| `--color <MODE>` | `always`, `never`, or `auto` |

`--full-auto` is deprecated by Codex and should not be used in new bridge calls. The bridge keeps `--full-auto` only as a compatibility alias for `--sandbox workspace-write`. `--search` and `--ask-for-approval` are top-level Codex flags; the bridge forwards them before `exec`.

Use `--search` only when live web evidence is needed. Treat remote content as untrusted and keep secrets out of prompts.

## Sandbox, network, and approvals

Sandbox network defaults (verified against current developer docs):

- Shell network is off by default in `read-only` and `workspace-write`. Enable it for workspace-write with `-c sandbox_workspace_write.network_access=true` (the bridge's `--network` flag).
- Workspace-write writable roots: the `-C` root, `/tmp`, `$TMPDIR`, and `--add-dir` values. Tune with `sandbox_workspace_write.writable_roots`, `.exclude_slash_tmp`, and `.exclude_tmpdir_env_var`.
- Web search is a separate path: config `web_search = "disabled" | "cached" | "live"` defaults to `cached` (OpenAI-maintained index, no live fetches). Top-level `--search` enables the live `web_search` tool with no per-call approval.

`codex exec` cannot prompt: under `untrusted` or `on-request`, an action that would require approval fails and the failure goes back to the model. Use `-a never` (or omit) for bridge calls and grant authority only via sandbox mode, `--add-dir`, `--network`, and `--search`.

Sandbox health: `codex sandbox -- true` should exit 0. On hosts that cannot enforce the sandbox (containers, PRoot, older WSL), every sandboxed command exits 182 (and `--enable use_legacy_landlock` panics with exit 101); read-only and workspace-write delegation silently produce no usable work. The bridge appends a warning when all commands fail and one exits 182.

## `codex exec resume`

Use this shape for resumed sessions:

```bash
codex exec --json -C /path/to/repo -s read-only resume <SESSION_ID> -- "Follow-up prompt"
codex exec --json -C /path/to/repo -s read-only resume --last -- "Follow-up prompt"
codex exec --json -C /path/to/repo -s read-only resume --all <SESSION_ID> -- "Follow-up prompt"
```

Keep the `SESSION_ID` in the collaboration capsule so later turns can continue the same Codex thread.

## `codex exec review`

Use this command directly for built-in code reviews:

```bash
codex exec review --uncommitted -o /tmp/codex-review.md
codex exec review --base origin/main -o /tmp/codex-review.md
codex exec review --commit <sha> -o /tmp/codex-review.md
```

Useful review flags:

| Flag | Use |
|---|---|
| `--uncommitted` | Review staged, unstaged, and untracked changes |
| `--base <BRANCH>` | Review changes against a base branch |
| `--commit <SHA>` | Review a specific commit |
| `--title <TITLE>` | Add a review title |
| `-o <FILE>` | Write final review text |
| `--json` | Emit JSONL events |

Current `codex exec review` does not use `--full-auto`.

## `codex apply`

Use only after reviewing a Codex-produced diff:

```bash
codex apply <TASK_ID>
```

It applies the latest diff from the specified task as `git apply` to the local working tree.

## `codex fork`

Use for interactive session branching:

```bash
codex fork <SESSION_ID> "Explore an alternate approach"
codex fork --last "Try a smaller variant"
```

`codex fork` is not the same as `codex exec resume`; it branches a saved interactive session rather than continuing the bridge's normal JSON handoff.

## JSONL events

The bridge relies on these event shapes:

```jsonl
{"type":"thread.started","thread_id":"019..."}
{"type":"turn.started"}
{"type":"item.completed","item":{"type":"agent_message","text":"..."}}
{"type":"item.completed","item":{"type":"command_execution","command":"...","exit_code":0,"status":"completed"}}
{"type":"item.completed","item":{"type":"file_change","status":"completed","changes":[{"path":"...","kind":"update"}]}}
{"type":"turn.completed","usage":{"input_tokens":123,"output_tokens":45}}
```

Item types include agent messages, reasoning, command executions, file changes, MCP tool calls, web searches, and todo/plan updates. `command_execution`, `file_change`, and `mcp_tool_call` items carry a `status` field (`completed`, `failed`, or `declined` for commands); `file_change` is emitted once per patch whether it succeeded or failed. The bridge returns `activity_counts` plus compact counters for commands (`commands_ran`, `commands_failed`), web searches, MCP activity, file activity (`files_changed`, `files_failed`), and todo/plan updates when those events appear.

If Codex changes event names, update `scripts/codex_bridge.py` and this reference together.

## Config and feature examples

```bash
-m gpt-5.4-mini
-c 'model_reasoning_effort="medium"'
-c 'model_reasoning_effort="xhigh"'
-c 'sandbox_workspace_write.network_access=true'
-c 'sandbox_permissions=["disk-full-read-access"]'
--enable multi_agent
--disable fast_mode
```

`codex debug models` lists current model slugs and reasoning levels (`low`, `medium`, `high`, `xhigh`); at the time of verification: `gpt-5.5` (default, medium), `gpt-5.4`, `gpt-5.4-mini`, and `gpt-5.3-codex-spark` (default high).

Stable and enabled per local `codex features list`: `multi_agent`, `fast_mode`, `guardian_approval`, `hooks`, `image_generation` (gpt-image-2, `$imagegen`), `browser_use`, and `computer_use`. Removed flags such as `steer`, `request_rule`, `remote_models`, `search_tool`, and `js_repl` should not be used.
