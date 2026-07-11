# Setup

Install skills from this repo into the agent harness you already use. Each skill is a self-contained directory holding a `SKILL.md` playbook plus `scripts/`, `references/`, and `assets/`. Pick the skills you want, place them where your harness discovers skills, and approve the bridge commands once.

## Runbooks

- [Claude Code](claude-code.md)
- [Codex CLI](codex.md)

Each runbook is written to be executed literally, by you or by your agent. Every step states the command to run and the result to expect.

## Which skills fit which host

| Skill | Claude Code host | Codex host |
|---|---|---|
| `collaborating-with-claude` | Skip. Claude delegating to Claude adds nothing. | Yes |
| `collaborating-with-codex` | Yes | Skip in most cases |
| `collaborating-with-grok` | Yes | Yes |
| `collaborating-with-antigravity` | Yes | Yes |
| `issue-driven-workflow` | Yes | Yes |

## Placement

A global install makes a skill available in every project. A project install lives inside one repo and travels with it to teammates.

| Host | Global | Project |
|---|---|---|
| Claude Code | `~/.claude/skills/<skill-name>` | `<project>/.claude/skills/<skill-name>` |
| Codex | `~/.codex/skills/<skill-name>` | `<project>/.codex/skills/<skill-name>` |

Grok CLI also discovers a project's `.claude/skills/`, so a Claude Code project install serves Grok hosts too. Dedicated Grok and Antigravity host runbooks are tracked in [BACKLOG.md](../../BACKLOG.md).
