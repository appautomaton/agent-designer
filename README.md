Language: English | [中文](README.zh-CN.md)

AGENT-DESIGNER (Codex Skills Workspace)
======================================

Purpose
  Design and maintain Codex/Claude-style SKILLs, plus supporting docs and MCP tool catalog.

How to start a new project
1) Generate docs/mcp-tools.md (mcp-tools-catalog).
   - Example prompt: "Generate docs/mcp-tools.md from enabled MCP servers."
2) Create AGENTS.md (agents-bootstrap).
   - Example prompt: "Bootstrap AGENTS.md for this project; ask for missing inputs."
3) Create plan/Issue CSV (plan).
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
  - Collaborate with Gemini: ask "work with Gemini CLI"; session IDs persist in context
  - Validate skill structure: follow docs/SKILLs/agent-skills-standard.md

Notes
  - This repo is documentation- and workflow-first. Most changes are text.
  - Use official docs as the primary source of truth.
