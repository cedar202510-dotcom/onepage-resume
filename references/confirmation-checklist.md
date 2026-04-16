# Confirmation Checklist

Run this checklist after initial extraction and before final render.

## Always Confirm

Present the FULL outline of extracted sections (all roles, projects, and experiences).
Ask the user explicitly:
- "是否确认保留以上所有的经历和项目？"
- "如果您认为篇幅过长，您希望删除或合并哪些部分？"

## If Page Is Too Long
Do not proactively delete content.
Only after the user explicitly points out which project or bullet to delete, you may remove it.

## User-Facing Delta Format

When content changes for fit, present short diff-style summary:

- `Experience / Company A / bullet 3`: "Led end-to-end..." -> "Led end-to-end launch..."
- `Education / Coursework`: kept top 3, removed 4 less relevant items

Use compact and transparent change notes so user can quickly approve.
