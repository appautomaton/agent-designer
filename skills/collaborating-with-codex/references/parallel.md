# Parallel Execution and Worktree Isolation

Use this when a task naturally splits into independent Codex runs or when write access must be isolated.

## Parallel read-only analysis

For independent analyses that do not modify files, run multiple bridge calls concurrently. In Claude Code, set `run_in_background: true` on each Bash tool call and monitor each task with TaskOutput.

```bash
python3 <skill_dir>/scripts/codex_bridge.py \
  --cd "/project" \
  --sandbox read-only \
  --PROMPT "Analyze auth module for correctness risks."

python3 <skill_dir>/scripts/codex_bridge.py \
  --cd "/project" \
  --sandbox read-only \
  --PROMPT "Analyze payment module for correctness risks."
```

For direct CLI output files, use current flags:

```bash
codex exec --json -C /project -s read-only -o /tmp/result-auth.md -- "Analyze auth"
codex exec --json -C /project -s read-only -o /tmp/result-pay.md -- "Analyze payments"
```

After all tasks complete, synthesize:

- contradictions between analyses
- shared dependencies or repeated findings
- gaps no agent covered
- concrete next action for the primary agent

## Worktree isolation

When multiple Codex instances need write access, use one git worktree per task.

```bash
git worktree add -b codex/auth-fix /tmp/wt-auth HEAD
git worktree add -b codex/perf-fix /tmp/wt-perf HEAD
```

Then run each write task in its own worktree:

```bash
python3 <skill_dir>/scripts/codex_bridge.py \
  --cd "/tmp/wt-auth" \
  --sandbox workspace-write \
  --PROMPT "Fix auth bug in src/auth/login.py. Run the narrow verification."

python3 <skill_dir>/scripts/codex_bridge.py \
  --cd "/tmp/wt-perf" \
  --sandbox workspace-write \
  --PROMPT "Optimize query in src/db/queries.py. Run the narrow verification."
```

Review each result before merging:

```bash
git -C /tmp/wt-auth diff
git -C /tmp/wt-perf diff

cd /original/repo
git merge codex/auth-fix
git merge codex/perf-fix
```

Cleanup after review:

```bash
git worktree remove /tmp/wt-auth
git worktree remove /tmp/wt-perf
```

## Worktree tips

- Put worktrees in `/tmp` or outside the repo.
- Use `git worktree add --detach /tmp/wt-readonly HEAD` for read-only codebase snapshots.
- `node_modules`, virtualenvs, caches, and build outputs are not shared automatically.
- The same branch cannot be checked out in multiple worktrees.
- Use absolute paths for result files and review artifacts.
- If Codex's environment lacks `rg`, prompts should allow fallback to `find`, `ls`, `sed`, or language-native tooling.

## Rate limits

- Start with 2-3 concurrent Codex runs.
- Stagger launches if rate limit errors appear.
- Split by independent concern; do not run duplicate agents on the same vague task.
