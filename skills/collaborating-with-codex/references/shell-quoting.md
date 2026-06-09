# Shell quoting for `--PROMPT`

When invoking `codex_bridge.py`, remember that your shell parses the command line before Python receives the prompt.

## The pitfall: Markdown backticks

Markdown inline code uses backticks (`` `like/this` ``). In bash/zsh, backticks mean command substitution, even inside double quotes, so this breaks before Codex runs:

```bash
python3 skills/collaborating-with-codex/scripts/codex_bridge.py \
  --cd "." \
  --PROMPT "Analyze `tmp/raw.json` and summarize."
```

Typical symptoms:

- `zsh: permission denied: tmp/raw.json`
- `zsh: command not found: as_of`

## Recommended: heredoc

Build the prompt with a single-quoted heredoc delimiter (`<<'EOF'`) so backticks, `$VARS`, and `$(...)` are not expanded by the shell:

```bash
PROMPT="$(cat <<'EOF'
Analyze `tmp/raw.json` and summarize.
Set `as_of` to `YYYY-MM-DD`.
EOF
)"

python3 skills/collaborating-with-codex/scripts/codex_bridge.py \
  --cd "." \
  --PROMPT "$PROMPT"
```

## Alternatives

- Escape backticks manually as `` \` ``.
- Avoid Markdown backticks in CLI prompts.
