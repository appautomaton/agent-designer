Language: 中文 | [English](README.md)

AGENT-DESIGNER（Codex Skills 工作区）
=====================================

目的
  设计并维护 Codex/Claude 风格的 SKILLs，同时维护相关文档与 MCP 工具目录。

如何开始一个新项目
0)（可选）将本仓库作为模板：clone 后删除 git 历史（`rm -rf .git`），再重新初始化（`git init`）。
1) 生成 docs/mcp-tools.md（mcp-tools-catalog）。
   - 原因：Codex 不一定会主动调用 MCP；把可用工具清单列出来，规划时更容易 "指哪打哪"。
   - 示例提示："根据启用的 MCP 服务器生成 docs/mcp-tools.md。"
2) 创建 AGENTS.md（agents-bootstrap）。
   - 原因：会根据项目要求把 "issues 驱动的开发工作流" 框架导入到 AGENTS.md 中。
   - 小提示：也可以先和 Codex 多轮对话明确方向，再让它 "bootstrap my AGENTS.md"。
3) 创建计划/Issue CSV（plan）。
   - 备注：本仓库提供了自定义 plan 技能（`.codex/skills/plan/`），会覆盖系统自带 plan。
   - 模板：`.codex/skills/plan/assets/_template.md` 与 `.codex/skills/plan/assets/_template.csv`。
   - 示例提示："为 <目标> 生成计划与 Issue CSV。"

关键文件
  - AGENTS.md（项目规则）
  - .codex/skills/（所有技能）
  - docs/SKILLs/agent-skills-standard.md（技能设计标准）
  - docs/mcp-tools.md（MCP 工具目录）
  - docs/testing-policy.md（测试默认规则）
  - issues/README.md（Issue CSV 格式）

常用操作
  - 生成/更新 MCP 工具目录：使用 mcp-tools-catalog
  - 生成新的 AGENTS.md：使用 agents-bootstrap
  - 与 Claude 协作：使用 collaborating-with-claude（通过 bridge 脚本；不要直接运行 `claude`）
  - 与 Gemini 协作：使用 collaborating-with-gemini（通过 bridge 脚本；不要直接运行 `gemini`）
  - 校验技能结构：参考 docs/SKILLs/agent-skills-standard.md

备注
  - 本仓库以文档与流程为主，大多数变更为文本修改。
  - 以官方文档作为主要信息来源。
  - 如需直接运行 bridge 脚本，优先使用 `python3`（部分系统不提供 `python` 命令）。
  - SKILL 编写最佳范式：在对话中引用 `docs/SKILLs/agent-skills-standard.md`（例如 "@docs/SKILLs/agent-skills-standard.md"）并迭代完善。
