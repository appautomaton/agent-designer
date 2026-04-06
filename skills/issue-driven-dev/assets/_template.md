---
mode: plan
task: <short title>
created_at: <ISO8601 timestamp>
complexity: <simple|medium|complex>
---

<!-- Complexity guide:
  simple  — bug fix, small feature, config change (7 sections)
  medium  — multi-file feature, refactor, migration (9 sections)
  complex — cross-system change, new subsystem, risky migration (12 sections)
-->

# Plan: <short title>

## Goal
<!-- One clear sentence: what does "done" look like? -->
- Example: Users can log in with SSO and see their dashboard within 3 seconds.

## Scope
- In: <!-- what this plan covers -->
- Out: <!-- what is explicitly excluded -->

## Assumptions / Dependencies
<!-- External requirements, team decisions, or things that must be true -->
- Example: Auth service v2 API is deployed and stable.
- Example: Database migration for `users` table is already applied.

## Phases
<!-- Ordered steps. Each phase should be independently testable. -->
1. Phase 1 — <description>
2. Phase 2 — <description>

## Tests & Verification
<!-- Map each requirement to its test method. Use the narrowest reliable method. -->
- Login with valid token -> `pytest tests/test_auth.py -k test_valid_login`
- Login with expired token -> `pytest tests/test_auth.py -k test_expired_token`
- UI renders dashboard -> manual: open /dashboard, verify layout

## Issue CSV
- Path: issues/<YYYY-MM-DD_HH-mm-ss>-<slug>.csv
- Must share the same timestamp/slug as this plan.
- Column spec: `references/issue-csv-spec.md`

<!-- How the plan maps to CSV rows:
  Plan section        → CSV column
  ─────────────────────────────────
  Phases              → rows (each phase = one or more issue rows, e.g., Phase 1 → A1, A2)
  Scope: In           → Description
  Tests & Verification→ Test_Method
  Tools / MCP         → Tools (server:tool format)
  Acceptance Checklist→ Acceptance
  Assumptions / Deps  → Dependencies
  References          → Notes (or file paths in Files column)
-->

## Acceptance Checklist
<!-- Concrete, verifiable items. Each should be pass/fail. -->
- [ ] All tests pass
- [ ] No regressions in existing auth flow
- [ ] PR reviewed and approved

<!-- medium and complex plans: include the sections below -->

## Risks / Blockers
<!-- What could go wrong? What would delay this? -->
- Example: If auth service v2 is unstable, SSO login will fail intermittently.
- Example: No staging environment available for E2E testing.

## References
<!-- File paths with line numbers, docs, or external links -->
- src/auth/login.ts:42 — current token validation logic
- https://docs.example.com/auth-v2 — API spec

<!-- complex plans only: include the sections below -->

## Tools / MCP
<!-- MCP tools needed. Use server:tool format from your available tools. -->
- playwright:browser_navigate — E2E login flow testing
- context7:get-library-docs — check auth library API

## Rollback / Recovery
<!-- How to undo if something goes wrong -->
- Revert migration: `python manage.py migrate auth 0042`
- Feature flag: disable `SSO_ENABLED` in config

## Checkpoints
<!-- When to commit / create a reviewable unit -->
- Commit after: Phase 1 (backend auth changes)
- Commit after: Phase 2 (frontend integration)
- Tag: `v1.2.0-rc1` after all issues pass regression
