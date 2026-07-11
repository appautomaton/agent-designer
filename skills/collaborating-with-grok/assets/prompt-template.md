# Grok Prompt Template

Start with `<task>`. Add only the blocks that materially constrain the run. See [prompt-recipes.md](../references/prompt-recipes.md) for task-specific examples and [prompt-blocks.md](../references/prompt-blocks.md) for optional blocks.

```xml
<task>
State one concrete objective, the relevant repository context, and the expected end state.
</task>

<scope>
Name the workspace, allowed external dependencies, and explicit exclusions.
Omit this block for routine read-only analysis.
</scope>

<done_criteria>
List concrete artifacts and checks.
Omit this block when the answer itself is the only deliverable.
</done_criteria>

<grounding_rules>
Ground claims in provided context or tool output and label inferences.
Use this for diagnosis, review, and research.
</grounding_rules>

<action_safety>
Keep changes scoped and avoid unrelated or irreversible actions.
Use this for write-capable work.
</action_safety>

<verification_loop>
Verify the result against the task requirements before finalizing.
</verification_loop>

<structured_output_contract>
Specify the exact final response shape and nothing more.
</structured_output_contract>
```

CLI flags enforce tool authority and sandbox posture. Prompt text communicates intent; it does not create a security boundary.
