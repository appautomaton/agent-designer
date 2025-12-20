# Issue CSV Rules

This repo uses Issue CSV as the execution contract for each plan.

## Required columns
All columns are required and must be populated:
- ID: unique issue ID (A1, A2, ...)
- Title: short title
- Description: scope/boundary
- Acceptance: done criteria
- Test_Method: how to verify (tool, command, or manual)
- Tools: MCP/tool to use (or "manual"/"none")
- Dev_Status: TODO | DOING | DONE
- Review1_Status: TODO | DOING | DONE
- Regression_Status: TODO | DOING | DONE
- Files: paths or scope (use a sentinel if none)
- Dependencies: other IDs or external deps (use "none" if none)
- Notes: extra context (use "none" if none)

## Sentinel values
Use these when a field is required but not applicable:
- Files: N/A | external | TBD | module:<name> | <glob>
- Dependencies: none
- Notes: none
- Tools: manual | none

## CSV formatting
- If a field contains commas, wrap the field in double quotes.
- Use "|" inside a field to list multiple values.

## Example row
ID,Title,Description,Acceptance,Test_Method,Tools,Dev_Status,Review1_Status,Regression_Status,Files,Dependencies,Notes
A1,Login error handling,"Handle invalid token in /auth/login","Returns 401 + error code","AUTOCURL mock token",AUTOCURL,TODO,TODO,TODO,"src/auth/login.ts | src/auth/token.ts",none,none
