# Grok Handoff Patterns

Use these to decide how much authority to give grok and how to bring its work back into the primary session.

## Read-only analysis

For diagnosis, architecture opinions, reviews, and code research.

```bash
python3 skills/collaborating-with-grok/scripts/grok_bridge.py \
  --cd "/path/to/repo" \
  --tools "read_file,grep,list_dir" \
  --PROMPT "$PROMPT"
```

Ask grok for evidence, file paths, line numbers, and a compact recommendation. The primary agent verifies the cited files before acting. Tool calls are not visible live in headless output; use ACP if live command auditing is required.

## Live web / X research

When the task needs current facts, releases, or X posts.

```bash
python3 skills/collaborating-with-grok/scripts/grok_bridge.py \
  --cd "/path/to/repo" \
  --disallowed-tools "run_terminal_cmd,search_replace" \
  --PROMPT "$PROMPT"
```

Keeps `web_search`/`web_fetch`, removes shell and edit. Set `GROK_WEB_FETCH=1` in the environment if grok needs to fetch specific URLs. Web search adds latency; run in the background.

## File-backed handoff

When a generated plan, review packet, or issue bundle is too large or too shell-sensitive for argv, write it to a file. Two shapes:

**Whole prompt in the file** — the file *is* the instruction:

```bash
python3 skills/collaborating-with-grok/scripts/grok_bridge.py \
  --cd "/path/to/repo" \
  --tools "read_file,grep,list_dir" \
  --prompt-file prompts/grok-handoff.md
```

Relative `--prompt-file` and `--stdin-file` paths resolve against `--cd`; use an absolute path only when the handoff intentionally lives elsewhere.

**Context file + a short instruction** — author the context/plan once, then steer it with text. `--PROMPT` carries the ask; the bridge combines it with the context in a temporary native prompt file because Grok 0.2.93 ignores stdin when `-p` is present:

```bash
python3 skills/collaborating-with-grok/scripts/grok_bridge.py \
  --cd "/path/to/repo" \
  --tools "read_file,grep,list_dir" \
  --stdin-file /tmp/grok-context.md \
  --PROMPT "Using the supplied context, produce a prioritized review. Cite file:line."
```

Keep the handoff self-consistent: one objective, relevant path pointers, scope, done criteria when applicable, verification, and an exact output contract. Use [prompt-recipes.md](prompt-recipes.md) rather than inventing a parallel format.

## Read-only patch proposal

When you want implementation help but don't want grok to edit files.

- Run with `--tools "read_file,grep,list_dir"` (no edit tool present).
- Use the narrow-fix recipe's raw-diff contract: begin with `---`/`+++`, with no Markdown fences or surrounding prose.
- Include the expected behavior and tests to satisfy.

After grok returns a patch, confirm it is raw diff text and inspect it before applying with `git apply`.

## Isolated write handoff

Grant write access only in an isolated worktree, preferably outside the parent repository. Obtain user consent, pass `--always-approve` explicitly, and pair it with the appropriate Grok sandbox profile.

```bash
git worktree add -b grok/<task-name> /tmp/grok-<task-name> HEAD

python3 skills/collaborating-with-grok/scripts/grok_bridge.py \
  --cd "/tmp/grok-<task-name>" \
  --always-approve --sandbox workspace \
  --prompt-file prompts/grok-task.md
```

Build `prompts/grok-task.md` from the isolated-implementation recipe. `--always-approve` lets grok edit and run shell and is mutually exclusive with `--permission-mode`. For narrower authority, prefer explicit rules such as `--allow "Edit(src/**)" --deny "Bash(rm*)"`; Grok 0.2.93 accepts `--permission-mode acceptEdits` but does not enforce it from the CLI.

`--sandbox workspace` limits writes but not arbitrary reads. A worktree nested inside a larger repository can inherit parent instructions and metadata; use a standalone directory plus `strict` or an external container when hard read isolation matters. After completion:

```bash
git -C /tmp/grok-<task-name> diff
git -C /tmp/grok-<task-name> status --short
```

Review and port deliberately. Do not merge blind.

## State capsule

Keep this compact state in the primary conversation and update it after each grok turn so compaction or handoff does not lose the thread:

```text
[Grok Capsule] Goal: | SID: | Model: | PermMode: | Files: | Last: | Next:
```
