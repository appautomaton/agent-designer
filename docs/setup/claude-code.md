# Claude Code setup

This runbook installs skills from this repo into Claude Code. Execute it literally: every step states the command to run and the result to expect. Replace `<skill-name>` with one of `collaborating-with-codex`, `collaborating-with-grok`, `collaborating-with-antigravity`, or `issue-driven-workflow`. Skip `collaborating-with-claude` on Claude Code hosts, because Claude delegating to Claude adds nothing.

## 1. Prerequisites

- `git` and `python3` (3.9 or newer) on PATH.
- Claude Code installed and signed in.
- For each bridge skill, the child CLI it delegates to must be installed and authenticated: `codex` for collaborating-with-codex, `grok` for collaborating-with-grok, `agy` for collaborating-with-antigravity. Each skill's SKILL.md states its auth check under Verification.
- `issue-driven-workflow` needs only `python3`.

## 2. Install

Clone once, then install each skill you want. Copy for a stable install, or symlink to track your clone.

Global install, available in every project:

```bash
git clone https://github.com/appautomaton/agent-designer.git ~/src/agent-designer
mkdir -p ~/.claude/skills
cp -R ~/src/agent-designer/skills/<skill-name> ~/.claude/skills/
rm -rf ~/.claude/skills/<skill-name>/scripts/__pycache__
```

Symlink variant, where `git pull` in the clone updates the install:

```bash
mkdir -p ~/.claude/skills
ln -s ~/src/agent-designer/skills/<skill-name> ~/.claude/skills/<skill-name>
```

Project install, committed with the project and shared with teammates:

```bash
mkdir -p <project>/.claude/skills
cp -R ~/src/agent-designer/skills/<skill-name> <project>/.claude/skills/
rm -rf <project>/.claude/skills/<skill-name>/scripts/__pycache__
```

## 3. Approve

Bridge skills spawn another agent CLI. Under classifier-gated auto-approval, that long-running call pattern-matches as high risk and can be denied silently, so pre-authorize it. Add entries to the settings file matching your install scope: `~/.claude/settings.json` for global, `<project>/.claude/settings.json` for project.

```json
{
  "permissions": {
    "allow": [
      "Bash(python3 *collaborating-with-grok*bridge.py*)"
    ]
  },
  "sandbox": {
    "excludedCommands": [
      "python3 *collaborating-with-grok*bridge.py*"
    ]
  }
}
```

If the settings file already exists, merge these entries into it rather than replacing the file. Add one pair of entries per installed bridge skill, substituting the skill name in both patterns. The two halves do different jobs. The `permissions.allow` rule pre-approves the Bash call, and its wildcard form keeps matching wherever the skill is installed. The `sandbox.excludedCommands` entry matters on sandboxed hosts, where sandbox network policy blocks the child CLI's API traffic even after the command itself is allowed.

`issue-driven-workflow` runs local scripts only and needs no entries. An optional convenience rule is `"Bash(python3 *issue-driven-workflow/scripts/*)"`.

## 4. Verify

1. Confirm the install location:

   ```bash
   ls ~/.claude/skills/<skill-name>/SKILL.md
   ```

   Expected: the path prints with no error.

2. Start a new Claude Code session in any project and ask "what skills are available". Expected: the reply lists `<skill-name>`.

3. For a bridge skill, run its help check, for example:

   ```bash
   python3 ~/.claude/skills/collaborating-with-grok/scripts/grok_bridge.py --help
   ```

   Expected: a usage block starting with `usage: grok_bridge.py`, and no permission prompt when run from inside a session.

## 5. Update and uninstall

- Update a copied install by re-copying from a pulled clone. A symlinked install updates with `git pull` alone.
- Uninstall by deleting the skill directory and removing its entries from the settings file.

## What you can do now

- "Use collaborating-with-grok to search the web and X for reactions to `<topic>`, with cited source URLs."
- "Get a second opinion from Grok on this diff before I merge it."
- "Hand this bug to Codex for diagnosis and have it propose a unified diff."
- "Ask Codex to generate a 512x512 banner PNG for the README."
- "Ask antigravity to review `src/auth.py` and propose fixes as a unified diff."
- "Create a plan and issue CSV for `<goal>`, then execute it row by row."
