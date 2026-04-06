Language: 中文 | [English](README.md)

# Agent Designer

面向 AI 编程 Agent 的可移植技能工作区 — 支持 Codex、Claude Code 和 Gemini。

设计结构化、可复用的技能，让你的 Agent 拥有清晰的工作流程、安全的默认行为和多轮协作能力。克隆本仓库作为任何项目的起点，让 Agent 有章可循地工作，而不是自由发挥。

## 包含内容

**协作技能** — 让 Agent 之间通过 bridge 脚本互相委托任务，支持会话连续性：

| 技能 | 用途 |
|---|---|
| `collaborating-with-claude` | 委托给 Claude Code CLI（评审、差异对比、咨询） |
| `collaborating-with-gemini` | 委托给 Gemini CLI（评审、网络搜索、图片分析） |
| `collaborating-with-codex` | 委托给 Codex CLI（实现、诊断、评审） |

**Issue 驱动开发** — 将工作结构化为计划和可追踪的 Issue CSV：

| 技能 | 用途 |
|---|---|
| `issue-driven-dev` | 计划 → Issue CSV → 自主执行并跟踪状态 |

**标准与测试** — 如何编写技能和验证工作：

| 资源 | 用途 |
|---|---|
| `docs/SKILLs/agent-skills-standard.md` | 如何编写可移植的 `SKILL.md` 文件 |
| `skills/testing/` | 测试原则、模式和策略 |

## 快速开始

> [!TIP]
> 1)（可选）将本仓库作为模板：clone 后删除 git 历史（`rm -rf .git`），再重新初始化（`git init`）。
> 2) 编写 `AGENTS.md` — 项目角色、约束、技术栈、安全规则。
>    - 如需添加 Issue 驱动工作流：让 Agent "将 `AGENTS.issues.template.md` 应用到 `AGENTS.md`"。
> 3) 开始工作 — 让 Agent 创建计划、生成 Issue CSV，或与其他 Agent 协作。
>    - 示例："为 <目标> 创建计划和 Issue CSV。"

## 项目结构

```
skills/                          ← 技能源码（核心内容）
  collaborating-with-claude/     ← bridge 脚本 + SKILL.md + 参考文档
  collaborating-with-gemini/     ← bridge 脚本 + SKILL.md + 参考文档
  collaborating-with-codex/      ← bridge 脚本 + SKILL.md + 参考文档 + 提示词模板
  issue-driven-dev/              ← 计划/CSV 工作流 + 模板 + 脚本
  testing/                       ← 测试原则和模式
.codex/skills/                   ← 符号链接（Codex 接入层）
docs/SKILLs/                     ← 技能编写标准
AGENTS.md                        ← 项目专属规则
AGENTS.issues.template.md        ← Issue 驱动工作流（叠加到 AGENTS.md）
```

## 工作原理

每个技能遵循**渐进式披露**原则：

- **第一层（元数据）** — YAML frontmatter 中的 `name` + `description`。始终加载，用于技能发现。
- **第二层（指令）** — SKILL.md 正文。技能被调用时加载。包含工作流、安全规则、快速入门。
- **第三层（资源）** — `scripts/`、`references/`、`assets/`。按需加载。包含详细文档、模板、辅助脚本。

## 备注

- 本仓库以工作流为主 — 大多数变更为文本修改，而非代码。
- Bridge 脚本封装 CLI 工具，返回结构化 JSON 并支持会话连续性。
- 技能可在 Codex 和 Claude Code 之间移植，仅需少量适配。
- 如需直接运行 bridge 脚本，优先使用 `python3`。

## 致谢

灵感来源：
- [anthropics/skills](https://github.com/anthropics/skills)
- [GuDaStudio/skills](https://github.com/GuDaStudio/skills)
