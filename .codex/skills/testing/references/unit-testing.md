# Unit Testing

Unit tests verify small pieces of behavior (functions/classes/modules) in isolation.

## What to unit test
- Pure logic and transformations
- Validation and edge cases (empty/null, boundaries, invalid inputs)
- Error handling and exceptional paths
- Business rules and invariants

Avoid unit tests for behavior that is primarily “wiring” across multiple systems; that belongs in integration tests.

## Isolation and mocking
- Mock/stub at boundaries: network, DB, filesystem, clocks, randomness, process environment.
- Prefer fakes over heavy mocks when possible (simpler and less brittle).
- Avoid asserting internal call sequences unless it is part of the contract.

## Determinism checklist
- Control time (inject clock, freeze time, or use deterministic timestamps).
- Control randomness (inject RNG / seed).
- Remove sleeps; use deterministic inputs and explicit waits only in integration tests.
- Ensure no reliance on test ordering or global state.

## Test structure and readability
- Use a consistent structure (Arrange/Act/Assert or Given/When/Then).
- Name tests by behavior and outcome (“returns X when Y”).
- Keep fixtures small; prefer factories/builders over large shared fixtures.
- Write focused assertions: verify outcomes and externally visible effects.

## Coverage guidance (practical)
- Use coverage as a signal for missing risk areas, not as the sole goal.
- Prioritize high-risk paths: edge cases, error handling, security-sensitive logic.

## When tests are missing
If the repo lacks unit test infrastructure:
1) Propose the lightest-weight setup aligned with existing tooling.
2) Document the command(s) to run tests locally and in CI.
3) If automation is not feasible, produce a repeatable manual checklist per `docs/testing-policy.md`.
