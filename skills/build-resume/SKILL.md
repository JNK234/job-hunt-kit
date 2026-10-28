---
name: build-resume
description: Build or rebuild resume masters from scratch, one per target track. Use when the user says "build my resume", "rebuild my resume", "start my resume over", "make a research engineer and an AI engineer resume", "my resume is outdated", "audit my experience", or has no masters in resume/ yet. Audits every experience and project (profile, old resumes, GitHub, writing), archives old files, analyzes JDs per track, gets the user's ranking, writes <Name>_<TRACK>.tex masters, and does a visual layout pass.
---

# Build Resume

Produce one master resume per target track (e.g. Research Engineer vs AI Engineer). Masters are what `/job-hunt-kit:tailor-resume` copies per job.

Workspace: `$JOB_HUNT_HOME` if set, else `./job-hunt/`. Paths below are relative to it.

Output: `resume/preamble.tex` (copied once from `${CLAUDE_PLUGIN_ROOT}/templates/resume/preamble.tex`) and `resume/<Name>_<TRACK>.tex` + `.pdf` per track, e.g. `Jane_Doe_RE.tex`.

Work through the steps in order. Steps a, c, d end with the user deciding. Keep chat short; put long lists in workspace files.

## a) Audit: build the inventory

Goal: every experience, project, paper, and piece of public writing the user has, each with verified facts.

1. Ask the user in one message: which old resumes to read (paths), their GitHub handle, their writing links (blog, Substack, papers), and anything not written down anywhere.
2. Launch parallel subagents, one per source, each writing raw notes to `resume/audit/<source>.md`:
   - **profile.md**: every role/project with dates, stack, numbers.
   - **Old resumes**: parse `.tex` directly; for `.pdf` use `pdftotext -layout`. Extract every claim per entry.
   - **GitHub**: `gh repo list <handle> --limit 200 --json name,description,pushedAt,primaryLanguage,isFork`, then for non-fork repos pushed in the last 6-12 months, `gh api repos/<handle>/<repo>/commits?author=<handle>&since=<ISO date>` to get commit counts and date ranges. Read READMEs of the substantial ones.
   - **Writing**: list posts with titles and dates.
   - If `gh` is missing or not logged in, ask the user to paste their repo list.
3. Merge into `resume/inventory.md`: one section per item, with dates, stack, facts, and the source of each fact. Dedupe claims that appear on several resumes. When two sources disagree on a number or date, keep both and mark it `CONFLICT` for the user.
4. Build a month-by-month timeline for the last 24 months. Flag every month with no visible work. The resume must show recent activity; a 2026 project with dates can close a gap if the work is real.
5. Show the user: count of items, conflicts, and date gaps. Ask them to resolve conflicts and fill gaps from memory. Add new facts to `profile.md` only with their confirmation.

## b) Archive old resume files

Move, never delete:

```bash
mkdir -p resume/archive/$(date +%F) && mv <old files> resume/archive/$(date +%F)/
```

Move only files the user listed or old resume files in `resume/`. Leave `preamble.tex`, `inventory.md`, `audit/`, and `tailored/` alone. List what moved.

## c) Pick tracks and analyze JDs

1. Ask the user for 1-2 target tracks (e.g. Research Engineer, AI Engineer). Two is the max; each extra track is another master to maintain.
2. Run `/job-hunt-kit:analyze-jds` once per track. Each produces `resume/jd-analysis-<track>-<date>.md` with keyword frequency, themes, and a KEEP/CUT map of the inventory.
3. Summarize in a few lines per track: top themes, the angle to lead on, the honest gaps.

## d) User ranks what goes on each master

Show the full list of experiences and projects as one compact list per track, each with a recommendation:

```
TRACK: RE
  KEEP  Company A (Applied Scientist) — lead with eval research angle
  KEEP  Project X (Mar-Aug 2026) — multi-month, matches "post-training" theme
  CUT   Hackathon Y — weekend project
  ASK   Take-home Z — strong but not a real job; include?
```

Rules for recommendations:
- Projects section = substantial multi-month work. No hackathons or take-homes unless the user says so.
- Take-home or interview work, if included, is described by what was built. Never as employment or production use.
- Recent dated work beats older bigger work when it closes a gap.

The user ranks and decides. Record the final ranking per track in `resume/inventory.md`.

## e) Write one master per track

1. Copy `${CLAUDE_PLUGIN_ROOT}/templates/resume/preamble.tex` to `resume/preamble.tex` (once) and `${CLAUDE_PLUGIN_ROOT}/templates/resume/master-example.tex` to `resume/<Name>_<TRACK>.tex`. Keep `\input{preamble}`. Update the ABOUTME lines.
2. Fill the header macros from `profile.md`.
3. Write entries in the user's ranked order.

Bullet rules:
- **Track angle, same job.** The same role reads differently per track: on the RE master lead with the question studied and what was found; on the AIE master lead with what was built, shipped, and its scale. Same facts both ways.
- **Verb-first.** "Built", "Designed", "Measured", not "Responsible for".
- **Research bullets: question -> method -> finding.** "Tested whether X causes Y by Z; found W."
- **Founder or tiny-company roles:** one-line company description first (what it does, for whom), so the reader knows what the bullets mean.
- **Papers: honest authorship.** First author, co-author, or contributor, as it was. Venue and year exact.
- **Recent projects get dates** (e.g. `Mar 2026 -- Present`) so the timeline shows no gap.
- **Skills lines only list skills a bullet proves.** Order each line by the frequency table from step c.
- Every number and claim traces to `profile.md` or the confirmed inventory. Never invent.
- Keep the user's voice and their numbers. Don't reword a metric the user can defend just to sound different.

## f) Compile and layout pass

```bash
cd resume && tectonic <Name>_<TRACK>.tex
```

No tectonic: tell the user to install it (`brew install tectonic`, or see tectonic-typesetting.github.io) or compile in Overleaf with XeLaTeX after uploading the .tex and `preamble.tex`.

Then render and LOOK at each page. Do not judge layout from the .tex:

```bash
pdftoppm -png -r 90 <Name>_<TRACK>.pdf /tmp/<Name>_<TRACK>
```

Read the PNGs and fix, recompiling after each round:
- **Orphan lines:** a bullet whose last line has 3 words or fewer. Shorten the bullet so it ends on the line above (or lengthen it with a real fact to fill the line).
- **No bullet longer than 2 lines.** Split or cut.
- **No section heading stranded at a page bottom.**
- **One page**, unless the user accepts a small spill onto page 2.
- **Unfilled page with a big gap:** LaTeX may refuse to split a project list across pages and push the whole list down. Insert `\pagebreak` before the item where the break should go, with a `%` comment saying why, so it is easy to find and remove later.
- Check `pdfinfo <file>.pdf | grep Pages`.

Then the text check:

```bash
pdftotext -layout <Name>_<TRACK>.pdf - | grep -n '[ﬀﬁﬂﬃﬄ]'
```

This must print nothing. The preamble turns ligatures off; if glyphs appear, the master is not using `resume/preamble.tex`.

## g) Hand-off

Report per track: path to the `.tex` and `.pdf`, page count, what leads, and gaps still open. Point the user to `/job-hunt-kit:tailor-resume` for per-job versions.

## Lessons (keep these)

- Don't nitpick metric wording the user can defend. Ask once if a number looks off; if they confirm it, it stays.
- Never invent. A missing metric is better than a made-up one.
- Keep the user's voice. Tighten, don't rewrite them into someone else.
- Always LOOK at the rendered PNG. The .tex never tells you about orphans or stranded headings.
- `pdftotext` must show no ligature glyphs, or ATS parsers will drop words like "efficient".
- Archive, never delete. Old resumes hold claims you may need later.
