# Parallel Execution and Worktree Isolation

Use this when a task naturally splits into independent grok runs, or when write access must be isolated.

## Parallel read-only analysis

For independent analyses that do not modify files, run multiple bridge calls concurrently. In Claude Code, set `run_in_background: true` on each Bash tool call and monitor each task with TaskOutput. grok sessions are independent — no shared lock — so concurrency is safe.

```bash
python3 <skill_dir>/scripts/grok_bridge.py \
  --cd "/project" --tools "read_file,grep,list_dir" \
  --PROMPT "Analyze the auth module for correctness risks."

python3 <skill_dir>/scripts/grok_bridge.py \
  --cd "/project" --tools "read_file,grep,list_dir" \
  --PROMPT "Analyze the payment module for correctness risks."
```

After all tasks complete, synthesize:

- contradictions between analyses
- shared dependencies or repeated findings
- gaps no run covered
- a concrete next action for the primary agent

Each run returns its own `SESSION_ID`; keep them if you want to follow up on a specific lane.

## Worktree isolation for writes

When multiple grok instances need write access, give each its own standalone git worktree so they cannot clobber each other. Obtain write consent and pass authority explicitly.

```bash
git worktree add -b grok/auth-fix /tmp/wt-auth HEAD
git worktree add -b grok/perf-fix /tmp/wt-perf HEAD

python3 <skill_dir>/scripts/grok_bridge.py \
  --cd "/tmp/wt-auth" --always-approve --sandbox workspace \
  --PROMPT "Fix the auth bug in src/auth/login. Keep changes scoped, then summarize."

python3 <skill_dir>/scripts/grok_bridge.py \
  --cd "/tmp/wt-perf" --always-approve --sandbox workspace \
  --PROMPT "Optimize the query in src/db/queries. Keep changes scoped, then summarize."
```

For non-trivial implementations, replace the one-line examples with the canonical isolated-implementation recipe from [prompt-recipes.md](prompt-recipes.md). Treat a lane as delivered only when its bridge result has `success: true` and `complete: true`.

Review each result before merging:

```bash
git -C /tmp/wt-auth diff
git -C /tmp/wt-perf diff

cd /original/repo
git merge grok/auth-fix
git merge grok/perf-fix
```

Cleanup after review:

```bash
git worktree remove /tmp/wt-auth
git worktree remove /tmp/wt-perf
```

grok also has native `grok worktree` / `-w` support, but for portability across these collaboration skills, prefer plain `git worktree` driven by the bridge's `--cd`.

## Worktree tips

- Put worktrees in `/tmp` or outside the repo.
- Remember that `workspace` limits writes, not arbitrary reads; use stronger external isolation when required.
- Use `git worktree add --detach /tmp/wt-readonly HEAD` for read-only codebase snapshots.
- `node_modules`, virtualenvs, caches, and build outputs are not shared automatically.
- The same branch cannot be checked out in multiple worktrees.
- Use absolute paths for result files and review artifacts.

## Rate limits

- Start with 2–3 concurrent grok runs.
- Stagger launches if rate-limit errors appear on stderr.
- Split by independent concern; do not run duplicate agents on the same vague task.
