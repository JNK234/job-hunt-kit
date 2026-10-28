---
name: apply-job
description: End-to-end job application workflow - fetch the posting and its exact form fields, research the company, score fit, draft and judge every answer, log the application. Use when the user says "apply to this job", "help me apply to [company]", "fill this application", "draft my application for [URL]", "assess fit for [URL]", "should I apply to [company]", or shares a job posting URL and wants help applying.
---

# Apply to a job

Pipeline: load profile -> fetch JD + exact form -> research company -> history check -> fit (STOP) ->
questions -> answer bank -> tailor resume -> draft -> judge -> second opinion -> log -> mark applied.

Run the steps in order. Do not draft anything before the user approves the fit assessment (Step 5).
You never submit the application. You draft, and optionally fill text fields; the user submits.

## Workspace

`$JOB_HUNT_HOME` if set, otherwise `./job-hunt/`. If it does not exist, tell the user to run
`/job-hunt-kit:setup` first and stop.

- `profile.md` - every fact about the user. Contact, work authorization, location prefs, roles, numbers.
- `answer-bank.md` - reusable answers, each with source + best-for.
- `applications/NNN-company-role.md` - one file per application (format: `${CLAUDE_SKILL_DIR}/references/log-template.md`).
- `outreach/tracker.csv` - people already contacted.

## Step 1: Load profile

Read `profile.md` and `answer-bank.md` in full. Every claim you later write must trace to `profile.md`.
Work authorization, sponsorship, location, and relocation answers come only from `profile.md`. If it
does not cover something the form asks, ask the user. Never infer it.

## Step 2: Fetch the JD and the EXACT form fields

Extract: company, role, location, salary, must-haves vs nice-to-haves, responsibilities, team
context, and every form field verbatim (label, type, required flag, options, word/char limits).
Never guess form fields. "JD silence is not form silence": a posting can say nothing about
citizenship while the form has required questions about it.

Try the ATS public APIs first when the URL matches. Strip trailing `/apply` or `/application` from
the URL before parsing the job id, or the id will not match.

- **Ashby** (`jobs.ashbyhq.com/<org>/<id>`). Board: `GET https://api.ashbyhq.com/posting-api/job-board/<org>`.
  Form: POST to `https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobPosting` with
  ```json
  {"operationName":"ApiJobPosting",
   "variables":{"organizationHostedJobsPageName":"<org>","jobPostingId":"<id>"},
   "query":"query ApiJobPosting($organizationHostedJobsPageName: String!, $jobPostingId: String!) { jobPosting(organizationHostedJobsPageName: $organizationHostedJobsPageName, jobPostingId: $jobPostingId) { title applicationForm { sections { fieldEntries { field isRequired } } } } }"}
  ```
  `field` is a JSON scalar; do not add a selection set to it. `jobPosting: null` means closed or wrong id.
- **Greenhouse** (`boards.greenhouse.io/<org>/jobs/<id>` or `job-boards.greenhouse.io/...`):
  `GET https://boards-api.greenhouse.io/v1/boards/<org>/jobs/<id>?questions=true`.
- **Lever** (`jobs.lever.co/<org>/<id>`): `GET https://api.lever.co/v0/postings/<org>?mode=json` gives
  the JD, but Lever does NOT expose custom questions publicly. Always read Lever forms live (below).

HTTP 200 does not mean the role is open. Closed postings often still serve 200; presence on the
board listing is the real check.

Otherwise, escalate in this order until you have the real content:
1. WebFetch. Fast, but JS-rendered pages (Ashby, Airtable, many careers sites) return only the title.
2. A web-reader MCP, if one is installed. Handles many JS pages.
3. chrome-devtools MCP, if installed: `new_page` with the URL, then `take_snapshot` to read the live
   accessibility tree (every question, option, and limit verbatim). Use a fresh page each time.
4. Ask the user to paste the JD and the form questions.

## Step 3: Research the company (subagent)

Dispatch a subagent; never run web searches in the main context. Ask it for 8-12 bullets: product
and technology, funding and stage, team size and leadership, news from the last 6 months, stated
values and hiring signals, the team this role sits on, and links to the user's domains in `profile.md`.

## Step 4: Pre-flight history check

Before scoring, search `applications/` and `outreach/tracker.csv` for this company. Report in one
or two lines: earlier applications and their status, rejections (with dates and any stated reason),
people already contacted, and follow-ups due. A recent rejection for the same role or team changes
the plan; say so plainly and let the user decide.

## Step 5: Assess fit (STOP)

Score each requirement against `profile.md`:
- STRONG: direct, recent, evidenced experience.
- MODERATE: related experience, transferable skill.
- WEAK: no direct experience.

Must-have: STRONG 3, MODERATE 2, WEAK 1. Nice-to-have: STRONG 2, MODERATE 1, WEAK 0.
Fit % = points / max points x 100. 70%+ proceed; 50-69% borderline; under 50% weak. Give the honest
read at every level, and let the user decide.

Find the employer's #1 criterion: what the JD repeats, lists first, or calls "required". If the user
is MODERATE or WEAK on it, say so even when the overall percentage looks good. A 75% score can
still flatter the candidate if the one gap is the thing they hire for.

Show the table, the percentage, and the #1-criterion read. **Stop and wait for the user's decision.**

## Step 6: Targeted questions

Use the AskUserQuestion tool; never list questions inline. Ask 2-3 questions about this role:
what genuinely draws them to this company or problem, any experience not yet in `profile.md`
that strengthens fit, and how to frame the WEAK rows. Add new facts the user confirms to `profile.md`.

## Step 7: Reuse the answer bank

For each form question, check `answer-bank.md` first and adapt any close match. If an answer
earned an interview before (noted in its source), fix only the grammar and the company-specific
parts. Keep its substance.

## Step 8: Tailor the resume (if the form has a resume upload)

Run `/job-hunt-kit:tailor-resume` with the JD already loaded. Note its ATS keyword match rate
next to the fit score. If the match is under 60%, or far from the fit score, warn the user before
going on.

## Step 9: Draft answers

- Every claim traces to `profile.md`. Never invent metrics, employers, deployments, or "production"
  use. Never claim compliance work (HIPAA, SOC2, ...) unless `profile.md` says it was done.
  Interview or take-home work is described by what was built, not as employment.
- Answer what the question actually asks. Use the user's work as evidence for their view, not as
  a substitute for it.
- Lead with the experience most relevant to this role. Use concrete systems and numbers.
- Carry real motivation from Step 6, with no filler enthusiasm ("passionate", "excited to").
- Respect stated word/char limits exactly; they are part of the evaluation.
- Apply the voice and banned phrases in `profile.md`.
- Short-answer fields (links, yes/no, sponsorship) come from `profile.md`; mark any gap `ASK USER`.

## Step 10: Judge every written answer

Run `/job-hunt-kit:judge --kind answer` on each free-text answer. Revise on every NO using its fix,
and re-judge until READY. Stop after 3 rounds and show the user what is still failing. If a NO is
a judge miss (the answer already does what it asks, or the fix would need an invented fact),
tell the user which check and why. Do not bend the answer to pass.

## Step 11: Second-opinion critique (optional, for essays)

Ask a different model if one is available (e.g. via an MCP), otherwise a fresh subagent with no
prior context. Brief it as a senior hiring manager at the company: top JD requirements plus the
drafts. Ask it to check impact and ownership, evidence, filler, missing domain concepts, and to
score each answer 1-10 with line-level rewrites. Apply only truthful fixes. Reject anything
that adds experience not in `profile.md`. Re-run Step 10 on any answer that changed.

## Step 12: Log the application

Next number = count of files in `applications/` + 1, zero-padded to 3 (`007`). Write
`applications/NNN-<company>-<role>.md` (lowercase, hyphenated) using
`${CLAUDE_SKILL_DIR}/references/log-template.md`, with status `Drafting`. Never renumber
existing files.

If an answer is reusable (why-this-field, proudest work, hardest problem...), append it to
`answer-bank.md` with question, source application file, best-for, and the full text.

## Step 13: Fill the form (only if asked) and mark applied

If the user asks you to fill the form via chrome-devtools: fill only free-text answer fields.
The user does uploads, yes/no, location, dropdowns, consent, and Submit. On Ashby, file uploads
wipe text that is already filled, so the user uploads first. Ashby also checks React state, not the
DOM: a programmatic textarea fill can show on screen and still submit as "Missing entry". After
filling, check that each textarea's value took (type into it, or fire `input` + `change` + blur),
and tell the user to read every field before submitting.

When the user confirms they submitted, set status to `Applied (YYYY-MM-DD)` in the application
file. Suggest `/job-hunt-kit:find-people` for team outreach if it is installed.

## Do not

- Draft before the fit approval, or ask questions as inline text.
- Write a claim that `profile.md` does not support.
- Show an answer as final before it passes the judge (or the user accepts a flagged judge miss).
- Submit, send, or tick consent/attestation boxes for the user.
- Turn one application's feedback into a rule for all of them.
- Paste long drafts into chat; they go in the application file, and chat gets a short summary.
