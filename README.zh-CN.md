Language: 中文 | [English](README.md)

# Agent Designer

面向 AI 编程 Agent 的可安装技能目录：支持 Claude Code、Codex、Antigravity 和 Grok。

结构化、可复用的技能，让你的 Agent 拥有清晰的工作流程、安全的默认行为和多轮协作能力。挑选所需技能，安装到你已在使用的宿主环境中，让 Agent 有章可循地工作，而不是自由发挥。

## 包含内容

**协作技能** — 让 Agent 之间通过 bridge 脚本互相委托任务，支持会话连续性：

| 技能 | 用途 |
|---|---|
| `collaborating-with-claude` | 委托给 Claude Code CLI（评审、差异对比、咨询） |
| `collaborating-with-antigravity` | 委托给 Antigravity CLI `agy`（评审、网络搜索、图片分析） |
| `collaborating-with-codex` | 委托给 Codex CLI（实现、诊断、评审、图像生成） |
| `collaborating-with-grok` | 委托给 Grok CLI（评审、诊断、实时 Web/X 搜索；编码模型如 `grok-4.5`） |

**Issue 驱动开发** — 将工作结构化为计划和可追踪的 Issue CSV：

| 技能 | 用途 |
|---|---|
| `issue-driven-workflow` | 计划 → Issue CSV → 自主执行并跟踪状态 |

## 快速开始

> [!TIP]
> 1) 从 `skills/` 中挑选所需技能。
> 2) 按照 [`docs/setup/`](docs/setup/README.md) 中对应宿主的运行手册执行：安装、授权、验证。
>    - 如需在项目中使用 Issue 驱动工作流：让 Agent "将 `AGENTS.issues.template.md` 应用到 `AGENTS.md`"。
> 3) 开始工作。让 Agent 创建计划、生成 Issue CSV，或与其他 Agent 协作。
>    - 示例："为 <目标> 创建计划和 Issue CSV。"

## 项目结构

```
skills/                          ← 技能源码（核心内容）
  collaborating-with-claude/     ← bridge 脚本 + SKILL.md + 参考文档
  collaborating-with-antigravity/ ← bridge 脚本 + SKILL.md + 参考文档（agy；接替已停服的 Gemini CLI）
  collaborating-with-codex/      ← bridge 脚本 + SKILL.md + 参考文档 + 提示词模板
  collaborating-with-grok/       ← bridge 脚本 + SKILL.md + 参考文档（Grok CLI；实时 Web/X 搜索）
  issue-driven-workflow/              ← 计划/CSV 工作流 + 模板 + 脚本
docs/setup/                      ← 各宿主的安装运行手册
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
- bridge 脚本的授权规则按宿主记录在 [`docs/setup/`](docs/setup/README.md) 中，采用与安装位置无关的通配符形式。详见各技能的 "Host-side approval" 章节。
- 技能可在 Codex 和 Claude Code 之间移植，仅需少量适配。
- 如需直接运行 bridge 脚本，优先使用 `python3`。

## 致谢

灵感来源：
- [anthropics/skills](https://github.com/anthropics/skills)
- [GuDaStudio/skills](https://github.com/GuDaStudio/skills)
