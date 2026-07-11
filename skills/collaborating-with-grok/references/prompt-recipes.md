# Prompt Recipes

Use the smallest recipe that fully defines the task. Keep blocks in this order: objective, scope or evidence rules, follow-through, verification, output. Delete blocks that do not change behavior.

Blocks reference: [prompt-blocks.md](prompt-blocks.md)

## Diagnosis

Run read-only with `--tools "read_file,grep,list_dir"`.

```xml
<task>
Diagnose why [failure] occurs in this repository and identify the smallest safe next step.
Inspect [paths, command output, or known clues].
</task>

<grounding_rules>
Ground every claim in repository files or tool output.
Label hypotheses and state any evidence still missing.
</grounding_rules>

<default_follow_through_policy>
Continue until the evidence supports one root cause confidently.
Only ask when missing context changes correctness or safety.
</default_follow_through_policy>

<verification_loop>
Before finalizing, check that the root cause explains every observed symptom.
</verification_loop>

<structured_output_contract>
Return: root cause, evidence with file:line references, smallest safe next step, and residual uncertainty.
</structured_output_contract>
```

## Narrow fix proposal

Run read-only with `--tools "read_file,grep,list_dir"`.

```xml
<task>
Propose the smallest safe fix for [issue].
Preserve behavior outside the failing path.
</task>

<scope>
Inspect only the relevant repository paths.
Do not modify files.
</scope>

<action_safety>
Avoid unrelated refactors, renames, or cleanup.
</action_safety>

<verification_loop>
Check the patch against the expected behavior and named tests.
</verification_loop>

<structured_output_contract>
Return a raw unified diff beginning with `---` and `+++`.
Do not use Markdown code fences or add prose before or after the diff.
</structured_output_contract>
```

## Root-cause review

Run read-only with `--tools "read_file,grep,list_dir"`.

```xml
<task>
Review [change or diff] for material correctness and regression risks.
</task>

<grounding_rules>
Ground every finding in repository files or tool output.
Label inferences clearly.
</grounding_rules>

<dig_deeper_nudge>
Check second-order failures, empty states, retries, stale state, and rollback paths.
</dig_deeper_nudge>

<structured_output_contract>
Return findings ordered by severity, evidence with file:line references, and concise next steps.
</structured_output_contract>
```

## Isolated implementation

Run only after write authority is appropriate, preferably in a standalone worktree with `--always-approve --sandbox workspace`.

```xml
<task>
Implement [single concrete change] in the designated workspace.
</task>

<scope>
Work only within [workspace].
Use only [explicit external runtime dependencies].
Do not modify unrelated files or perform external side effects.
</scope>

<done_criteria>
Produce [artifacts].
Run [checks] successfully.
Leave the result reproducible.
</done_criteria>

<action_safety>
Keep changes scoped and avoid destructive or irreversible actions.
</action_safety>

<verification_loop>
Verify every done criterion against files and tool output before finalizing.
</verification_loop>

<structured_output_contract>
Return the result, checks run, files changed, and residual risks.
Do not claim checks or sensory evaluation that did not occur.
</structured_output_contract>
```

The prompt states intended scope; `--sandbox`, tool policy, and external isolation enforce access. Use ACP instead of this headless bridge when every command must be audited live.

## Live web / X research

Run with `--model grok-4.5 --disallowed-tools "run_terminal_cmd,search_replace" --timeout 300`, or use the current coding model from `--list-models`.

```xml
<task>
Research the current state of [topic] using web and X search, then recommend a path.
</task>

<research_mode>
Separate observed facts, reasoned inferences, and open questions.
Go deeper only where evidence changes the recommendation.
</research_mode>

<citation_rules>
Back important claims with primary-source URLs.
State when search cannot confirm a point.
</citation_rules>

<structured_output_contract>
Return key facts with URLs, recommendation, tradeoffs, and unresolved questions.
</structured_output_contract>
```
