# Shell quoting for `--PROMPT`

When invoking `grok_bridge.py`, remember that your shell parses the command line before Python receives the prompt.

## The pitfall: Markdown backticks

Markdown inline code uses backticks (`` `like/this` ``). In bash/zsh, backticks mean command substitution, even inside double quotes, so this breaks before grok runs:

```bash
python3 <skill_dir>/scripts/grok_bridge.py \
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

python3 <skill_dir>/scripts/grok_bridge.py \
  --cd "." \
  --tools "read_file,grep,list_dir" \
  --PROMPT "$PROMPT"
```

## Alternatives

- For large or generated prompts, write the prompt to a file and pass `--prompt-file prompts/task.md`. Relative paths resolve against `--cd`; absolute paths are unchanged. grok reads the file natively, sidestepping argv and shell-quoting limits entirely.
- Escape backticks manually as `` \` ``.
- Avoid Markdown backticks in CLI prompts.
