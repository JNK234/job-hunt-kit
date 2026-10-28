---
name: job-pipeline
description: Resumable job-application pipeline with persistent state - sources roles, live-verifies them through ATS public APIs (Ashby, Greenhouse, Lever), extracts exact form schemas, drafts submit-ready packages, and runs an honesty gate. Built to be driven repeatedly by /loop. Use when the user says "job loop", "source more roles", "draft the next batch", "what's in my pipeline", "keep applying", or sets a goal about applying to N jobs.
---

# Job pipeline

`/job-hunt-kit:apply-job` handles one application in depth. This skill handles batches with
memory: state persists in `roles/PIPELINE.json`, so each run continues where the last stopped
instead of re-sourcing roles that are dead, drafted, or already submitted.

## The one hard rule

Never click Submit. Never set a role to `submitted` on your own. Application forms carry legal
attestations (work authorization, EEO, "the contents are true") signed in the user's name. The
terminal state for your work is `drafted`. Only the user's own message ("I submitted X") moves a
role to `submitted`. State this once if asked, then continue with the work that is yours.

## Workspace

`$JOB_HUNT_HOME` if set, otherwise `./job-hunt/`. If `profile.md` is missing, tell the user to run
`/job-hunt-kit:setup` and stop.

- `profile.md` - the only source of facts about the user, including work authorization and location.
- `answer-bank.md` - reusable answers. Reuse before writing new prose.
- `applications/` - one record per application (written by apply-job Step 12).
- `roles/PIPELINE.json` - pipeline state. `roles/<company>-<role>.md` - submit-ready packages.

Helpers (Python 3 stdlib, no installs; each prints usage when run bare):

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/pipeline.py stats|status|next [n]|add ...|set <id> <k> <v>|verify
python3 ${CLAUDE_SKILL_DIR}/scripts/ats.py parse <url>|board <ats> <slug>|form <ats> <slug> <id>|alive <url>
python3 ${CLAUDE_SKILL_DIR}/scripts/gate.py roles/<file>.md
```

Run them from the directory that contains `job-hunt/`, or with `JOB_HUNT_HOME` set. Role id is
`<ats>:<slug>:<jobId>`; `add` skips duplicates. Status: `sourced -> verified -> drafted ->
submitted` (user only), or `dead` with a reason in `note`.

## Commands

| Say | Does |
|---|---|
| "what's in my pipeline" | `stats` + `next 10`, one line each |
| "source N more roles" | Step 2 for N roles (default 20) |
| "draft the next N" | Steps 4-7 for the top N `sourced`/`verified` roles (default 5) |
| "verify the pipeline" | Step 3 across every open role |
| "I submitted <company>" | `set <id> status submitted`, and set the application record to `Applied (YYYY-MM-DD)` |
| bare "job loop" | verify -> source if fewer than ~8 roles are queued -> draft 5 -> report |

The bare form is what `/loop 6h /job-hunt-kit:job-pipeline` should run. Filled browser tabs
expire (Ashby and Greenhouse do not save anonymous drafts), so the loop never fills forms; filling
happens only when the user sits down to submit.

## Step 1: Load state and profile

Run `pipeline.py stats` and `pipeline.py next 10`. Read `profile.md` and `answer-bank.md` once per
session. List companies in `applications/` whose status is past Drafting; never re-draft those.

From `profile.md`, pull: target role types, fit criteria, work authorization, sponsorship needs,
location rules, degree, and any companies the user has ruled out. If work authorization or
sponsorship is missing, ask before sourcing; it decides which roles are worth drafting.

## Step 2: Source (parallel subagents, disjoint segments)

Never web-search in the main context. Split the search into 4-8 non-overlapping segments derived
from the target roles in `profile.md` (for example by company type, stage, or domain) and give
each subagent one segment. Overlapping segments converge on the same companies.

Good feeds: company careers pages that link to Ashby/Greenhouse/Lever boards, curated boards for
the user's field (e.g. the 80,000 Hours board for AI safety, which tags visa status per listing),
YC's Work at a Startup, and boards of companies already in the pipeline. Boards are deep: once a
company fits, run `ats.py board <ats> <slug>` and read the whole list, not just the first hit.

Each subagent returns, per role: company, ATS + board slug, jobId, title, URL, the verbatim
sponsorship / work-authorization sentence (or "none stated"), the degree bar, and the seniority bar.
No slug means no schema, so require it.

Score fit 0-10 against `profile.md` only. Then register:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/pipeline.py add <ats> <slug> <jobId> "<Company>" "<Title>" "<url>" <fit> <yes|no|unknown>
```

The last argument is whether the employer sponsors visas in writing. `next` ranks
sponsorship-in-writing first, then fit. That ordering matters only if `profile.md` says the user
needs sponsorship; otherwise pass `unknown` for every role and fit drives the queue.

Flag, do not silently draft:
- **PhD required** when `profile.md` shows no PhD. Mark `dead` with note `phd-required`, unless the
  posting says "or equivalent experience"; then keep it and say so in the report.
- **No sponsorship** when `profile.md` says the user needs it. Read what is actually refused:
  "we cannot sponsor visas" can still allow work on existing authorization (some forms list
  e.g. OPT as an accepted option). Check the form's options before writing a company off, and
  record the time limit honestly.
- **US-person / export-control / clearance** requirements the user cannot meet truthfully. Read the
  option list, not the header; some only screen specific sanctioned countries.

Do not pad to hit a number. If only 8 roles are honest fits, register 8 and say why. Never inflate
a fit score to fill the count.

## Step 3: Verify live

HTTP status is useless on its own: Ashby serves a 200 shell for any path, and closed postings on
other ATSs often still return 200. Presence on the board listing is the real check.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/ats.py alive "<url>"        # LIVE | DEAD | UNKNOWN
python3 ${CLAUDE_SKILL_DIR}/scripts/pipeline.py verify          # every open role; marks DEAD as dead
```

`UNKNOWN` means the board was unreachable or empty; leave the role alone. Some Lever boards return
`[]` from the API while the page is live (client-rendered); read those in a browser before killing
them. A dead posting means that req closed, not that the company stopped hiring; re-source a
company after about a week.

**URL-parsing trap:** strip the query string and a trailing `/apply` or `/application` before
reading the jobId. Left on, the id never matches the board and live roles get marked dead.
`ats.py parse` does this; never hand-parse URLs.

## Step 4: Extract the EXACT form schema

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/ats.py form ashby      <slug> <jobPostingId>
python3 ${CLAUDE_SKILL_DIR}/scripts/ats.py form greenhouse <slug> <jobId>
python3 ${CLAUDE_SKILL_DIR}/scripts/ats.py form lever      <slug> <postingId>
```

Output: `REQUIRED|optional <TAB> type <TAB> verbatim title <TAB> options <TAB> flags`.

| ATS | Board endpoint | Form schema |
|---|---|---|
| Ashby | `GET https://api.ashbyhq.com/posting-api/job-board/<slug>` | `POST https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobPosting`, query `ApiJobPosting` -> `applicationForm.sections.fieldEntries { field isRequired }`. `field` is a JSON scalar; do not add a selection set. |
| Greenhouse | `GET https://boards-api.greenhouse.io/v1/boards/<slug>/jobs` | `GET .../jobs/<id>?questions=true` (includes select options) |
| Lever | `GET https://api.lever.co/v0/postings/<slug>?mode=json` | Not public. Custom questions are absent from the API; read the form live. |
| Workday, SmartRecruiters, Workable, iCIMS | - | No public schema. Workday needs a candidate login: flag as manual, never queue as drafted. |

For anything without a schema API, use chrome-devtools if installed (`new_page` on the apply URL,
then `take_snapshot`), else ask the user to paste the questions. Never guess fields.

JD silence is not form silence: a posting can say nothing about citizenship while the form has
required US-person questions. Always read the form. Then act on the `flags` column:
- `INVERTED-AUTH?` - read the sponsorship question literally. "Authorized to work *without*
  sponsorship?" and "*unrestricted* work authorization?" invert the usual answer for anyone on a
  temporary visa. Answer from `profile.md`, per form; never copy an answer between forms.
- `AI-TRAP-LEAVE-BLANK` - a decoy question addressed to an LLM. Leave it completely blank.
- `NO-AI-DRAFTING` - the employer asked for no AI help. Do not draft that field; give the user
  raw material from `profile.md` and leave the writing to them.
- `US-PERSON/EXPORT` - check whether the user can answer truthfully; if not, mark the role `dead`.

Save the schema into the package and `pipeline.py set <id> status verified`.

## Step 5: Resume check

Compare the JD's core with the user's resume masters in `resume/`. If the role centers on something
none of them leads with (infra vs research, frontend, data engineering, a domain with its own
vocabulary, staff-level scope), put a **RESUME MISMATCH** line in the package naming the gap and
the closest master, list it under "Needs a tailored resume" in the report, and offer
`/job-hunt-kit:tailor-resume`. A tailored resume reorders real work; it never adds skills.

## Step 6: Draft the package

Draft each role by running `/job-hunt-kit:apply-job` Steps 7 and 9-11 (answer bank, draft, judge, second
opinion) against the schema from Step 4. Skip apply-job's interactive fit stop and questions for
batch runs; instead put anything that needs the user under "Decisions for you" in the package.

For more than 3 roles, dispatch drafting subagents (3-5 roles each) in one message. They write
directly to `roles/<company>-<role>.md`; never have them return prose for you to re-type. Each
brief must carry the live field list, the path to `profile.md` with "every fact and number must
appear there", the work-authorization answers from `profile.md`, and the flags from Step 4. An
under-briefed drafter invents numbers; that is the main failure at volume.

Package layout:
1. **Header** - apply URL, ATS + slug + jobId, location, verbatim salary, verbatim sponsorship line,
   which resume to upload, interview process if stated.
2. **Live field list** - the Step 4 table with required flags and verbatim word/char limits.
3. **Answers** - `**Field N - <label>**` then a fenced block per field, within stated limits. Note
   when a form has no essay field (the resume and one link are then the whole pitch).
4. **Decisions for you** - salary, relocation, anything `profile.md` does not cover.
5. **Submit checklist** - upload resume, check sponsorship answers, remaining inputs.

Leave a field blank rather than fabricate it (a "favorite recent paper" the user never read, a tool
they never used). An unverifiable claim gets cut, not softened.

## Step 7: Gate

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/gate.py roles/<file>.md
```

It flags AI-slop phrasing, phrases listed under a "Banned" heading in `profile.md`, compliance
claims (HIPAA, SOC 2...) that `profile.md` never mentions, numbers in answer blocks that do not
appear in `profile.md`, and leftover TODO/TBD placeholders. Exit 1 means fix, or confirm each flag
is a false positive. It cannot tell whether an argument is good: every written answer must also
pass `/job-hunt-kit:judge` before the package counts as drafted.

Then `pipeline.py set <id> status drafted`, `set <id> file roles/<file>.md`, and log the application
via apply-job Step 12 (status `Drafting`, pointing at the package).

## Step 8: Report

Short: how many sourced, verified, drafted, and killed this run (with reasons), what was left blank
and why, and anything needing a decision. Never call a role submitted. End with the links list,
highest priority first, no prose between lines:

```
Apply links
1. <Company> - <Title> · <url>  [drafted, paste from roles/<file>.md]
2. <Company> - <Title> · <url>  [needs tailored resume]
3. <Company> - <Title> · <url>  [manual - Workday]
```

## Filling forms (only when the user is about to submit)

Fill in batches of 3-4 the user will submit in one sitting. Follow apply-job Step 13: free-text
fields only, user uploads first (Ashby uploads wipe filled text), and the user does yes/no,
location, consent, and Submit. On Ashby, check React state, not the DOM: a programmatic textarea
fill can look right and submit as "Missing entry". The committed value lives in `savedValue` on a
parent fiber (2-3 levels up from the textarea); if it is missing or short, set the value with the
native setter, fire `input` + `change` + blur, and re-check. Clicks register only on the foreground
tab, so `select_page` with `bringToFront` before clicking.

## Do not

- Submit, tick attestations, or mark `submitted` without the user's word.
- Write a fact or number that `profile.md` does not contain.
- Answer a sponsorship question by copying it from another form.
- Kill a role on an `UNKNOWN` check, or keep one that the board no longer lists.
- Queue a Workday or other login-walled role as drafted.
