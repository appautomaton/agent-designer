# Backlog

Deferred work items. Review at session start; delete items when done.

## docs/setup: dedicated Grok and Antigravity host runbooks

The setup docs cover Claude Code and Codex hosts. Grok CLI reads a project's `.claude/skills/` (see the config section of `skills/collaborating-with-grok/references/cli-reference.md`), so a Claude Code project install already serves Grok hosts. Write dedicated runbooks when Grok or agy hosting gets real use.

## Package as a Claude Code plugin

A plugin (marketplace plus `/plugin install`) is the first-class drop-in install path for Claude Code and would replace the manual copy step in `docs/setup/claude-code.md`. Evaluate once the à la carte setup docs have settled.

## collaborating-with-antigravity: reference parity

The antigravity skill ships 3 reference files where its siblings (claude, codex, grok) ship 9 — missing `prompt-blocks`, `prompt-recipes`, `patterns`, `prompt-antipatterns`, and `handoff-patterns`. Worth a deliberate authoring pass **if agy delegation gets heavy use**; don't copy-paste from siblings — agy is advisory-first (no writes by convention) so the recipes differ. Note: `parallel.md` is intentionally absent — the bridge serializes calls with a file lock.

## collaborating-with-grok: terminal/web allowlist session build bug (still open on 0.2.93)

Re-probed on **v0.2.93 stable** (2026-07-11): `--tools` allowlists containing `web_search`, `web_fetch`, or `run_terminal_cmd` fail at session build:
`RequirementError { tool: "GrokBuild:run_terminal_cmd", message: "auto_background_on_timeout requires enabled_background to be true" }`. Confirmed with both `read_file,web_search` and `run_terminal_cmd`; `read_file,grep,list_dir` works. Default toolset + `--disallowed-tools` remains the workaround; skill docs + bridge warn accordingly.

**When a newer grok ships:** re-run both repros. If fixed, delete the allowlist warnings in `skills/collaborating-with-grok/SKILL.md` + `references/cli-reference.md` and the terminal/web allowlist warning block in `scripts/grok_bridge.py` — then restamp per the no-lookback policy.
