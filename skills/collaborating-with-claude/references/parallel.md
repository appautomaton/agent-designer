# Parallel Execution and Worktree Isolation

Use when a task splits into independent runs, or when write access must be isolated.

## Parallel read-only analysis

For independent analyses that don't modify files, run multiple bridge calls concurrently. In Claude Code, set `run_in_background: true` on each Bash tool call and monitor each via the task-output view (the bridge streams timestamped progress to stderr).

```bash
python3 skills/collaborating-with-claude/scripts/claude_bridge.py \
  --cd "/project" --permission-mode plan \
  --PROMPT "Analyze the auth module for correctness risks."

python3 skills/collaborating-with-claude/scripts/claude_bridge.py \
  --cd "/project" --permission-mode plan \
  --PROMPT "Analyze the payment module for correctness risks."
```

After all complete, synthesize: contradictions, shared dependencies, gaps no run covered, and the concrete next action.

## Claude-managed subagents

Claude can spawn its own subagents for independent lanes via `--agents` (inline JSON) or `--agent <name>`:

```bash
python3 skills/collaborating-with-claude/scripts/claude_bridge.py \
  --cd "/project" --permission-mode plan \
  --PROMPT "Use parallel subagents: one for security risks, one for test gaps, one for maintainability. Wait for all, then summarize only final findings with file references."
```

Keep subagent work read-only unless each write lane has its own worktree. Ask for distilled summaries, not raw logs.

## Worktree isolation

When multiple write-capable runs are needed, use one git worktree per task (canonical setup in [handoff-patterns.md](handoff-patterns.md)):

```bash
git worktree add -b claude/auth-fix /tmp/wt-auth HEAD
git worktree add -b claude/perf-fix /tmp/wt-perf HEAD

python3 skills/collaborating-with-claude/scripts/claude_bridge.py \
  --cd "/tmp/wt-auth" --permission-mode acceptEdits \
  --PROMPT "Fix the auth bug in src/auth/login.py. Run the narrow verification."
```

Review each (`git -C /tmp/wt-auth diff`) before merging, then `git worktree remove /tmp/wt-auth`.

Claude also offers native `claude --worktree <name>` to create a session worktree directly (verify it composes with `--print` for your version before relying on it in scripts).

## Worktree tips

- Put worktrees in `/tmp` or outside the repo.
- `node_modules`, virtualenvs, caches, and build outputs are not shared automatically.
- The same branch cannot be checked out in multiple worktrees.
- Use absolute paths for result files and review artifacts.

## Rate limits

- Start with 2–3 concurrent runs.
- Stagger launches if rate-limit events appear (the bridge surfaces `rate_limited` in its result).
- Split by independent concern; don't run duplicate agents on the same vague task.
