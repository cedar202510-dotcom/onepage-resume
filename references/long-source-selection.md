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

## Step C: Build Full Candidate JSON

Build normalized JSON from ALL chunks.
DO NOT filter or drop any entries to fit a one-page limit. Extract everything.
If total content clearly exceeds one-page limits, flag this for the user in the next step, but **do not make the cut yourself**.

## Step D: User Confirmation (Zero Deletion Rule)

Show a complete Extraction Report before final render:
- List exactly what was extracted (all roles, all projects).
- Inform the user if the content is too long for one page.
- Ask them: "由于篇幅限制，请问是否确认保留所有经历，还是需要我为您删减某个早期的项目？"
- **Require user approval** before dropping or shortening ANY content.

## Non-Negotiable

- Never rewrite facts.
- Never infer missing metrics.
- Never merge two different roles into one role entry.
