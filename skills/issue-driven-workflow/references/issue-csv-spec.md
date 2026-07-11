# Issue CSV Specification

The Issue CSV is the execution contract for each plan. It is machine-managed: create it with `create_issues.py`, update it with `update_issue.py`, and expect canonical quoting after any script write. Never string-edit the file.

## Required columns

All columns are required and must be populated:

| Column | Description |
|---|---|
| ID | Unique issue ID, letters then digits (A1, A2, ...) |
| Title | Short title |
| Description | Scope and boundary |
| Acceptance | Done criteria |
| Test_Method | How to verify (command, tool, or manual) |
| Tools | MCP tool in `server:tool` format, or `manual`/`none` |
| Dev_Status | TODO \| DOING \| DONE |
| Review_Status | TODO \| DOING \| DONE |
| Regression_Status | TODO \| DOING \| DONE |
| Files | Paths or scope (sentinel if none) |
| Dependencies | `none`, or pipe-separated row IDs |
| Notes | Extra context (`none` if none) |

## Status fields

- **Dev_Status**: implementation progress.
- **Review_Status**: verification after the issue is implemented.
- **Regression_Status**: verification after all issues are complete (full pass or smoke).

Values are always `TODO | DOING | DONE`, never percentages, never null.

The validator enforces status ordering: `Review_Status` past TODO requires `Dev_Status` DONE, and `Regression_Status` past TODO requires both. Only mark review or regression DONE after the declared `Test_Method` runs and passes, or record an explicit manual result with the risk noted.

## Dependencies

Use `none`, or a pipe-separated list of other row IDs such as `A1 | A2`. Every referenced ID must exist in the file. Self-references and cycles are rejected. Record external dependencies (deployed services, team decisions) in Notes, not here.

## Sentinel values

Use these when a field is required but not applicable:

| Field | Allowed sentinels |
|---|---|
| Files | `N/A` · `external` · `TBD` · `module:<name>` · `<glob>` |
| Dependencies | `none` |
| Notes | `none` |
| Tools | `manual` · `none` |

## Test_Method guidance

Every issue must specify how it will be verified. Use the narrowest reliable method, and match the method to the files the row touches:

- **Unit / Integration**: prefer if a test harness exists and the change is logic-heavy.
- **API / Contract**: for backend or service changes (curl or an HTTP client suite).
- **UI / E2E**: for frontend flows (Playwright or Chrome DevTools MCP).
- **Manual**: only if automation is impractical. Include the exact steps and set Tools to `manual` or `none`.

## Validation

`validate_issues_csv.py` reports every error in one run, with physical line numbers that stay accurate when quoted fields span multiple lines. It checks: header mismatches (naming the missing or unexpected columns), empty cells, status values, ID format and duplicates, dangling or cyclic dependencies, status ordering, and header-only files. A `manual` Test_Method combined with an automation tool in Tools produces a warning.

## CSV formatting

- The scripts write canonical quoting, where fields are quoted only when needed. A hand-authored file may be re-quoted once on its first script write.
- Use `|` inside a field to list multiple values.
- A UTF-8 BOM (added by Excel) is tolerated on read.

## Example rows

```csv
ID,Title,Description,Acceptance,Test_Method,Tools,Dev_Status,Review_Status,Regression_Status,Files,Dependencies,Notes
A1,Token validation,"Reject invalid, expired, and malformed tokens in /auth/login",Returns 401 with a structured error code,pytest tests/test_auth.py -k test_invalid_token,none,DONE,DONE,TODO,src/auth/login.py | src/auth/token.py,none,Phase 1
A2,Session persistence,Persist refreshed sessions in Redis,Session survives a server restart,pytest tests/test_auth.py -k test_session_persistence,none,DOING,TODO,TODO,src/auth/session.py,A1,Phase 1
A3,Dashboard loads after login,Dashboard renders for a signed-in user,Page shows the user profile within 3s,npx playwright test tests/dashboard.spec.ts,playwright:browser_navigate,TODO,TODO,TODO,src/pages/dashboard.tsx,A2,Phase 2
```

Note the coherence rules the examples model: pytest rows verify Python files, the Playwright row verifies a frontend page, and statuses vary legitimately (A1 implemented and reviewed, A2 in progress, A3 waiting on A2).
