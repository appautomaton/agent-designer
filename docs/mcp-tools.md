# MCP Tools (Project)

Generated: 2025-12-23
Source: `codex mcp list --json` + runtime tool introspection

## Enabled servers
- context7
- shadcn

## Tools
- context7:resolve-library-id — Resolve a package/product name to a Context7-compatible library ID.
- context7:get-library-docs — Fetch up-to-date documentation for a library (requires resolve-library-id first unless an exact ID is provided).
- shadcn:get_add_command_for_items — Get the shadcn CLI add command for specific registry items.
- shadcn:get_audit_checklist — Get a checklist to verify newly created components/code are working.
- shadcn:get_item_examples_from_registries — Find usage examples/demos with complete code from registries.
- shadcn:get_project_registries — List configured registries from components.json.
- shadcn:list_items_in_registries — List items in registries (requires components.json).
- shadcn:search_items_in_registries — Fuzzy search components in registries.
- shadcn:view_items_in_registries — View details and file contents for registry items.
