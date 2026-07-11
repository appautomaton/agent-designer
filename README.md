Language: English | [中文](README.zh-CN.md)

# Agent Designer

A catalog of installable skills for AI coding agents: Claude Code, Codex, Antigravity, and Grok.

Structured, reusable skills that give your agents clear workflows, safe defaults, and multi-turn collaboration capabilities. Install the ones you want into the harness you already use, and your agents work methodically rather than freestyle.

## What's inside

**Collaboration skills** — let your agents delegate to each other via bridge scripts with session continuity:

| Skill | Purpose |
|---|---|
| `collaborating-with-claude` | Delegate to Claude Code CLI (review, diff, consultation) |
| `collaborating-with-antigravity` | Delegate to Antigravity CLI `agy` (review, web search, image analysis) |
| `collaborating-with-codex` | Delegate to Codex CLI (implementation, diagnosis, review, image generation) |
| `collaborating-with-grok` | Delegate to Grok CLI (review, diagnosis, live web/X search; coding model e.g. `grok-4.5`) |

**Issue-driven development** — structure work into plans and trackable Issue CSVs:

| Skill | Purpose |
|---|---|
| `issue-driven-workflow` | Plan → Issue CSV → autonomous execution with status tracking |

## Getting started

> [!TIP]
> 1) Pick the skills you want from `skills/`.
> 2) Follow the runbook for your harness in [`docs/setup/`](docs/setup/README.md): install, approve, verify.
>    - To add the issue-driven workflow to a project: ask your agent to "apply `AGENTS.issues.template.md` on top of `AGENTS.md`".
> 3) Start working. Ask your agent to create a plan, generate an Issue CSV, or collaborate with another agent.
>    - Example: "Create a plan and Issue CSV for <goal>."

## Project structure

```
skills/                          ← skill source (the real content)
  collaborating-with-claude/     ← bridge script + SKILL.md + references
  collaborating-with-antigravity/ ← bridge script + SKILL.md + references (agy; succeeds the retired Gemini CLI)
  collaborating-with-codex/      ← bridge script + SKILL.md + references + prompt recipes
  collaborating-with-grok/       ← bridge script + SKILL.md + references (Grok CLI; live web/X search)
  issue-driven-workflow/              ← plan/CSV workflow + templates + scripts
docs/setup/                      ← install runbooks per harness
AGENTS.md                        ← project-specific rules
AGENTS.issues.template.md        ← issue-driven workflow (apply on top of AGENTS.md)
```

## How it works

Each skill follows **progressive disclosure**:

- **Level 1 (metadata)** — `name` + `description` in YAML frontmatter. Always loaded. Used for discovery.
- **Level 2 (instructions)** — the SKILL.md body. Loaded when the skill is invoked. Contains workflow, safety, quick start.
- **Level 3 (resources)** — `scripts/`, `references/`, `assets/`. Loaded on demand. Contains deep docs, templates, helper scripts.

## Notes

- This repo is workflow-first — most changes are text, not code.
- Bridge scripts wrap CLI tools and return structured JSON with session continuity.
- Approval rules for the bridge scripts are documented per harness in [`docs/setup/`](docs/setup/README.md), in wildcard forms that work at any install location. See the "Host-side approval" section in each skill.
- Skills are portable across Codex and Claude Code with minimal adaptation.
- If invoking bridge scripts directly, prefer `python3`.

## Acknowledgements

Inspired by:
- [anthropics/skills](https://github.com/anthropics/skills)
- [GuDaStudio/skills](https://github.com/GuDaStudio/skills)
