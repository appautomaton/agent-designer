# Prompt Anti-Patterns

Common mistakes when prompting Codex. Each shows the problem and a fix.

## Vague task framing

Bad:
```
Take a look at this and let me know what you think.
```

Fix — state the job:
```xml
<task>
Review this change for material correctness and regression risks.
</task>
```

## Missing output contract

Bad:
```
Investigate and report back.
```

Fix — define the shape:
```xml
<structured_output_contract>
Return:
1. root cause
2. evidence
3. smallest safe next step
</structured_output_contract>
```

## No follow-through default

Bad:
```
Debug this failure.
```

Fix — tell Codex when to stop:
```xml
<default_follow_through_policy>
Keep going until you have enough evidence to identify the root cause confidently.
</default_follow_through_policy>
```

## Asking for more reasoning instead of a better contract

Bad:
```
Think harder and be very smart.
```

Fix — add a verification loop:
```xml
<verification_loop>
Before finalizing, verify that the answer matches the observed evidence and task requirements.
</verification_loop>
```

## Mixing unrelated jobs into one run

Bad:
```
Review this diff, fix the bug you find, update the docs, and suggest a roadmap.
```

Fix — one task per run:
1. Run review first.
2. Run a separate fix prompt if needed.
3. Use a third run for docs or roadmap.

## Unsupported certainty

Bad:
```
Tell me exactly why production failed.
```

Fix — require grounding:
```xml
<grounding_rules>
Ground every claim in the provided context or tool outputs.
If a point is an inference, label it clearly.
</grounding_rules>
```
