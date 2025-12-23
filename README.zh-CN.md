Language: 中文 | [English](README.md)

AGENT-DESIGNER（Codex Skills 工作区）
=====================================

目的
  设计并维护 Codex/Claude 风格的 SKILLs，同时维护相关文档与 MCP 工具目录。

如何开始一个新项目
1) 生成 docs/mcp-tools.md（mcp-tools-catalog）。
   - 示例提示："根据启用的 MCP 服务器生成 docs/mcp-tools.md。"
2) 创建 AGENTS.md（agents-bootstrap）。
   - 示例提示："为本项目初始化 AGENTS.md，如有缺失信息请先提问。"
3) 创建计划/Issue CSV（plan）。
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
  - 与 Gemini 协作：直接说“work with Gemini CLI”，会在上下文中保留 SESSION_ID
  - 校验技能结构：参考 docs/SKILLs/agent-skills-standard.md

备注
  - 本仓库以文档与流程为主，大多数变更为文本修改。
  - 以官方文档作为主要信息来源。
