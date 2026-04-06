# Testing Policy

Consistent verification across tasks while allowing domain-specific methods.

## Required per issue

- Set `Test_Method` in the Issue CSV (command, tool, or "manual").
- Set `Tools` (or "manual"/"none") in the Issue CSV.
- If `Test_Method` is manual, add a short checklist in `Notes` or `Acceptance`.

## Default test layers

| Layer | Purpose |
|---|---|
| Unit | Fast checks on individual components |
| Integration | Real dependencies or realistic stubs |
| E2E / Acceptance | Critical user flows or end-to-end verification |
| Regression | Full suite or critical subset after batch completion |

## Minimum expectations by task type

| Task type | Required testing |
|---|---|
| Backend logic | Unit + Integration |
| API changes | Integration + contract verification |
| Frontend UI | UI/E2E (or manual checklist if no automation) |
| Data/schema | Migration test + rollback check |
| Performance-sensitive | Targeted perf check or benchmark |
| Research / analysis | Manual review of outputs against acceptance criteria |
| Content / documentation | Manual review or automated lint/link check |
| Infrastructure / config | Smoke test or dry-run verification |

## When automation is missing

- Use `Test_Method = manual`.
- Include a repeatable checklist (steps + expected outcome).
- Add a risk note in the plan if coverage is incomplete.

## Regression policy

- After all issues in a batch are DONE, run a regression pass.
- Failures must be fixed before marking `Regression_Status = DONE`.

## Command format (examples)

`pytest -q` · `npm test` · `pnpm test:e2e` · `go test ./...` · `manual: verify output matches spec`
