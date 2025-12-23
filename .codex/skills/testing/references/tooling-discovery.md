# Tooling Discovery

Goal: identify how this repo runs unit and integration tests, without guessing.

## 1) Prefer explicit repo guidance
Look for test commands and conventions in:
- Closest in-scope `AGENTS.md`
- `docs/testing-policy.md` (if present)
- `README.md`, `CONTRIBUTING.md`, `docs/`
- CI config (e.g., `.github/workflows`, `.gitlab-ci.yml`, `buildkite`, `circleci`, `azure-pipelines`)

If guidance exists, treat it as authoritative for commands, env vars, and required services.

## 2) Detect language and test runner signals
Use repo files to infer likely tooling (then confirm via docs/scripts):
- JavaScript/TypeScript: `package.json` scripts (`test`, `test:unit`, `test:integration`, `test:e2e`), lockfiles, `jest.*`, `vitest.*`, `playwright.config.*`, `cypress.*`
- Python: `pyproject.toml`, `pytest.ini`, `tox.ini`, `noxfile.py`, `requirements*.txt`
- Go: `go.mod`, `*_test.go`
- Rust: `Cargo.toml`, `tests/`, `src/**/mod.rs`
- .NET: `*.sln`, `*.csproj`, `Directory.Build.props`
- Java/Kotlin: `pom.xml`, `build.gradle*`, `settings.gradle*`
- Ruby: `Gemfile`, `spec/`
- PHP: `composer.json`, `phpunit.xml*`

## 3) Find existing “how to run tests” commands
Prefer existing entrypoints over raw runner calls:
- `Makefile` / `justfile` / `Taskfile.yml` / `scripts/` folder
- `package.json` scripts for JS/TS
- `tox`/`nox` for Python

Common “command patterns” to look for (do not assume they exist):
- Unit: `test`, `test:unit`, `unit`
- Integration: `test:integration`, `integration`, `it`, `verify`
- Coverage: `coverage`, `test:cov`

## 4) Determine how to run a subset
You need a “smallest relevant command” for tight iteration:
- By path (single file/package)
- By test name/pattern
- By tag/marker/category
- By affected package/module

If the repo has no documented subset mechanism, ask the user or propose the safest default: run unit tests only and add a manual checklist for integration verification.

## 5) Clarify only what blocks action
Ask focused questions like:
- “What’s the intended unit/integration runner command in this repo?”
- “Do integration tests require Docker or a local service?”
- “Are we expected to generate coverage/junit artifacts for CI?”

When the user can’t answer, proceed with explicit assumptions and a validation step (e.g., “I’ll scan CI config and `package.json`/`pyproject.toml` to infer the command.”).
