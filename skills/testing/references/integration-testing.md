# Integration Testing

Integration tests verify behavior across boundaries: modules/services, persistence, queues, HTTP APIs, or other real dependencies.

## When to use integration tests
- Changes to APIs, data schemas, persistence, or external service adapters
- “Wiring” logic that coordinates multiple components
- Risky boundaries: serialization, auth, permissions, migrations, caching, concurrency

## Make dependencies reproducible
Prefer hermetic or locally reproducible dependencies:
- Ephemeral databases/queues (e.g., containers) rather than shared dev instances
- Migrations applied from scratch in setup
- Deterministic seed data per test suite

If the repo relies on a shared environment, be explicit about prerequisites and add a repeatable manual fallback.

## Isolation and cleanup
- Each test run should not depend on prior runs.
- Use per-test (or per-suite) unique resources (DB/schema/usernames/paths).
- Always clean up: close connections, stop containers, remove temp files.

## Avoid common sources of flakiness
- Avoid static ports and globally named resources where possible.
- Avoid `sleep`-based timing; prefer “wait until condition” with timeouts.
- Capture diagnostics on failure (logs, response bodies, DB state snapshots) but keep secrets redacted.

## Contract boundaries (optional)
When appropriate, add contract-style checks:
- Consumer expectations for APIs and events
- Schema validation / backwards compatibility checks

## Running strategy
- Provide a “fast integration subset” for local iteration (single service, single suite).
- Keep a clear full-suite command for CI/regression.
