# Prompt Patterns

Use this file to choose a delegation posture. Build the actual prompt from [prompt-recipes.md](prompt-recipes.md); do not maintain a second wording here.

## Selection

| Pattern | Use when | Bridge posture |
|---|---|---|
| Diagnosis | Root cause or unfamiliar code path | `--tools "read_file,grep,list_dir"` |
| Review | Independent correctness or regression pass | `--tools "read_file,grep,list_dir"` |
| Patch proposal | You want a diff without writes | read-only tools + exact unified-diff contract |
| Implementation | Grok should edit and test | standalone worktree + explicit user consent + `--always-approve` |
| Web/X research | Current facts need source URLs | explicit coding model + deny shell/edit tools |
| Live audit | Every command must be visible while it runs | ACP, not the headless bridge |

## Good delegation boundaries

- Give Grok one objective per run.
- Point to repository paths and approximate lines instead of pasting large files.
- Include known symptoms, failing commands, and recent changes when they narrow the search.
- State exact done criteria for implementation and an exact output contract for analysis.
- Keep access control in CLI flags and external isolation; use the prompt to state intent and scope.
- Verify Grok's cited files and artifacts before adopting its conclusion.

## Poor fits

- Trivial edits the primary agent can complete faster.
- Vague prompts without an observable end state.
- Secrets, production data, or irreversible external actions.
- Real-time interaction or command auditing through headless output.
- Multiple unrelated jobs bundled into one turn.
