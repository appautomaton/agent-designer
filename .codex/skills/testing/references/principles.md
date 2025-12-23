# Testing Principles (Framework-Agnostic)

Use these principles to write tests that increase confidence without slowing development.

## Reliability first
- Prefer deterministic tests: avoid real time, randomness without a seed, shared mutable globals, and external network calls.
- Make failures actionable: clear names, focused assertions, and useful error output.
- Keep tests isolated: each test can run alone and in any order.

## Choose the right layer
- **Unit tests** validate logic in isolation (fast, cheap, high signal).
- **Integration tests** validate boundaries between components and real dependency behavior (slower, higher realism).
- Avoid dogma: pick the layer that best catches the risk for this change.

## Test what you own; mock at boundaries
- Mock/stub external systems (network, DB, filesystem, clocks) at the edges of the unit under test.
- Avoid overspecifying implementation details (e.g., asserting internal calls) unless the behavior contract requires it.

## Make tests easy to read
- Use clear, behavior-oriented names: “when X, does Y”.
- Structure tests predictably (Arrange/Act/Assert or Given/When/Then).
- Prefer small, local fixtures and factories over large shared fixtures.

## Keep the feedback loop fast
- Default to running the smallest relevant subset locally.
- Separate slow tests (integration) from fast tests (unit) by convention/tags/paths.

## Be explicit about commands and policy
- Reuse the repository’s existing test commands and conventions.
- If the repo defines a testing policy (e.g., `docs/testing-policy.md`), follow it.
