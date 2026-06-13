# Handoff Patterns

How much authority to give Claude, and how to bring its work back.

## Read-only analysis

For diagnosis, architecture opinions, reviews, and research.

```bash
python3 skills/collaborating-with-claude/scripts/claude_bridge.py \
  --cd "/path/to/repo" \
  --permission-mode plan \
  --PROMPT "$PROMPT"
```

Ask for evidence, file paths, line numbers, and a compact recommendation. Verify the cited files before acting.

`plan` also denies `WebFetch`/`WebSearch`. If the analysis needs the web, use the scoped recipe in [cli-reference.md](cli-reference.md) (`dontAsk` + `--tools` + pre-approved `--allowed-tools`) instead of widening the permission mode. Check `tools_failed` / `permission_denials` in the result: a denied tool means Claude answered without the evidence it asked for.

## File-backed handoff

When the prompt is large, generated, or shell-sensitive (backticks, `$VARS`), pass it via a file instead of argv:

```bash
python3 skills/collaborating-with-claude/scripts/claude_bridge.py \
  --cd "/path/to/repo" \
  --permission-mode plan \
  --prompt-file /tmp/claude-handoff.md
```

`--prompt-file` pipes the file to Claude's stdin, bypassing argv and shell-quoting limits (keep it under ~10 MB). For large system context, use `--system-prompt-file` / `--append-system-prompt-file`.

## Read-only patch proposal

When you want implementation help without letting Claude edit:

- Ask for `OUTPUT: Unified Diff Patch ONLY`.
- Include expected behavior and the tests to satisfy.
- Run in `--permission-mode plan` so no writes happen.

Inspect the patch, then apply it yourself with `git apply`.

## Isolated write handoff

Give write access only in an isolated worktree, preferably under `/tmp`. **This is the canonical worktree pattern — other references point here.**

```bash
git worktree add -b claude/<task-name> /tmp/claude-<task-name> HEAD

python3 skills/collaborating-with-claude/scripts/claude_bridge.py \
  --cd "/tmp/claude-<task-name>" \
  --permission-mode acceptEdits \
  --PROMPT "$PROMPT"
```

(`acceptEdits` auto-approves file edits; `auto` adds classifier-gated command approval — see [cli-reference.md](cli-reference.md).) After completion:

```bash
git -C /tmp/claude-<task-name> diff
git -C /tmp/claude-<task-name> status --short
```

Review and port the changes deliberately. Do not merge blind. Claude also offers native `claude --worktree` for interactive sessions — see [parallel.md](parallel.md).

## Parallel read-only runs

Split independent questions into separate sessions: one prompt per concern, separate `SESSION_ID`s, `plan` mode, explicit output contracts. Synthesize by comparing contradictions, shared evidence, and gaps. Details in [parallel.md](parallel.md).

## State capsule

Keep the `[Claude Capsule]` from `SKILL.md` updated after each turn, so compaction or handoff does not lose the thread.
