# Codex Handoff Patterns

Use these patterns to decide how much authority to give Codex and how to bring its work back into the primary session.

## Read-only analysis

Use for diagnosis, architecture opinions, reviews, and research.

```bash
python3 skills/collaborating-with-codex/scripts/codex_bridge.py \
  --cd "/path/to/repo" \
  --sandbox read-only \
  --PROMPT "$PROMPT"
```

Ask Codex for evidence, file paths, line numbers, and a compact recommendation. The primary agent verifies the cited files before acting.

## Read-only patch proposal

Use when you want implementation help but do not want Codex to edit files.

Prompt requirements:

- Ask for `OUTPUT: Unified Diff Patch ONLY`.
- Include the expected behavior and tests to satisfy.
- Tell Codex not to modify files directly.

After Codex returns a patch, inspect it before applying.

## Isolated write handoff

Use write access only in an isolated worktree, preferably under `/tmp`.

```bash
git worktree add -b codex/<task-name> /tmp/codex-<task-name> HEAD

python3 /path/to/skills/collaborating-with-codex/scripts/codex_bridge.py \
  --cd "/tmp/codex-<task-name>" \
  --sandbox workspace-write \
  --PROMPT "$PROMPT"
```

After completion:

```bash
git -C /tmp/codex-<task-name> diff
git -C /tmp/codex-<task-name> status --short
```

Review and port the changes deliberately. Do not merge blind.

## Parallel read-only runs

Split independent questions into separate Codex sessions:

- one prompt per subsystem or concern
- separate `SESSION_ID` values
- read-only sandbox
- explicit output contracts

Synthesize by comparing contradictions, shared evidence, and gaps. Do not stack unrelated tasks into one Codex run.

## State capsule

Keep this compact state in the primary conversation:

```text
[Codex Capsule] Goal: | SID: | Sandbox: | Files: | Last: | Next:
```

Update it after each Codex turn so compaction or handoff does not lose the thread.
