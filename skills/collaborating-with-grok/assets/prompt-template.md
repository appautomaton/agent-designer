# Grok Prompt Template

Quick plain-text starters for common tasks. For complex or high-stakes work, use the XML prompt blocks in `references/prompt-blocks.md` and recipes in `references/prompt-recipes.md`.

## Analysis / Plan (read-only)

Run with `--tools "read_file,grep,list_dir"`.

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

Run with `--tools "read_file,grep,list_dir"` so grok cannot edit.

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

## Review

```
Task:
- Review the following unified diff for correctness, edge cases, and missing tests.

Constraints:
- Return a checklist of issues + suggested fixes (no code unless requested).

Input diff:
<paste unified diff here>
```

## Web / X research (live)

Run with `--disallowed-tools "run_terminal_cmd,search_replace"` (keeps web_search).

```
Task:
- <current question about releases, facts, or X posts>

Constraints:
- Use web and X search. Cite a source URL for each key fact.
- Separate facts from inferences; flag anything search couldn't confirm.

Output:
- Findings with source URLs, then open questions.
```

## Implementation (worktree + writes)

Run in an isolated worktree with `--always-approve` (or `--permission-mode acceptEdits`).

```
Task:
- <what to implement>

Repo pointers:
- <entry file paths + approximate line numbers>

Done criteria:
- <specific acceptance criteria>

Constraints:
- Stay focused on the stated task. No unrelated refactors.

Output:
- List of files changed and a brief summary.
```

## When to upgrade to XML blocks

Use XML prompt blocks (`references/prompt-blocks.md`) when:
- The task is multi-step and you need a `<completeness_contract>`.
- Correctness matters and you want a `<verification_loop>`.
- You're doing review/research and need `<grounding_rules>` or `<citation_rules>`.
- grok keeps stopping early — add `<default_follow_through_policy>`.

See `references/prompt-recipes.md` for ready-to-use end-to-end templates.
