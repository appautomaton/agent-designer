# Prompt Patterns

Use this for deciding when to delegate and how to shape the prompt.

## When to delegate

| Good fit | Poor fit |
|---|---|
| Large-scale code search or call-chain tracing | Simple edits faster for the primary agent |
| Bug investigation in unfamiliar code | Tasks requiring real-time user interaction |
| Cross-model code review | Work involving secrets or production data |
| Architecture comparison grounded in repo files | Questions already answered by current context |
| Parallel analysis of independent concerns | Vague prompts with no scope or expected output |

## Pattern overview

| Pattern | Scenario | Sandbox |
|---|---|---|
| Deep analysis | Root cause, architecture, data flow | `read-only` |
| Code review | Pre-commit, PR, security pass | `read-only` |
| Parallel research | Multiple independent questions | `read-only` |
| Prototyping | Draft code or scaffold | `read-only` diff or isolated `workspace-write` |
| Architecture comparison | Evaluate design alternatives | `read-only` |

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

After review, apply manually, use `git apply`, or use `codex apply <TASK_ID>` only when you have reviewed the Codex-produced diff.

## Code review

Use direct review for repository diffs:

```bash
codex exec review --uncommitted -o /tmp/review.md
codex exec review --base origin/main -o /tmp/review.md
```

For focused review prompts:

```text
Review the changes in src/auth/ for:
- SQL injection vulnerabilities
- missing validation
- race conditions in session handling

Skip formatting-only changes.
Output prioritized findings with severity and suggested fixes.
```

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

For direct writes, move to an isolated worktree and use `--sandbox workspace-write`.

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

- Set boundaries: say what not to touch.
- Pin file paths and line numbers.
- Provide clues: failing commands, stack traces, recent commits.
- Request structured output: table, JSON, or unified diff.
- Split unrelated work into separate Codex runs.
- Match effort with `-c 'model_reasoning_effort="medium"'` or `"xhigh"` when needed.
