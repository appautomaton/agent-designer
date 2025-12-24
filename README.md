Language: English | [中文](README.zh-CN.md)

AGENT-DESIGNER (Codex Skills Workspace)
======================================

Purpose
  Design and maintain Codex/Claude-style SKILLs, plus supporting docs and MCP tool catalog.

How to start a new project
0) (Optional) Use this repo as a template: clone it, remove the git history (`rm -rf .git`), then re-init (`git init`).
1) Generate docs/mcp-tools.md (mcp-tools-catalog).
   - Why: Codex may not proactively use MCP; having the full tool list makes planning easier.
   - Example prompt: "Generate docs/mcp-tools.md from enabled MCP servers."
2) Create AGENTS.md (agents-bootstrap).
   - Why: this imports an issues-driven dev workflow into AGENTS.md based on your project requirements.
   - Tip: you can also talk with Codex first to clarify scope, then ask it to "bootstrap my AGENTS.md".
3) Create plan/Issue CSV (plan).
   - Note: this repo ships a custom plan skill at `.codex/skills/plan/` (overrides the system plan skill).
   - Templates: `.codex/skills/plan/assets/_template.md` and `.codex/skills/plan/assets/_template.csv`.
   - Example prompt: "Create a plan and Issue CSV for <goal>."

Key files
  - AGENTS.md (project rules)
  - .codex/skills/ (all skills)
  - docs/SKILLs/agent-skills-standard.md (skill design standard)
  - docs/mcp-tools.md (MCP tools catalog)
  - docs/testing-policy.md (testing defaults)
  - issues/README.md (Issue CSV format)

Common actions
  - Regenerate MCP tools catalog: use the mcp-tools-catalog skill
  - Draft a new AGENTS.md: use the agents-bootstrap skill
  - Collaborate with Claude: use the collaborating-with-claude skill (bridge script; don't run `claude` directly)
  - Collaborate with Gemini: use the collaborating-with-gemini skill (bridge script; don't run `gemini` directly)
  - Validate skill structure: follow docs/SKILLs/agent-skills-standard.md

Notes
  - This repo is documentation- and workflow-first. Most changes are text.
  - Use official docs as the primary source of truth.
  - If invoking bridge scripts directly, prefer `python3` (some systems don't have `python`).
  - Skill authoring best-practice: reference `docs/SKILLs/agent-skills-standard.md` in chat (e.g., "@docs/SKILLs/agent-skills-standard.md") and iterate.

Acknowledgements
  - Initial inspiration:
    - https://github.com/anthropics/skills
    - https://github.com/GuDaStudio/skills
