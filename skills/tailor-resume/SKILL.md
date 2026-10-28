---
name: tailor-resume
description: Tailor a master LaTeX resume to one job description. Use when the user says "tailor my resume for [company]", "customize resume for this role", "tailor-resume [URL]", "make a resume for [role]", or when /job-hunt-kit:apply-job needs a resume upload. Copies the matching track master, reorders and swaps bullets using only facts in profile.md, stops for approval, compiles one dense page with tectonic, and reports an ATS keyword match rate.
---

# Tailor Resume

Make a job-specific copy of a master resume. Same facts, different emphasis. The master is never edited here.

Workspace: `$JOB_HUNT_HOME` if set, else `./job-hunt/`. Paths below are relative to it.

- Masters: `resume/<Name>_<TRACK>.tex` (+ `.pdf`), all sharing `resume/preamble.tex`
- Output: `resume/tailored/<company-role>/<Name>_<TRACK>.tex` and `.pdf` (same filename as the master, so the upload looks clean)
- Facts: `profile.md` is the only source of claims
- Compiler: `tectonic` (fallback below if missing)

No masters yet? Stop and run `/job-hunt-kit:build-resume` first.

Execute the steps in order. Do not write LaTeX before the Step 3 approval.

## Step 1: Load the JD and pick the master

1. Get the JD: a URL (fetch it; if the page is JS-rendered and returns only a title, try a browser MCP, else ask the user to paste it), pasted text, or the JD snapshot in `applications/NNN-*.md` from an active `/job-hunt-kit:apply-job` run.
2. List `resume/*.tex` (ignore `preamble.tex`). Pick the master whose TRACK fits the JD (e.g. a research-heavy JD goes to `_RE`, a product/infra JD to `_AIE`). If unclear, ask the user which one in one line.
3. Read the master, `profile.md`, and the newest `resume/jd-analysis-<track>-*.md` if one exists (it says which angle to lead on for this track).

## Step 2: Map the JD to the resume

Extract JD keywords in clusters: languages, frameworks/tools, methods, domain terms, responsibilities, outcomes. Mark each as must-have (in requirements) or nice-to-have.

For each must-have, find the strongest evidence:
- a bullet already in the master,
- a fact in `profile.md` that is not on the master yet (a swap candidate),
- or nothing. That is a gap. Gaps stay gaps.

Decide:
- Order of experience entries and of bullets inside each entry (most relevant first).
- Which bullets or projects to swap in from `profile.md` and which to cut to make room. Keep the master's entry count so it still fits one page.
- Wording changes that use the JD's exact vocabulary for something the user really did (e.g. JD says "evaluation harness", profile says "eval framework": same thing, use their word).
- Skills line order: JD terms first. Add a skill only if a bullet on this resume proves it.

## Step 3: Present the plan, then STOP

Show it compactly:

```
MASTER: resume/<Name>_<TRACK>.tex  ->  resume/tailored/<company-role>/
EXPERIENCE ORDER: A, B, C (reason in a few words each)
SWAP IN:  [entry/bullet] from profile.md — covers <JD keyword>
SWAP OUT: [entry/bullet] — least relevant to this JD
REWORDS:  [entry] bullet N: "old phrase" -> "JD phrase" (same fact)
SKILLS:   new order / additions (each backed by bullet X)
GAPS (not faked): <keyword>, <keyword>
```

Wait for the user's approval or edits. Do not continue without it.

## Step 4: Write the tailored .tex

1. `mkdir -p resume/tailored/<company-role>` (lowercase, hyphens, e.g. `acme-research-engineer`).
2. Copy the master to `resume/tailored/<company-role>/<Name>_<TRACK>.tex`.
3. Change `\input{preamble}` to `\input{../../preamble}`. Do not copy the preamble; one shared copy keeps every resume consistent.
4. Apply only the approved changes. Keep the ABOUTME header lines, updating the second line to name the company and role.

Rules for edits:
- Every claim traces to `profile.md`. No new metrics, employers, titles, dates, users, deployments, or "production" claims.
- Never claim compliance work (HIPAA, SOC2, FDA...) unless `profile.md` says it was done.
- Do not change dates, company names, titles, degrees, or paper authorship.
- Do not change spacing parameters in the preamble. Fit the page by wording and by swapping entries.
- Keep the user's voice: verb-first bullets, their phrasing, their numbers.

## Step 5: Second-opinion check (optional but recommended)

Ask a different model if one is available (e.g. via an MCP), otherwise a fresh subagent, with the JD's top requirements and the .tex path:

```
Review this resume for <Role> at <Company>. Top requirements: <list>.
1. Do the strongest items lead and match the top requirements?
2. Which bullets are vague or irrelevant to this role?
3. Which JD keywords are missing that the resume could truthfully include?
4. Flag any bullet that overstates or could be read as fabricated.
5. Score alignment 1-10 and suggest up to 3 rewrites that keep the facts.
```

Apply only suggestions that stay true to `profile.md`. Ignore anything that invents.

## Step 6: Compile and check the layout

```bash
cd resume/tailored/<company-role> && tectonic <Name>_<TRACK>.tex
```

- On error: read the log, fix (common: unescaped `&`, `%`, `#`, `_`; missing brace), retry.
- Page count must be 1: `pdfinfo <Name>_<TRACK>.pdf | grep Pages`.
- Render and LOOK at it: `pdftoppm -png -r 90 <Name>_<TRACK>.pdf /tmp/tailor-preview` then read the PNG.
- Fix orphan lines (a bullet whose last line has 3 words or fewer: shorten it), any bullet longer than 2 lines, and a section heading stranded at the bottom. Dense means full lines, not tiny gaps.
- Recompile after each fix.

No tectonic? Tell the user: install it (`brew install tectonic` or see tectonic-typesetting.github.io), or upload the folder with `preamble.tex` to Overleaf and compile there with XeLaTeX. Then do the ATS check on the PDF they produce.

## Step 7: ATS keyword match rate

Measure on the PDF text, not the .tex, because that is what an ATS reads:

```bash
pdftotext -layout <Name>_<TRACK>.pdf - | tr '[:upper:]' '[:lower:]' > /tmp/tailor-resume.txt
```

1. Check for ligature glyphs (`ﬁ`, `ﬂ`, `ﬀ`, `ﬃ`) in the text. There should be none; the preamble disables them. If any show up, the preamble was not used; fix the `\input` path.
2. For each JD keyword from Step 2, grep the text (case-insensitive; count a close variant like "PyTorch"/"pytorch" or "LLM"/"LLMs" as found).
3. Report:

```
ATS MATCH: X/Y must-have (NN%), A/B nice-to-have
Missing, could add truthfully: <kw> (evidence in profile.md: ...)
Missing, real gap: <kw>
```

Guide: 80%+ strong, 60-79% apply with a strong cover note, under 60% tell the user plainly it is a weak match.

If a missing keyword is backed by `profile.md`, propose the edit, wait for approval, recompile, re-measure.

## Step 8: Report

Keep it short:
- Paths to the tailored `.tex` and `.pdf`
- What changed (order, swaps, rewords, skills)
- Match rate and the honest gaps
- Confirm the master in `resume/` is unchanged

If running inside `/job-hunt-kit:apply-job`, add the PDF path and match rate to the application file.

## LaTeX reference (from preamble.tex)

- `\resumeSubheading{Company}{Location}{Title}{Dates}` experience header
- `\resumeProjectHeading{\textbf{Name} $|$ \emph{Stack}}{Date}` project header
- `\resumeItem{text}` bullet; `\resumeItemListStart` / `\resumeItemListEnd` around bullets
- `\resumeSubHeadingListStart` / `\resumeSubHeadingListEnd` around a section's entries
- In a publications list, put `\item[]` before `\resumeItemListStart`

## Do not

1. Fabricate or inflate anything. A gap reported honestly beats a keyword that falls apart in the interview.
2. Edit the master in `resume/`.
3. Compile before the Step 3 approval.
4. Rename the PDF to include the company; keep the master's filename.
5. Stuff keywords the user has not used just to raise the match rate.
