---
name: onepage-resume
description: Generate a one-page resume from user-provided content with strict fact preservation, section extraction, interactive inclusion confirmation, style selection, and print-ready HTML/PDF output. Use when a user asks to create, reformat, condense, polish, or export a resume into a single-page layout.
---

# Onepage Resume

Use this skill to produce recruiter-ready one-page resumes with minimal friction:
- Ask style by default (`stripe`, `compact`, `sidebar`).
- In the first reply, provide style preview link: `style-gallery.html`.
- Ask theme color for section bars/lines.
- If `sidebar` is selected, use one unified color for both left panel and section lines.
- Preserve user facts exactly (names, dates, company/school, metrics, titles).
- Condense wording only when needed to fit one page.
- Confirm optional sections before final render.

## Workflow

1. Collect source and style.
2. Extract and normalize resume data.
3. Build a draft content plan.
4. Ask inclusion confirmation for optional items.
5. Render one-page HTML.
6. Export PDF.
7. Run final quality checks.

## Step 1: Collect Source and Style

Ask for:
- Resume source text (free-form, Markdown, existing bullets, or mixed language).
- Style: `stripe`, `compact`, or `sidebar`.
- Accent color (hex), for example `#1f4e8c`.
- If style is `sidebar`, keep sidebar color unified with the selected accent color.
- Mention preview page before style confirmation:
  - `Open this file to compare styles: style-gallery.html`
  - This preview page is self-contained and should work directly without running scripts.
  - Do not rely on `outputs/*.html` file links in user-facing flows.

Default assumptions:
- Language: infer from source.
- Page size: A4 if user locale is unknown.
- Tone: neutral professional.

## Step 2: Extract and Normalize

Load extraction rules from [references/extraction-schema.md](references/extraction-schema.md).
If source is long or mixed with unrelated content, apply [references/long-source-selection.md](references/long-source-selection.md) before normalization.

Normalize into sections:
- `profile`: name, phone/email, location, links, short summary.
- `experience[]`: role, company, date range, location, bullets.
- `projects[]`: name, role, date range, bullets, stack.
- `education[]`: school, major, degree, date range, coursework, honors.
- `skills[]`: grouped technical and tools.
- `awards[]`: awards/scholarships/certifications.
- `additional`: languages, volunteering, publications.

Hard constraints:
- Never fabricate missing facts.
- Never alter factual numbers/dates/names.
- Keep original order when chronology is ambiguous.
- If multiple versions of the same experience exist, keep the most complete one and record which variant was dropped.

## Step 3: Draft One-Page Content Plan

Apply these density rules:
- Keep total output to one page at 10-11 pt body size.
- Keep each work experience to 3-5 bullets.
- Keep each project to 2-4 bullets.
- Limit summary to 2 lines.
- Prefer quantified bullets when available.

Apply safe condensation only:
- Merge repetitive bullets.
- Replace verbose phrases with shorter equivalents.
- Remove filler words.
- Preserve meaning and factual claims.

Never do:
- Reframe outcomes with stronger claims than source.
- Invent metrics or technologies.
- Change chronology.

## Step 4: Confirm Optional Sections

Run confirmation flow from [references/confirmation-checklist.md](references/confirmation-checklist.md).

Always ask user whether to include:
- Education honors.
- Coursework.
- Awards/certifications.
- Personal evaluation / self-summary paragraph.
- Additional info (languages, volunteering, publications).

If content is too long:
- Show exactly what was condensed or omitted.
- Ask for approval before final render.

## Step 5: Render One-Page HTML

Load layout constraints from [references/layout-rules.md](references/layout-rules.md).

Render priority:
1. Header (name + contacts + links)
2. Experience
3. Projects
4. Skills
5. Education
6. Optional sections confirmed by user

Style mapping:
- `stripe`: banner-style section labels with horizontal bars and optional icons.
- `compact`: dense minimalist style with lines and concise bullet hierarchy.
- `sidebar`: left-right layout with colored left panel and content area on the right.

Use the deterministic renderer when structured JSON is available:
- `python3 scripts/render_onepage_resume.py --input resume.json --output resume.html --style stripe`
- `python3 scripts/render_onepage_resume.py --input resume.json --output resume.html --style compact`
- `python3 scripts/render_onepage_resume.py --input resume.json --output resume.html --style sidebar`

Default theme colors:
- `stripe`: blue
- `compact`: black (highest-density style)
- `sidebar`: black (unified for left panel + section lines)

## Step 6: Export PDF

Prefer browser print pipeline:
- Open `resume.html` in Chromium.
- Print to PDF with background graphics enabled.
- Keep margins between 8 mm and 12 mm.
- Ensure single-page output.

Fallback:
- Reduce vertical gaps.
- Compress long bullets.
- Move optional section below fold only after user confirmation.

## Step 7: Final Quality Checks

Validate before delivery:
- Name/contact correctness.
- Date consistency (no overlaps unless explicit).
- No factual drift from user source.
- One-page print fit.
- Section headers and typography consistent.
- ATS readability (critical info stays in text, not icon-only).
- Line-break quality: avoid ragged short wrap lines (for example, a new line starting with only 1-2 Chinese characters). Condense or rephrase wording when needed.

Return:
- `resume.html` (editable source)
- `resume.pdf` (submission-ready)
- Brief note listing any condensed lines approved by user
