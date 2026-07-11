# Codex CLI setup

This runbook installs skills from this repo into Codex CLI. Execute it literally: every step states the command to run and the result to expect. Replace `<skill-name>` with one of `collaborating-with-claude`, `collaborating-with-grok`, `collaborating-with-antigravity`, or `issue-driven-workflow`. Skip `collaborating-with-codex` on Codex hosts in most cases, because Codex delegating to Codex rarely adds value.

## 1. Prerequisites

- `git` and `python3` (3.9 or newer) on PATH.
- Codex CLI installed and signed in (`codex login`).
- For each bridge skill, the child CLI it delegates to must be installed and authenticated: `claude` for collaborating-with-claude (run `claude` then `/login`, or set `ANTHROPIC_API_KEY`), `grok` for collaborating-with-grok, `agy` for collaborating-with-antigravity.
- `issue-driven-workflow` needs only `python3`.

## 2. Install

Clone once, then install each skill you want. Copy for a stable install, or symlink to track your clone.

Global install, available in every project:

```bash
git clone https://github.com/appautomaton/agent-designer.git ~/src/agent-designer
mkdir -p ~/.codex/skills
cp -R ~/src/agent-designer/skills/<skill-name> ~/.codex/skills/
rm -rf ~/.codex/skills/<skill-name>/scripts/__pycache__
```

Symlink variant, where `git pull` in the clone updates the install:

```bash
ln -s ~/src/agent-designer/skills/<skill-name> ~/.codex/skills/<skill-name>
```

Project install, committed with the project and shared with teammates:

```bash
mkdir -p <project>/.codex/skills
cp -R ~/src/agent-designer/skills/<skill-name> <project>/.codex/skills/
rm -rf <project>/.codex/skills/<skill-name>/scripts/__pycache__
```

## 3. Approve

Codex has no settings allowlist equivalent to Claude Code's `permissions.allow`, so two gates matter instead.

- Approval gate: `codex exec` is non-interactive, and nothing can be approved mid-run. A gated bridge call fails on the spot rather than prompting. Run bridge calls where an escalation can be approved, or accept that a denial surfaces as an immediate error.
- Sandbox gate: both `read-only` and `workspace-write` block shell network, and every child CLI needs API network to reach its backend. Run the bridge call through an approved escalation, or knowingly grant network for that call.

For collaborating-with-claude specifically: the child `claude` must be signed in before the first bridge call. The `--help` smoke test in Verify confirms the wiring without any network grant.

## 4. Verify

1. Confirm the install location:

   ```bash
   ls ~/.codex/skills/<skill-name>/SKILL.md
   ```

   Expected: the path prints with no error.

2. Start a new Codex session and ask "what skills are available". Expected: the reply lists `<skill-name>`.

3. For a bridge skill, run its help check, for example:

   ```bash
   python3 ~/.codex/skills/collaborating-with-claude/scripts/claude_bridge.py --help
   ```

   Expected: a usage block starting with `usage: claude_bridge.py`.

## 5. Update and uninstall

- Update a copied install by re-copying from a pulled clone. A symlinked install updates with `git pull` alone.
- Uninstall by deleting the skill directory.

## What you can do now

- "Hand this refactor to Claude Code in plan mode and report its findings."
- "Have Claude Code review this diff and return a unified patch."
- "Use collaborating-with-grok to run a live X search on `<topic>` with cited URLs."
- "Ask antigravity for a second opinion on this design tradeoff."
- "Create a plan and issue CSV for `<goal>`, then execute it row by row."
