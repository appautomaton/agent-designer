# Prompt Patterns

When to delegate to Claude, and how to shape the prompt.

## When to delegate

| Good fit | Poor fit |
|---|---|
| Large-scale code search or call-chain tracing | Simple edits faster done directly |
| Bug investigation in unfamiliar code | Tasks needing real-time user interaction |
| Cross-model / second-opinion code review | Work involving secrets or production data |
| Architecture comparison grounded in repo files | Questions already answered by current context |
| Parallel analysis of independent concerns | Vague prompts with no scope or expected output |

## Pattern overview

| Pattern | Scenario | Permission mode |
|---|---|---|
| Deep analysis | Root cause, architecture, data flow | `plan` |
| Code review | Pre-commit, PR, security pass | `plan` |
| Parallel research | Multiple independent questions | `plan` |
| Prototyping | Draft code or scaffold | `plan` diff, or `acceptEdits`/`auto` in a worktree |
| Architecture comparison | Evaluate design alternatives | `plan` |

Prefer `--permission-mode plan` (analyze, no writes) or `--tools "Read,Glob,Grep"` for read-only work. Full permission-mode set in [cli-reference.md](cli-reference.md).

## Deep analysis

```text
In this codebase, we are seeing:
<symptom, error, or failing command>

Known clues:
- <file or module>
- <recent change>
- <related stack trace>

Analyze:
1. root cause with file:line evidence
2. full code path involved
3. smallest safe fix approach

Do not modify files.
```

## Bug fix proposal

```text
Bug: <what is happening>
Reproduction: <steps or failing test>
Expected: <correct behavior>

Investigate root cause. Check:
- <paths>
- <related components>

Output: root cause analysis with file:line evidence, then a unified diff fix.
Do not modify files directly.
```

After review, apply with `git apply` (Claude has no separate apply subcommand).

## Code review

Pass the diff in the prompt (Claude has no built-in review subcommand):

```text
Review this diff for correctness, edge cases, and missing tests:
<unified diff>

Output prioritized findings with severity and suggested fixes. Skip formatting-only changes.
```

Or point Claude at the changed paths in `plan` mode and let it read them itself.

## Prototyping

```text
Implement <feature> in <project>.

Requirements:
- <requirement>

Reference:
- <existing similar code path>

Constraints:
- follow existing patterns
- no unrelated refactors

Output: unified diff patch only.
Do not modify files directly.
```

For direct writes, use an isolated worktree with `--permission-mode acceptEdits` (or `auto`). See [handoff-patterns.md](handoff-patterns.md).

## Architecture comparison

```text
We need to implement <feature>. Compare:

Option A: <description>
Option B: <description>

Based on actual code under <paths>, evaluate:
1. implementation complexity
2. performance implications
3. impact on existing code
4. maintainability

Output a comparison table with a recommendation.
```

## Multi-file refactoring

```text
Refactor <what> across <scope>.

Rules:
- <rule>

Files:
- <glob or directory>

Analyze impact first, list affected files, then produce a unified diff.
Do not modify files directly.
```

## Tips

- Point, don't paste: pin file paths and line numbers; let Claude read via `--cd` / `--add-dir`.
- One objective per run; split unrelated work into separate runs.
- State done criteria and output shape (table, JSON, unified diff).
- **Verify Claude's output** before changing final code or reporting to the user — the bridge plumbing is reliable, but the model's reasoning still needs checking.
- Tune effort/cost with `--effort` (`low`→`max`), `--model` (`sonnet`/`opus`), and `--max-budget-usd`. See [cli-reference.md](cli-reference.md).
