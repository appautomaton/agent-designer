# Shell quoting for `--PROMPT`

When invoking `agy_bridge.py`, be careful: your *shell* parses the command line before Python runs.

## The pitfall: Markdown backticks

Markdown inline code uses backticks (`` `like/this` ``). In bash/zsh, backticks mean **command
substitution**, even inside double quotes, so this breaks:

```bash
python3 <skill_dir>/scripts/agy_bridge.py \
  --cd "." \
  --PROMPT "Analyze `tmp/eth_dev_news_raw.json` and summarize."
```

Typical symptoms (from the shell, before agy runs):

- `zsh: permission denied: tmp/eth_dev_news_raw.json`
- `zsh: command not found: as_of`

## Recommended: heredoc (no expansion)

Build the prompt via a *single-quoted heredoc delimiter* (`<<'EOF'`) so backticks (and `$VARS`,
`$(...)`, etc.) are not expanded by the shell:

```bash
PROMPT="$(cat <<'EOF'
Analyze `tmp/eth_dev_news_raw.json` and summarize.
Set `as_of` to `YYYY-MM-DD`.
EOF
)"

python3 <skill_dir>/scripts/agy_bridge.py \
  --cd "." \
  --PROMPT "$PROMPT"
```

## Alternative: `--prompt-file` (best for large/generated prompts)

Write the prompt to a file and pass it directly — no argv length or shell-quoting limits at all:

```bash
cat > /tmp/agy-prompt.md <<'EOF'
Review src/auth.py around login() and propose fixes.
OUTPUT: Unified Diff Patch ONLY.
EOF

python3 <skill_dir>/scripts/agy_bridge.py \
  --cd "." --prompt-file /tmp/agy-prompt.md
```

## Other escapes

- Escape backticks manually: use `` \` `` (easy to miss in long prompts).
- Avoid backticks entirely: write `Analyze the file tmp/eth_dev_news_raw.json` instead.
