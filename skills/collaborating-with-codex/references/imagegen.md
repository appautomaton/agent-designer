# Image Generation via Codex (gpt-image-2)

Codex's built-in image generation runs **gpt-image-2** — a frontier image model, not a placeholder generator. It renders coherent in-image text, follows composition and style direction precisely, and has an agentic reasoning layer that interprets intent before generating. Treat it accordingly: **brief it like a senior art director briefs a designer**, delegate real asset work (icons, banners, diagrams, mockups, sprites, product shots), and expect quality worth iterating on.

Verified headless through the bridge (`--sandbox workspace-write`); the harness details are in [SKILL.md](../SKILL.md#images-input-and-generation).

## Delegation contract (the bridge prompt)

Give Codex the full frame in one prompt — what to make, where to save it, and how to prove it. `$imagegen` must survive the shell: single-quoted heredoc or `--prompt-file`.

```bash
PROMPT="$(cat <<'EOF'
Use $imagegen to create one asset.

BRIEF: App icon for a developer-facing log-analysis tool. Audience: engineers.
Flat geometric mark — a magnifying glass over three horizontal log lines —
two-color: deep indigo (#3D3D8F) on white. Centered, generous margins,
no gradients, no text, no border.

OUTPUT: 1024x1024 PNG saved as assets/icon.png in the workspace root.
Then reply with exactly: SAVED <path> <bytes> <dimensions>
EOF
)"
```

Always state: exact save path, exact size, the report-back contract. Codex handles generation, normalization, and saving; you verify the file exists and looks right before shipping it.

## Prompting the model

- **Brief, don't tag-soup.** State intent first — what the asset is for and who sees it — then scene → subject → key details → constraints. The model rewards clear purpose over keyword lists.
- **Subject early.** The opening words dominate composition; lead with the main subject, not the style.
- **Name the medium.** "Photorealistic photograph", "flat vector illustration", "watercolor", "3D render", "35mm film photo with subtle grain" — material and texture words steer style more reliably than adjectives like "beautiful".
- **Direct the camera.** Framing (close-up / wide / top-down), angle (eye-level / low-angle), lighting (soft diffuse / golden hour / high-contrast), and explicit placement ("logo top-right", "subject centered").
- **Constrain the negative space.** "No extra text. No watermark. No logos. Do not add new elements." — the model honors explicit exclusions; without them it decorates.

## Exact text in images (the signature strength)

- Put literal copy in **quotes** and demand it verbatim: `Include ONLY this text (verbatim): "Fresh and Clean"` — never ask for "a slogan" unless you want invented words.
- Specify typography: font character, weight, color, placement.
- Spell tricky brand names **letter-by-letter** for character accuracy.
- Use `quality high` (or at least medium) for small text, dense layouts, or multi-font work.
- Close with a hard stop: "Render this text exactly. No extra characters. No duplicate text."

## Parameters worth setting

| Parameter | Guidance |
|---|---|
| Size | `1024x1024` (square) · `1024x1536` (portrait) · `1536x1024` (landscape). Any size works if: edges multiples of 16, max edge <3840, ratio ≤3:1. Treat >2.5K outputs as experimental. |
| Quality | `low` = fast drafts · `medium` = default · `high` = small text, infographics, faces, identity-sensitive edits. |
| Background | Ask for a **transparent background** for icons/sprites needing alpha; `opaque` white for product extraction. |

## Edits and iteration

- **Edits:** attach the source via `--image` (repeatable). With multiple inputs, reference each by index and role: "Image 1: product photo. Image 2: style reference. Apply Image 2's style to Image 1."
- **Lock what must not change**, explicitly: "Do not change face, body shape, pose, or identity." Repeat the preserve-list on *every* iteration — drift compounds.
- **Iterate in small, single-change turns** over the same `SESSION_ID`: "make the lighting warmer", "remove the extra tree". Re-specify any critical detail the moment it drifts.

## Cost discipline

Image turns consume Codex usage limits ~3–5× faster than text turns (API pricing applies instead when `OPENAI_API_KEY` is set). Draft at `low`/`medium`, spend `high` only on finals — and batch related assets into one session so style context carries instead of being re-prompted.
