---
description: Draft a plan from plan/_template.md and ask for confirmation
argument-hint: "<task description>"
---

You are in Plan mode.

Goal: draft a plan for $ARGUMENTS in the current repository using plan/_template.md.

Rules:
- Do not edit code or create plan files yet. Draft the plan in chat first.
- If $ARGUMENTS is empty or unclear, ask up to 2 clarifying questions, then proceed.
- Use plan/_template.md as the structure and fill every section.
- Choose complexity (simple|medium|complex).
- Set created_at to today's date (YYYY-MM-DD).
- Include an Issue CSV path that matches the plan timestamp/slug.

After drafting, ask for confirmation to write the plan file:
"Reply CONFIRM to write plan/<timestamp>-<slug>.md (and only then create the file)."

When confirmed:
1) Create plan/ if needed.
2) Write the plan file with naming pattern plan/YYYY-MM-DD_HH-mm-ss-<slug>.md.
3) Ensure Issue CSV path uses the same timestamp/slug.

Do not generate the Issue CSV unless the user asks.
