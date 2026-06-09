# Claude Prompt Template (Token-Efficient)

Prefer model aliases (`--model sonnet` for routine work, `--model opus` for harder tasks); omit `--model` to use the CLI default. For complex or high-stakes work, upgrade to the XML blocks in [../references/prompt-blocks.md](../references/prompt-blocks.md) and recipes in [../references/prompt-recipes.md](../references/prompt-recipes.md).

## Analysis / Plan (read-only)

```
Task:
- <what to analyze>

Repo pointers:
- <file paths + approximate line numbers>

Constraints:
- Keep it concise and actionable.
- Reference files/lines instead of pasting code.

Output:
- Bullet list of findings and a proposed plan.
```

## Patch (Unified Diff only)

```
Task:
- <what to change>

Repo pointers:
- <file paths + approximate line numbers>

Constraints:
- OUTPUT: Unified Diff Patch ONLY.
- Minimal, focused changes. No unrelated refactors.

Output:
- A single unified diff patch.
```

## Review (audit an existing diff)

```
Task:
- Review the following unified diff for correctness, edge cases, and missing tests.

Constraints:
- Return a checklist of issues + suggested fixes (no code unless requested).

Input diff:
<paste unified diff here>
```

## Implementation (worktree + acceptEdits)

```
Task:
- <what to implement>

Repo pointers:
- <entry file paths + approximate line numbers>

Done criteria:
- <specific acceptance criteria>

Constraints:
- Stay focused on the stated task. No unrelated refactors.
- Run the narrowest test that proves correctness.

Output:
- List of files changed and a brief summary.
```

Run implementation with write access only in an isolated worktree (`--permission-mode acceptEdits`); see [../references/handoff-patterns.md](../references/handoff-patterns.md).

## When to upgrade to XML blocks

Use the XML blocks in [../references/prompt-blocks.md](../references/prompt-blocks.md) when:
- The task is multi-step and you need a `<completeness_contract>`.
- Correctness matters and you want a `<verification_loop>`.
- You're doing review/research and need `<grounding_rules>`.
- Claude keeps stopping early — add `<default_follow_through_policy>`.

See [../references/prompt-recipes.md](../references/prompt-recipes.md) for ready-to-use end-to-end templates.
