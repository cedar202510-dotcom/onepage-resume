# Extraction Schema

Use this schema to normalize user source text before layout.

## Field Rules

- Preserve all factual text values exactly when possible.
- Keep style choices independent from factual extraction.
- Keep unknown values as empty string (`""`) or empty list (`[]`).
- Normalize date format to `YYYY.MM` when source is clear; otherwise keep original string.
- Keep language as provided by user; do not force translation.

## JSON Shape

```json
{
  "style": "stripe",
  "style_config": {
    "accent_color": "#1f4e8c",
    "sidebar_bg_color": "#1f1f1f"
  },
  "profile": {
    "name": "",
    "title": "",
    "phone": "",
    "email": "",
    "location": "",
    "links": [],
    "summary": "",
    "photo_url": ""
  },
  "experience": [
    {
      "company": "",
      "role": "",
      "location": "",
      "start_date": "",
      "end_date": "",
      "bullets": []
    }
  ],
  "projects": [
    {
      "name": "",
      "role": "",
      "start_date": "",
      "end_date": "",
      "stack": [],
      "bullets": []
    }
  ],
  "education": [
    {
      "school": "",
      "degree": "",
      "major": "",
      "start_date": "",
      "end_date": "",
      "coursework": [],
      "honors": []
    }
  ],
  "skills": [
    {
      "group": "",
      "items": []
    }
  ],
  "awards": [],
  "additional": {
    "languages": [],
    "volunteering": [],
    "publications": []
  }
}
```

## Extraction Priorities

1. Extract identity and contact fields first.
2. Extract work/project/education with date ranges.
3. Extract bullet details with outcomes and metrics.
4. Extract optional sections only if present.
5. For long input, keep only chunks that pass the selection process in `long-source-selection.md`.

## Safe Condensation Rules

- Prefer shortenings like "Responsible for X and Y" -> "Owned X, Y".
- Merge repeated tooling details across bullets.
- Keep numbers and nouns untouched.
- Keep action-result structure when possible.

## Non-Negotiable Constraints

- Do not invent employers/schools/projects.
- Do not change numerical results.
- Do not infer certifications/awards without explicit source.
- Keep a short trace note of source origin when there are duplicate or conflicting inputs.
