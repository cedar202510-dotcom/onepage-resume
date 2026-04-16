---
name: onepage-resume
description: |
  Generate a one-page resume from user-provided content with strict fact preservation,
  section extraction, interactive inclusion confirmation, style selection, and print-ready
  HTML/PDF output. Use when a user asks to create, reformat, condense, polish, or export
  a resume into a single-page layout.
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

## Step 1: Collect Source and Assert Requirements

- Check if the user has provided ANY resume content (whether via file upload, direct text paste, or previous interaction context).
- **If NO resume content is provided at all**, politely pause and ask them to provide it: "您好！开始为您生成/优化简历前，我需要您的素材支撑。您可以上传一份当前的简历文档（PDF/Word 等格式），或者把您的简历文本直接粘贴在这里。"
- **If source is provided**, warn about the avatar limitation: "正在为您整合提取信息。*提示：因系统与版面限制，我们将跳过原文档中的头像提取。稍后排版完成后，请您在工作台右侧直接手动上传证件照片，以获得最佳清晰度。*"
- Ask for their preferred Style (`stripe`, `compact`, or `sidebar`). You can provide the `style-gallery.html` link.

## Step 2: Extract and Normalize (Zero Deletion)

Load extraction rules from [references/extraction-schema.md](references/extraction-schema.md).

Normalize into sections:
- `profile`: name, phone/email, location, links, short summary.
- `experience[]`: role, company, date range, location, bullets.
- `projects[]`: name, role, date range, bullets, stack.
- `education[]`: school, major, degree, date range, coursework, honors.
- `skills[]`: grouped technical and tools.
- `awards[]`: awards/scholarships/certifications.
- `additional`: languages, volunteering, publications.

**CRITICAL CONSTRAINT**: You MUST extract ALL entries. NEVER fabricate facts, but also NEVER silently omit or summarize away any project or work experience the user uploaded. If they provided a new supplementary project, APPEND it completely to the array.

## Step 3: Present Full Outline and Ask for Confirmation

Do NOT render the final HTML yet.
You MUST present a "Full Module Checklist" to the user and let them decide what to keep.

- Show them exactly what you extracted. Example: "我已为您提取了完整的简历内容（共X段工作经历，Y段项目）。我们在后台未作任何删减。"
- Ask them: "由于单页（One-page）简历的篇幅极为受限，请问是否**确认所有经历全部保留**？如果篇幅过长，您希望将排版风格设为『极致紧凑』，还是愿意在此刻挑出几个早期不重要的项目让我进行删减合并？"

**Pause and wait for the user's decision.** Only proceed to rendering after they confirm.

## Step 4: Draft One-Page JSON and Condense (Only with Permission)

Based on the user's decision in Step 3, if they agreed to drop or condense certain items, do so safely.
- Keep each work experience to 3-5 bullets.
- Limit summary to 2 lines.

Export the finalized, confirmed data strictly as structured JSON (e.g., `resume.json`).

## Step 5: Render One-Page HTML (Mandatory Python Script)

CRITICAL: NEVER generate the HTML manually or try to write `.html` files directly via text generation, as this causes UI layout cross-contamination (e.g., "Core skills" breaking layout in dense mode).

You MUST use the deterministic renderer script:
1. Save the JSON from Step 4 to `resume.json`.
2. Run the generator: `python3 scripts/render_onepage_resume.py --input resume.json --output resume.html --style <chosen_style>`
3. Note to user: The generated `resume.html` contains built-in spacing and line-height sliders in the top right, allowing them to instantly adjust the compact/density feel.

## Step 6: Export PDF

Prefer browser print pipeline:
- Open `resume.html` in Chromium.
- Print to PDF with background graphics enabled.
- Ensure single-page output.

## Step 7: Final Delivery & Auto-Open

Validate before delivery:
- Name/contact correctness.
- Date consistency (no overlaps unless explicit).
- No factual drift from user source.
- One-page print fit.
- Section headers and typography consistent.
- ATS readability (critical info stays in text, not icon-only).
- Line-break quality: avoid ragged short wrap lines (for example, a new line starting with only 1-2 Chinese characters). Condense or rephrase wording when needed.

Delivery Actions:
1. You MUST run the terminal command `open resume.html` (or equivalent for the user's OS) to automatically pop open the generated file in their browser.
2. Tell the user you have automatically opened the preview for them.
3. Briefly list `.html` and `.pdf` generation status, and outline any condensed lines approved by the user.
