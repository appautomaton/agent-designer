# Backlog

Deferred work items. Review at session start; delete items when done.

## collaborating-with-antigravity: reference parity

The antigravity skill ships 3 reference files where its siblings (claude, codex, grok) ship 9 — missing `prompt-blocks`, `prompt-recipes`, `patterns`, `prompt-antipatterns`, and `handoff-patterns`. Worth a deliberate authoring pass **if agy delegation gets heavy use**; don't copy-paste from siblings — agy is advisory-first (no writes by convention) so the recipes differ. Note: `parallel.md` is intentionally absent — the bridge serializes calls with a file lock.

## collaborating-with-grok: allowlist + web_search session build bug (still open on 0.2.93)

Re-probed on **v0.2.93** (2026-07-08): any `--tools` allowlist that includes `web_search` still fails at session build:
`RequirementError { tool: "GrokBuild:run_terminal_cmd", message: "auto_background_on_timeout requires enabled_background to be true" }`. Repro: `grok -p "hi" --tools "read_file,web_search"`. Denylist form remains the workaround; skill docs + bridge warn accordingly.

**When a newer grok ships:** re-run the repro. If fixed, delete the allowlist warnings in `skills/collaborating-with-grok/SKILL.md` + `references/cli-reference.md` and the `web_search`-allowlist warning block in `scripts/grok_bridge.py` — then restamp per the no-lookback policy.
