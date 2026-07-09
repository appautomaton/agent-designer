# Prompt Recipes

End-to-end prompt templates for common grok tasks.
Copy the smallest recipe that fits, then trim what you don't need.

Blocks reference: [prompt-blocks.md](prompt-blocks.md)

## Diagnosis

Find the root cause of a failing test, command, or runtime error.

```xml
<task>
Diagnose why [failing test / command / error] is breaking in this repository.
Use the available repository context and tools to identify the most likely root cause.
</task>

<compact_output_contract>
Return a compact diagnosis with:
1. most likely root cause
2. evidence
3. smallest safe next step
</compact_output_contract>

<default_follow_through_policy>
Keep going until you have enough evidence to identify the root cause confidently.
Only stop to ask questions when a missing detail changes correctness materially.
</default_follow_through_policy>

<verification_loop>
Before finalizing, verify that the proposed root cause matches the observed evidence.
</verification_loop>

<missing_context_gating>
Do not guess missing repository facts.
If required context is absent, state exactly what remains unknown.
</missing_context_gating>
```

Run read-only: `--tools "read_file,grep,list_dir"`.

## Narrow fix (unified diff)

Propose the smallest safe fix without editing files.

```xml
<task>
Propose the smallest safe fix for [issue] in this repository.
Preserve existing behavior outside the failing path.
</task>

<structured_output_contract>
Return:
1. summary of the fix
2. touched files
3. a single unified diff patch
4. residual risks or follow-ups
OUTPUT the diff only — do not modify files.
</structured_output_contract>

<action_safety>
Keep changes tightly scoped to the stated task.
Avoid unrelated refactors or cleanup.
</action_safety>
```

## Root-cause review

Analyze a change for correctness and regression risks.

```xml
<task>
Analyze this change for material correctness and regression issues.
Focus on the provided repository context only.
</task>

<structured_output_contract>
Return:
1. findings ordered by severity
2. supporting evidence (file:line) for each finding
3. brief next steps
</structured_output_contract>

<grounding_rules>
Ground every claim in the repository context or tool outputs.
If a point is an inference, label it clearly.
</grounding_rules>

<dig_deeper_nudge>
Check for second-order failures, empty-state handling, retries, stale state, and rollback paths before finalizing.
</dig_deeper_nudge>
```

## Live web / X research

Explore current facts and recommend a path, with sources.

```xml
<task>
Research the current state of [topic] using web and X search, and recommend the best path.
</task>

<structured_output_contract>
Return:
1. key facts, each with a source URL
2. reasoned recommendation
3. tradeoffs
4. open questions live search could not settle
</structured_output_contract>

<research_mode>
Separate observed facts, reasoned inferences, and open questions.
Prefer breadth first, then go deeper only where the evidence changes the recommendation.
</research_mode>

<citation_rules>
Back important claims with a source URL. Prefer primary sources.
</citation_rules>
```

Run with `--model grok-4.5 --disallowed-tools "run_terminal_cmd,search_replace" --timeout 300` (or the current coding id from `--list-models`) — pass an explicit coding model when search/X matters (host config can select composer) and give research loops a generous timeout.
