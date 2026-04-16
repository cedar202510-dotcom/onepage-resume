# Long Source Selection

Use this when users provide long raw materials (portfolio notes, yearly reviews, multiple resume drafts, project docs).

## Goal

Select only one-page-relevant content while preserving factual accuracy.

## Step A: Segment the Source

Split source into chunks by headings, date lines, and blank-line blocks.

Common heading hints:
- Chinese: `个人信息`, `工作经历`, `项目经历`, `教育背景`, `技能`, `奖项`, `证书`, `自我评价`
- English: `Profile`, `Experience`, `Projects`, `Education`, `Skills`, `Awards`, `Certifications`, `Summary`

## Step B: Tag and Score Each Chunk

Assign one primary tag per chunk:
- `profile`
- `experience`
- `projects`
- `education`
- `skills`
- `awards`
- `additional`
- `irrelevant`

Use scoring to resolve duplicates:
- +3 contains explicit role/company/school/date
- +2 contains quantified outcomes (numbers, percentages, scale)
- +1 contains tools/tech stack details
- -2 generic narrative without concrete facts
- -3 irrelevant personal diary or non-career content

Keep highest-score chunk when duplicate statements exist.

## Step C: Build Candidate Resume

Build normalized JSON from kept chunks only.

If total content exceeds one-page limits:
- Keep most recent and highest-impact entries.
- Keep quantified bullets over descriptive-only bullets.
- Move low-signal content to optional pool.

## Step D: User Confirmation

Show a short selection report before final render:
- Which chunks were included
- Which chunks were excluded
- Why they were excluded (`duplicate`, `low-signal`, `irrelevant`, `page-limit`)

Require user approval before permanently dropping optional content.

## Non-Negotiable

- Never rewrite facts.
- Never infer missing metrics.
- Never merge two different roles into one role entry.
