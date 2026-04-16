# Layout Rules

Use these constraints to produce print-safe, one-page resume HTML.

## Page and Typography

- Support A4 and Letter through CSS `@page`.
- Use body font size 10-11 px equivalent (`pt` or `rem` print-safe).
- Keep line-height between 1.25 and 1.4.
- Keep left/right page margins between 8 mm and 12 mm.

## Section Order

1. Header
2. Experience
3. Projects
4. Skills
5. Education
6. Optional sections

## Header Rules

- Name is most prominent element.
- Contacts and links in a single compact row when possible.
- Never hide email/phone behind icon-only indicators.

## Bullet Rules

- Start with strong action verb.
- Prefer one-line bullets, max two lines.
- Keep punctuation style consistent.
- Avoid first-person pronouns.

## Style Tokens

Define CSS variables:

- `--text-primary`
- `--text-secondary`
- `--accent`
- `--rule`
- `--bg`

Suggested palettes:

- `classic`: grayscale accents only.
- `modern`: low-saturation blue/green accent only.
- `minimal`: near-monochrome with subtle separators.

## PDF Export Notes

- Avoid sticky/fixed elements.
- Avoid large box shadows and heavy gradients.
- Ensure print background enabled only if contrast stays strong.
