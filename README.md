Language: English | [中文](README.zh-CN.md)

# Agent Designer

A portable skills workspace for AI coding agents — Codex, Claude Code, and Gemini.

Design structured, reusable skills that give your agents clear workflows, safe defaults, and multi-turn collaboration capabilities. Clone this repo as a starting point for any project where you want agents to work methodically rather than freestyle.

## What's inside

**Collaboration skills** — let your agents delegate to each other via bridge scripts with session continuity:

| Skill | Purpose |
|---|---|
| `collaborating-with-claude` | Delegate to Claude Code CLI (review, diff, consultation) |
| `collaborating-with-gemini` | Delegate to Gemini CLI (review, web search, image analysis) |
| `collaborating-with-codex` | Delegate to Codex CLI (implementation, diagnosis, review) |

**Issue-driven development** — structure work into plans and trackable Issue CSVs:

| Skill | Purpose |
|---|---|
| `issue-driven-dev` | Plan → Issue CSV → autonomous execution with status tracking |

**Testing** — how to verify work:

| Resource | Purpose |
|---|---|
| `skills/testing/` | Testing principles, patterns, and policies |

## Getting started

> [!TIP]
> 1) (Optional) Use this repo as a template: clone it, remove git history (`rm -rf .git`), re-init (`git init`).
> 2) Write your `AGENTS.md` — project role, constraints, stack, safety rules.
>    - To add issue-driven workflow: ask your agent to "apply `AGENTS.issues.template.md` on top of `AGENTS.md`".
> 3) Start working — ask your agent to create a plan, generate an Issue CSV, or collaborate with another agent.
>    - Example: "Create a plan and Issue CSV for <goal>."

## Project structure

```
skills/                          ← skill source (the real content)
  collaborating-with-claude/     ← bridge script + SKILL.md + references
  collaborating-with-gemini/     ← bridge script + SKILL.md + references
  collaborating-with-codex/      ← bridge script + SKILL.md + references + prompt recipes
  issue-driven-dev/              ← plan/CSV workflow + templates + scripts
  testing/                       ← testing principles and patterns
.codex/skills/                   ← symlinks (Codex wiring)
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
- Skills are portable across Codex and Claude Code with minimal adaptation.
- If invoking bridge scripts directly, prefer `python3`.

## Acknowledgements

Inspired by:
- [anthropics/skills](https://github.com/anthropics/skills)
- [GuDaStudio/skills](https://github.com/GuDaStudio/skills)
