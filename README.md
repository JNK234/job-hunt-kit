# job-hunt-kit

A Claude Code plugin for the whole job hunt: build master resumes from real job-description research, tailor them
per role, apply with answers that are checked before you submit, and run outreach that gets replies — all from plain
text files you own.

## Install

```
/plugin marketplace add JNK234/job-hunt-kit
/plugin install job-hunt-kit@job-hunt-kit
```
Local try-out: `claude --plugin-dir ./job-hunt-kit`.

## Start

```
/job-hunt-kit:setup            # creates ./job-hunt/ and builds your profile.md with you
/job-hunt-kit:build-resume     # audit your work, research JDs, write one master resume per target track
/job-hunt-kit:apply-job <url>  # fit check, tailored resume, drafted + judged answers, logged
```

## Skills

| Skill | What it does |
| --- | --- |
| `setup` | Creates the workspace and fills `profile.md` — the single source of truth for every claim |
| `build-resume` | Audits your experience, archives old resumes, picks tracks, writes dense one-page LaTeX masters |
| `analyze-jds` | Keyword frequency and requirement themes across many live job descriptions for a track |
| `tailor-resume` | Tailors a master to one JD, compiles it, reports the ATS keyword match |
| `apply-job` | Reads the exact form, scores fit, drafts answers, judges them, logs the application |
| `judge` | Gold-standard yes/no content check for emails and application answers, with a fix for every NO |
| `write-outreach` | Short, specific outreach emails and a 3-touch follow-up cadence |
| `find-people` | Finds the hiring manager or peer engineer and verifies their email |
| `job-pipeline` | Resumable sourcing → verification → drafting loop across many roles |

## Your workspace

```
job-hunt/
  profile.md  answer-bank.md  applications/  roles/  outreach/tracker.csv  resume/
```
Everything is plain text or LaTeX. Nothing is sent or submitted for you — the kit drafts; you send.

## Optional tools

All optional; each skill has a manual fallback.

- `tectonic` and poppler (`pdftotext`, `pdftoppm`) — compile resumes and check layout and ATS text
- `uv` — runs the judge script
- `TYPESAFE_API_KEY` — the judge uses TypeSafe's Jev for fast yes/no checks; without it Claude answers the same questions
- `gh` — GitHub activity audit
- Gmail MCP — save drafts and scan replies; chrome-devtools MCP — read live application forms and LinkedIn
- `HUNTER_API_KEY` / `APOLLO_API_KEY` in `job-hunt/.env` — verified email lookup

## Principles

- Every claim traces to `profile.md`. No invented numbers, employers, or "production" usage.
- Warm paths (referrals, intros) beat cold email; the kit looks for one first.
- On web forms the kit fills only the written answers; you upload files and answer the yes/no questions.

## License

MIT. Resume template based on [sb2nov/resume](https://github.com/sb2nov/resume).
