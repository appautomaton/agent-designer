# Flaky Tests (Triage + Fix)

Flaky tests pass and fail without relevant code changes. Treat them as reliability bugs.

## Quick triage checklist
1) Re-run the same test(s) multiple times to confirm flakiness.
2) Run the test in isolation (single file / single test) to rule out ordering.
3) Vary execution order or disable parallelism to detect shared-state issues.
4) Increase logging/diagnostics to capture what differs between pass/fail.

## Common root causes
- Time dependence (real clock, time zones, DST, timeouts too tight)
- Concurrency/races (async work not awaited, eventual consistency)
- Shared mutable state (static singletons, global caches, shared DB/schema)
- Resource leakage (open handles/sockets/files), especially with parallel runs
- Environment coupling (ports, filesystem paths, locale, CPU speed)
- External dependencies (network calls, shared services)

## Fix patterns (prefer these over “rerun until green”)
- Replace sleeps with “wait-for condition” helpers and explicit timeouts.
- Inject/freeze time; seed randomness.
- Create per-test unique resources; clean up reliably.
- Make setup/teardown idempotent and explicit.
- Remove reliance on test ordering; reset globals between tests.

## Quarantine (last resort)
If fixing immediately is not possible:
- Quarantine the flaky test behind a tag/marker and run it in a separate CI lane.
- Record an issue with: reproduction steps, suspected cause, and owner.
- Do not silently ignore: quarantined tests should still run somewhere and be tracked to zero.

## What to record when reporting flakiness
- Exact command, environment, and seed/order settings
- Failure output and any captured diagnostics
- A hypothesis for root cause and the smallest next experiment
