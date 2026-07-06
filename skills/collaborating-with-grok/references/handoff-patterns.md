# Grok Handoff Patterns

Use these to decide how much authority to give grok and how to bring its work back into the primary session.

## Read-only analysis

For diagnosis, architecture opinions, reviews, and code research.

```bash
python3 skills/collaborating-with-grok/scripts/grok_bridge.py \
  --cd "/path/to/repo" \
  --tools "read_file,grep,list_dir" \
  --PROMPT "$PROMPT"
```

Ask grok for evidence, file paths, line numbers, and a compact recommendation. The primary agent verifies the cited files before acting. Tool calls aren't visible in headless output — trust the answer only after checking the files it claims to have read.

## Live web / X research

When the task needs current facts, releases, or X posts.

```bash
python3 skills/collaborating-with-grok/scripts/grok_bridge.py \
  --cd "/path/to/repo" \
  --disallowed-tools "run_terminal_cmd,search_replace" \
  --PROMPT "$PROMPT"
```

Keeps `web_search`/`web_fetch`, removes shell and edit. Set `GROK_WEB_FETCH=1` in the environment if grok needs to fetch specific URLs. Web search adds latency; run in the background.

## File-backed handoff

When a generated plan, review packet, or issue bundle is too large or too shell-sensitive for argv, write it to a file. Two shapes:

**Whole prompt in the file** — the file *is* the instruction:

```bash
python3 skills/collaborating-with-grok/scripts/grok_bridge.py \
  --cd "/path/to/repo" \
  --tools "read_file,grep,list_dir" \
  --prompt-file /tmp/grok-handoff.md
```

**Context file + a short instruction** — author the context/plan once, then steer it with text. The file is piped to grok as context; `--PROMPT` carries the ask (verified: grok folds piped stdin into the prompt):

```bash
python3 skills/collaborating-with-grok/scripts/grok_bridge.py \
  --cd "/path/to/repo" \
  --tools "read_file,grep,list_dir" \
  --stdin-file /tmp/grok-context.md \
  --PROMPT "Using the piped context, produce a prioritized review. Cite file:line."
```

Keep the handoff itself elegant and self-consistent — point at repo paths instead of pasting code, state the output contract, and name what is out of scope.

## Read-only patch proposal

When you want implementation help but don't want grok to edit files.

- Run with `--tools "read_file,grep,list_dir"` (no edit tool present).
- Ask for `OUTPUT: Unified Diff Patch ONLY`.
- Include the expected behavior and tests to satisfy.

After grok returns a patch, inspect it before applying with `git apply`.

## Isolated write handoff

Grant write access only in an isolated worktree, preferably under `/tmp`. Because grok's config may be `always-approve`, be explicit about the directory.

```bash
git worktree add -b grok/<task-name> /tmp/grok-<task-name> HEAD

python3 skills/collaborating-with-grok/scripts/grok_bridge.py \
  --cd "/tmp/grok-<task-name>" \
  --always-approve \
  --PROMPT "Implement the focused fix in <file>. Keep changes scoped. Then summarize what changed."
```

`--always-approve` lets grok edit and run shell. Alternatives: `--permission-mode acceptEdits` (edits only) or scoped rules like `--allow "Edit(src/**)" --deny "Bash(rm*)"`. After completion:

```bash
git -C /tmp/grok-<task-name> diff
git -C /tmp/grok-<task-name> status --short
```

Review and port deliberately. Do not merge blind.

## State capsule

Keep this compact state in the primary conversation and update it after each grok turn so compaction or handoff does not lose the thread:

```text
[Grok Capsule] Goal: | SID: | Model: | PermMode: | Files: | Last: | Next:
```
