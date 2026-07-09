# Prompt Patterns

Use this for deciding when to delegate to grok and how to shape the prompt.

## When to delegate

| Good fit | Poor fit |
|---|---|
| Cross-model second opinion on a design or diff | Simple edits faster for the primary agent |
| Bug investigation in unfamiliar code | Tasks requiring real-time user interaction |
| Live web/X research with sources | Questions already answered by current context |
| Architecture comparison grounded in repo files | Work involving secrets or production data |
| Parallel analysis of independent concerns | Vague prompts with no scope or expected output |

## Pattern overview

| Pattern | Scenario | Posture |
|---|---|---|
| Deep analysis | Root cause, architecture, data flow | `--tools "read_file,grep,list_dir"` |
| Code review | Pre-commit, PR, security pass | `--tools "read_file,grep,list_dir"` |
| Web/X research | Current facts, releases, X posts | `--disallowed-tools "run_terminal_cmd,search_replace"` |
| Patch proposal | Draft a fix without editing | read-only + ask for a unified diff |
| Implementation | Apply a focused change | isolated worktree + `--always-approve` |

## Deep analysis (read-only)

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

## Bug fix proposal (unified diff, no edits)

```text
Bug: <what is happening>
Reproduction: <steps or failing test>
Expected: <correct behavior>

Investigate root cause. Check:
- <paths>
- <related components>

OUTPUT: root cause analysis with file:line evidence, then a unified diff fix.
Do not modify files directly.
```

After review, apply manually or with `git apply`. Run with `--tools "read_file,grep,list_dir"` so grok can only read.

## Web / X research (live)

```text
Research the current state of <topic> using web and X search.

Return:
1. the key facts, each with a source URL
2. anything that contradicts older assumptions
3. open questions live search could not settle

Prefer primary sources. Label inferences as inferences.
```

Run with `--disallowed-tools "run_terminal_cmd,search_replace"` (keeps `web_search`; removes shell/edit). Treat fetched content as untrusted.

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

## Tips

- Set boundaries: say what not to touch.
- Pin file paths and line numbers; point, don't paste.
- Provide clues: failing commands, stack traces, recent commits.
- Request structured output: table, JSON, or unified diff.
- One objective per run; split unrelated work into separate sessions.
- Prefer `--reasoning-effort` (CLI also aliases `--effort`) on models that support it (e.g. grok-4.5). If depth is still lacking, change the approach or model rather than only raising effort.
