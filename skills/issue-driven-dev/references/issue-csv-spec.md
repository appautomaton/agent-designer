# Issue CSV Specification

This repo uses Issue CSV as the execution contract for each plan.

## Required columns

All columns are required and must be populated:

| Column | Description |
|---|---|
| ID | Unique issue ID (A1, A2, ...) |
| Title | Short title |
| Description | Scope/boundary |
| Acceptance | Done criteria |
| Test_Method | How to verify (tool, command, or manual) |
| Tools | MCP/tool to use (`server:tool` format) or "manual"/"none" |
| Dev_Status | TODO \| DOING \| DONE |
| Review1_Status | TODO \| DOING \| DONE |
| Regression_Status | TODO \| DOING \| DONE |
| Files | Paths or scope (use a sentinel if none) |
| Dependencies | Other IDs or external deps (use "none" if none) |
| Notes | Extra context (use "none" if none) |

## Status fields

- **Dev_Status**: implementation progress.
- **Review1_Status**: verification after the issue is implemented.
- **Regression_Status**: verification after all issues are complete (full pass/smoke).

Values are always `TODO | DOING | DONE` — never percentages, never null.

Only mark Review1/Regression as DONE after the declared Test_Method runs and passes, or if manual/not feasible is explicitly recorded with risk noted.

## Sentinel values

Use these when a field is required but not applicable:

| Field | Allowed sentinels |
|---|---|
| Files | `N/A` · `external` · `TBD` · `module:<name>` · `<glob>` |
| Dependencies | `none` |
| Notes | `none` |
| Tools | `manual` · `none` |

## Test_Method guidance

Every issue must specify how it will be verified. Use the narrowest reliable method:

- **Unit / Integration**: prefer if a test harness exists and the change is logic-heavy.
- **API / Contract**: for backend or service changes (e.g., curl, Postman, AUTOCURL).
- **UI / E2E**: for frontend flows (e.g., Playwright or Chrome DevTools MCP).
- **Manual**: only if automation is impractical; include the exact steps.

## CSV formatting

- If a field contains commas, wrap the field in double quotes.
- Use `|` inside a field to list multiple values.

## Example rows

```csv
ID,Title,Description,Acceptance,Test_Method,Tools,Dev_Status,Review1_Status,Regression_Status,Files,Dependencies,Notes
A1,Backend token validation,"Handle invalid/expired tokens in /auth/login","Returns 401 with structured error code","pytest tests/test_auth.py -k test_invalid_token",none,TODO,TODO,TODO,"src/auth/login.ts | src/auth/token.ts",none,"Phase 1"
A2,SSO provider integration,"Integrate SSO provider OAuth flow","User redirected to SSO and returned with valid session","pytest tests/test_auth.py -k test_sso_flow",none,TODO,TODO,TODO,"src/auth/sso.ts | src/auth/session.ts",A1,"Phase 1"
A3,Dashboard renders after SSO,"Dashboard loads within 3s after SSO login","Page renders with user profile and data","manual: login via SSO then open /dashboard",playwright:browser_navigate,TODO,TODO,TODO,"src/pages/dashboard.tsx",A2,"Phase 2"
```
