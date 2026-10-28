---
name: analyze-jds
description: Analyze 50-150 job descriptions for one target track to find what employers actually ask for. Use when the user says "analyze JDs for [track]", "what do research engineer postings want", "keyword analysis for my resume", "which skills should my resume lead with", "analyze-jds [track]", or when /job-hunt-kit:build-resume reaches its JD step. Outputs keyword frequencies, rising terms, top themes, a KEEP/CUT map of the user's inventory, ordered skills lines, and honest gaps to resume/jd-analysis-<track>-<date>.md.
---

# Analyze JDs

Turn a pile of real postings for one track into resume decisions: what to lead with, what to cut, which skills lines to write, and which gaps not to fake.

Workspace: `$JOB_HUNT_HOME` if set, else `./job-hunt/`. Paths below are relative to it.

Input: a track name (e.g. "Research Engineer", "AI Engineer"). If none is given, ask in one line.
Output: `resume/jd-analysis-<track-slug>-<YYYY-MM-DD>.md`, plus raw data under `resume/jd-corpus/<track-slug>/`.

## Step 1: Scope (main thread, quick)

1. Read `profile.md` and `resume/inventory.md` if it exists (from `/job-hunt-kit:build-resume`). This is the user's inventory.
2. Confirm in one message: track name, title variants to include (e.g. "Research Engineer", "Member of Technical Staff - Research", "ML Research Engineer"), seniority, and any company list the user wants included. Use sensible defaults if they say "just go".

## Step 2: Gather the corpus (one subagent)

Hand the gathering to one subagent so JD text stays out of the main context. Tell it to write files to disk and return only counts and the file list.

Sources, in order:
1. **The user's `roles/` folder**: every saved JD. Keep only ones matching the track.
2. **ATS public APIs** (no key needed) for companies that hire this track. Build the company list from `roles/`, `applications/`, and the user's list, then add well-known employers for the track.
   - Ashby: `https://api.ashbyhq.com/posting-api/job-board/<org>?includeCompensation=true`
   - Greenhouse: `https://boards-api.greenhouse.io/v1/boards/<token>/jobs?content=true`
   - Lever: `https://api.lever.co/v0/postings/<company>?mode=json`
   - Filter titles to the track variants. Strip HTML from descriptions.
3. **~15 live postings** found by web search for the track title (fetch each; skip ones that return only a title).

Target 50-150 JDs total. Dedupe by company + normalized title. For each JD save `resume/jd-corpus/<track-slug>/<company>-<title-slug>.md` with frontmatter: `company`, `title`, `source` (roles / ashby / greenhouse / lever / web), `url`, `posted` (date if the API gives one, else saved date, else `unknown`).

If fewer than 30 JDs come back, say so in the report. The frequencies are weaker; do not pad with off-track roles.

## Step 3: Analyze (same or second subagent, reads the corpus files)

### 3.1 Keyword frequency

Extract terms per JD: languages, frameworks, tools, infra, methods (e.g. RLHF, evals, distributed training), domains, and degree/years requirements. Normalize variants (`PyTorch`/`pytorch`, `LLM`/`LLMs`/`large language models`).

Count **share of JDs** that mention each term (not raw mentions). Split by date: **recent** (posted in the last 90 days) vs **older**. A term is **rising** if its recent share is at least 1.5x its older share and appears in at least 5 recent JDs. If dates are mostly unknown, say the split is unreliable.

Table, top ~40 terms:

```
| Term | All % | Recent % | Older % | Rising |
```

Also report: share requiring a PhD, share stating years of experience (and the median), share mentioning visa sponsorship.

### 3.2 Top 8 requirement themes

Cluster requirements into 8 themes (e.g. "large-scale training infra", "eval design", "research taste / paper reproduction"). For each: a one-line description, share of JDs, and 1 short quoted example line from a real JD with its company.

### 3.3 KEEP/CUT map of the user's inventory

For each experience and project in the inventory:

```
| Item | KEEP/CUT | Themes it proves | Angle to lead on for this track |
```

- KEEP if it proves a theme in the top 8 or a term above ~20% share.
- The angle is how to frame the same facts for this track (e.g. "lead with the eval methodology and finding, not the API").
- CUT items still useful for other tracks are marked `CUT (keep for <other track>)`.
- Every claim about the user must come from `profile.md` or the inventory.

### 3.4 Recommended skills lines

2-4 lines, grouped by category, each line ordered by share of JDs. Include only skills the user has actually used per `profile.md` or the inventory. Mark any skill on the line that no planned bullet proves yet, so build-resume can add evidence or drop it.

### 3.5 Honest gaps

Frequent terms (above ~15% share) the user has not used. For each: share, and one of
- **learnable soon** (a small real project could close it),
- **real gap** (do not claim; be ready to say so in interviews),
- **hard filter** (e.g. PhD required: tell the user what share of the corpus this rules out).

Never suggest adding these to the resume without real work behind them.

## Step 4: Write the report

Write `resume/jd-analysis-<track-slug>-<YYYY-MM-DD>.md`:

```
---
track: <Track>
date: <YYYY-MM-DD>
jds: <N> (roles: a, ashby: b, greenhouse: c, lever: d, web: e)
recent_window_days: 90
---
# JD analysis: <Track>
## Corpus
## Keyword frequency
## Rising terms
## Top 8 themes
## Inventory KEEP/CUT
## Skills lines
## Honest gaps
## Sources   (one line per JD: company, title, url)
```

## Step 5: Report to the user

Short: JD count by source, the 5 strongest terms, rising terms, which inventory items lead, the top 2 honest gaps, and the report path. If called from `/job-hunt-kit:build-resume`, return there for the ranking step.

## Rules

- Count shares of JDs, not raw word counts; one verbose posting must not skew the table.
- Never invent JDs, dates, or quotes. Each quote must come from a saved corpus file.
- Skills lines contain only what the user has used. Gaps are reported, not hidden and not faked.
- Do not write anything inside the plugin folder; all output goes in the workspace.
