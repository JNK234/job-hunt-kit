---
name: setup
description: Create the job-hunt workspace and the user's profile — run first, before any other job-hunt-kit skill. Triggers on "set up job hunt", "start job search", "create my profile", or when another job-hunt-kit skill finds no profile.md.
---

# Setup

Creates the workspace every other skill reads and writes (layout in `${CLAUDE_PLUGIN_ROOT}/CONVENTIONS.md`).

## 1. Create the workspace

Use `$JOB_HUNT_HOME` if set, else `./job-hunt/`. Ask before creating it somewhere unexpected.

```bash
WS="${JOB_HUNT_HOME:-$PWD/job-hunt}"
mkdir -p "$WS"/{applications,roles,outreach/drafts,resume/tailored,resume/archive}
cp -n ${CLAUDE_PLUGIN_ROOT}/templates/workspace/profile.md "$WS/profile.md"
cp -n ${CLAUDE_PLUGIN_ROOT}/templates/workspace/answer-bank.md "$WS/answer-bank.md"
cp -n ${CLAUDE_PLUGIN_ROOT}/templates/workspace/tracker.csv "$WS/outreach/tracker.csv"
cp -n ${CLAUDE_PLUGIN_ROOT}/templates/resume/preamble.tex "$WS/resume/preamble.tex"
```

## 2. Fill profile.md with the user

`profile.md` is the single source of truth: every claim any skill writes must trace to it.

1. Ask for existing material first: resume files, LinkedIn export, GitHub handle, portfolio/blog URLs. Read them
   (pdftotext for PDFs; `gh repo list <handle>` for GitHub) and pre-fill the profile.
2. Then ask, with AskUserQuestion, only for what is missing: contact details, work authorization (and whether they
   need sponsorship now or later), location and relocation preferences, target roles, writing preferences
   (sign-off, phrases they hate).
3. For each role and project record: title, dates, what they built, for whom, stack, and verified numbers with
   where each number comes from. Mark anything unverified as such.
4. Show the filled profile and ask the user to correct it. Never invent facts.

## 3. Check tools (all optional)

Report which are available and what each unlocks; do not block on any:
- `tectonic` (LaTeX → PDF resumes), `pdftotext`/`pdftoppm` (poppler: ATS text and layout checks)
- `uv` (runs the judge script); `TYPESAFE_API_KEY` (fast Jev judging; otherwise Claude answers the questions)
- `gh` (GitHub audit); Gmail MCP (save drafts, scan replies); chrome-devtools MCP (read live forms, LinkedIn)
- `HUNTER_API_KEY` / `APOLLO_API_KEY` in `$WS/.env` (verified emails for find-people)

## Next

Suggest `/job-hunt-kit:build-resume` to build master resumes, then `/job-hunt-kit:apply-job <url>`.
