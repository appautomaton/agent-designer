# MCP Tools (Project)

Generated: 2025-12-20
Source: `codex mcp list --json` + runtime tool definitions

## Enabled servers
- chrome-devtools
- context7
- playwright
- shadcn

## Tools
- chrome-devtools:click — Click an element by uid in the selected page.
- chrome-devtools:close_page — Close a browser page by index.
- chrome-devtools:drag — Drag one element onto another.
- chrome-devtools:emulate — Emulate CPU/network/geolocation settings.
- chrome-devtools:evaluate_script — Execute JavaScript in the page context.
- chrome-devtools:fill — Fill a single input/textarea/select element.
- chrome-devtools:fill_form — Fill multiple form fields at once.
- chrome-devtools:get_console_message — Fetch a console message by id.
- chrome-devtools:get_network_request — Fetch a network request by id.
- chrome-devtools:handle_dialog — Accept or dismiss a browser dialog.
- chrome-devtools:hover — Hover over an element.
- chrome-devtools:list_console_messages — List console messages for the page.
- chrome-devtools:list_network_requests — List network requests for the page.
- chrome-devtools:list_pages — List open pages/tabs.
- chrome-devtools:navigate_page — Navigate/reload/back/forward on a page.
- chrome-devtools:new_page — Open a new page with a URL.
- chrome-devtools:performance_analyze_insight — Analyze a specific performance insight.
- chrome-devtools:performance_start_trace — Start a performance trace.
- chrome-devtools:performance_stop_trace — Stop the active performance trace.
- chrome-devtools:press_key — Send a key or key combo to the page.
- chrome-devtools:resize_page — Resize the browser window.
- chrome-devtools:select_page — Select a page by index for future actions.
- chrome-devtools:take_screenshot — Capture a page or element screenshot.
- chrome-devtools:take_snapshot — Capture an accessibility snapshot.
- chrome-devtools:upload_file — Upload a file via a file input.
- chrome-devtools:wait_for — Wait for text to appear on the page.

- context7:get-library-docs — Fetch up-to-date documentation for a library.
- context7:resolve-library-id — Resolve a library/package name to a Context7 ID.

- playwright:browser_click — Click an element.
- playwright:browser_close — Close the current page.
- playwright:browser_console_messages — Get console messages.
- playwright:browser_drag — Drag and drop between elements.
- playwright:browser_evaluate — Execute JavaScript in the page.
- playwright:browser_file_upload — Upload one or more files.
- playwright:browser_fill_form — Fill multiple fields at once.
- playwright:browser_handle_dialog — Accept/dismiss a dialog.
- playwright:browser_hover — Hover over an element.
- playwright:browser_install — Install the Playwright browser runtime.
- playwright:browser_navigate — Navigate to a URL.
- playwright:browser_navigate_back — Go back in history.
- playwright:browser_network_requests — List network requests.
- playwright:browser_press_key — Press a keyboard key.
- playwright:browser_resize — Resize the browser window.
- playwright:browser_run_code — Run a Playwright code snippet.
- playwright:browser_select_option — Select an option in a dropdown.
- playwright:browser_snapshot — Capture an accessibility snapshot.
- playwright:browser_tabs — List/create/close/select tabs.
- playwright:browser_take_screenshot — Take a screenshot.
- playwright:browser_type — Type text into an element.
- playwright:browser_wait_for — Wait for text or a timeout.

- shadcn:get_add_command_for_items — Get the CLI add command for components.
- shadcn:get_audit_checklist — Get a shadcn audit checklist.
- shadcn:get_item_examples_from_registries — Fetch usage examples for items.
- shadcn:get_project_registries — Read configured registries from components.json.
- shadcn:list_items_in_registries — List items in registries.
- shadcn:search_items_in_registries — Search items in registries.
- shadcn:view_items_in_registries — View details/files for specific items.
