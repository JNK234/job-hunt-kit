---
name: write-outreach
description: Draft and follow up on short outreach emails to busy people (hiring managers, researchers, founders, team leads, mentors). Use when the user says "draft an email", "write outreach", "cold email", "follow up", "email this person", "reach out to", or "check my outreach". Covers the drafting method, voice, follow-up cadence, dead-thread revival, and reply checks. Never sends.
---

# Write Outreach

Busy people skim. Every message should be readable in 15 seconds, easy to answer, and easy to forward.
This skill writes the message and runs the follow-up loop. It never sends anything; the user does.

## Inputs (read first)

Workspace: `$JOB_HUNT_HOME` if set, else `./job-hunt/`.

- `profile.md` — every fact about the user, plus the **Writing preferences** section:
  - `sign-off` (default if missing: `Best,`)
  - `banned phrases` (added to the defaults below, never replacing them)
  - `hedges to avoid` (added to the default hedge list below)
- `outreach/tracker.csv` — columns: person, company, channel, email, artifact, touch_count, last_touch, next_touch_due, status
- `applications/` — one file per application, with status

If `profile.md` is missing, stop and point the user to `/job-hunt-kit:setup`.

## Warm before cold

Warm paths (a referral, an intro from a mutual contact, someone the user has already spoken with) get far higher reply
rates than cold email, and referred candidates are hired at much higher rates than cold applicants. Before drafting
cold, ask: does the user know anyone at this company, or anyone who knows the recipient? Check `outreach/tracker.csv`
and `profile.md` for prior contacts. If there is a warm path, write that message (a forward request, rule 8) first.

## Pre-flight: check the history

Before writing to anyone at a company, check `applications/` and `outreach/tracker.csv`:
- **Rejected by this team in the last ~month** → don't cold-email that team. It reads as pressure. Pick another team or wait.
- **Live pending application** → outreach can help, but keep it value-first. Never "please reconsider me".
- **Existing thread with this person** → revive it (rule 7). Don't start a new cold thread.

## The 8 rules

1. **Target people, not portals.** Write to the named person who owns the problem. Job portals are a parallel track.
2. **Open with their work, not yourself.** The first sentence shows you read their paper, used their tool, or understand their problem. No intro, no fan language.
3. **Lead with one artifact.** One link to the user's best relevant work plus one line on what it does and why it matters to them. The artifact is the pitch. One line of credentials at most.
4. **6–8 sentences.** If it scrolls on a phone, cut it.
5. **One small, specific ask.** "Is your team hiring for X this year?" / "Could you forward this to whoever owns hiring for X?" / "15 minutes for one question about X?" Never "any opportunities?".
6. **Follow up on a fixed cadence.** See the follow-up loop below. Three touches max. Track every thread.
7. **Revive dead threads.** Stalled processes and silent contacts get one re-ping with one line of real news.
8. **Ask mentors for forwards, explicitly.** What the user is looking for (one sentence) + best-work link + "would you introduce me to anyone relevant?" + a short paste-ready blurb they can forward.

## Drafting protocol (do this before writing a word)

Most outreach fails by leading with the wrong, weak, or unverified finding. A resume bullet compresses results; drafting
from it picks a weaker hook and invites fabrication.

1. **Inventory real artifacts.** List the user's public work from `profile.md`: posts, papers, repos, demos. A post that explains a finding beats a bare repo link.
2. **Read the source behind the hook.** Open the actual post, paper section, or README, not the summary. Find the strongest, most specific real finding: a number, a mechanism, a surprising result.
3. **Match finding to recipient.** Pick the result that connects to this person's work. Different recipient, different finding from the same body of work.
4. **Verify every claim against `profile.md`** and the source you just read. Every number and claim must trace to one of them. Never cite an unconfirmed result, never claim a method was run if it wasn't, never invent employers, metrics, or production use.
5. **Verify the recipient hook.** The thing you cite about them (post, talk, repo, JD line) must be real and read, not guessed. Never fabricate an "I saw your post" reference.
6. Then write to the voice rules and run the gates below.

## Structure

Cold first touch: 6–8 sentences of plain prose. Their work → your one artifact and why it's relevant → one line of
credentials → one ask → sign-off.

After a meeting, or when they asked for a resume or background, use the bulleted form:

```
Subject: <anchor on shared context, not the ask>

Hi <Name>,

<One warm sentence + one factual sentence about why you're writing.> Quick context on me:

- <most credible / recent fact>
- <closest match to the recipient's work>
- <specific build with a metric or method>
- <recent or active project>

<One soft interest line. Never two.>

<CTA with an easy out: forward instead of decide.>

<sign-off from profile.md>
<first name>
<one link, e.g. portfolio or LinkedIn>
```

Length: 120–180 words including the signature for the bulleted form; under ~150 for a cold first touch.

## Voice rules

1. **Subject anchors on shared context**, not the ask. Good: `Following up — <Name> (<event> yesterday)`. Bad: `Job inquiry`.
2. **Opening = one warm sentence + one factual sentence.** No throat-clearing.
3. **Bullets, not prose** in the bulleted form. 4–6 bullets, one line each, one fact + one specific.
4. **Most relevant bullet in position 2 or 3**, the top of the skim zone.
5. **Keep specifics, drop superlatives.** Keep model names, metrics, methods, venues, dates. Drop "passionate", "excited", "world-class", "cutting-edge", "impactful".
6. **One soft interest line.** Never stack two.
7. **CTA gives an easy out.** "Let me know if anything looks like a fit, or who I should be talking to."
8. **Sign-off comes from `profile.md`.** Never "Sincerely,".
9. **Don't read their tagline back to them.** Naming their team's work is fine; quoting their homepage is not.
10. **Concrete time words.** "yesterday", "last week", not "recently" or "previously".
11. **No false-politeness hedges.** If the email asks for something, the ask stands plainly. Default hedges to cut: "no rush at all", "happy to wait either way", "whenever convenient", "if that works for you", plus the profile's list.

## Banned phrases (defaults; `profile.md` can add more)

"I hope this email finds you well" · "Thanks for taking the time" · "Reaching out with my profile" · "I would love to…" (more than once) ·
"Would be glad to…" · "Quick snapshot" · "Prior:" / "Previously:" · "At your earliest convenience" · "Please let me know" ·
"Looking forward to hearing from you" · "Sincerely," / "Best regards," · "Per our conversation" · "I am writing to…"

More AI-tell phrases and the full human-touch checklist: `${CLAUDE_SKILL_DIR}/references/human-touch.md`.

## When the draft is too long, cut in this order

1. Second interest line  2. Adjectives ("successfully shipped" → "shipped")  3. Throat-clearing in the opening
4. CTA hedges  5. The bullet least relevant to the recipient  6. Generic descriptors (keep names and metrics)

## When the draft is too short or generic, add in this order

1. A concrete metric or method on the weakest bullet  2. Venue or date for credentials
3. One soft interest line, if missing  4. A relevant project not yet mentioned, only if it sharpens the closest match

## Anti-patterns

Multi-paragraph prose in the bulleted form · restating their tagline · listing every project · three-sentence opening ·
two interest lines · formal sign-off · emojis (unless asked) · bullets longer than one line · buzzwords · begging energy
("would really appreciate any opportunity at all").

## Reference example (fictional)

```
Subject: Following up — Priya (Open Evals Meetup yesterday)

Hi Daniel,

Good to meet you yesterday at the Open Evals Meetup — sending my background over as you suggested. Quick context on me:

- MS in Computer Science, based in Austin
- Built an eval harness for code agents that flags reward hacking; caught 31 of 40 seeded exploits
- Wrote up why pass@1 overstated our agent's ability by 18 points once tests were deduplicated
- Currently fine-tuning a 7B model on synthetic bug-fix pairs
- Earlier: data engineer at a logistics startup (pipelines over 2B shipment events)

The eval-infrastructure work your team described is exactly what I'd want to dig into — happy to help in whatever form makes sense.

Let me know if anything looks like a fit, or who I should be talking to.

Best,
Priya
priya.example.dev
```

~150 words, 5 bullets, one interest line, CTA offers the forward path. All names and facts are invented.

## Gates before saving (every final draft)

1. **Human-touch check** against `references/human-touch.md`: all 3 load-bearing gates pass, ≥10/12 overall.
2. **Fact check**: every user claim traces to `profile.md` or the artifact read in step 2.
3. **`/job-hunt-kit:judge` with kind `email`.** Apply each fix it returns, re-run until it passes. Only truthful fixes; never add a claim to satisfy the judge.

Show the user the draft. Iterate on one dimension per round (tone or content or length). Stop when the user says lock it.

## Saving (never send)

- **Gmail MCP available** → save as a Gmail draft (create draft only; never call send).
- **Otherwise** → write `outreach/drafts/<YYYY-MM-DD>-<person-slug>.md` with To, Subject, Body.
- Attachments: Gmail drafts via MCP may not support them. Tell the user to attach the resume by hand.
- Update `outreach/tracker.csv`: add or update the row, `touch_count`, `last_touch` (draft date; the user corrects it on send), `next_touch_due` = last_touch + 7–9 days, `status`.

## Follow-up loop

Most replies come on the 2nd or 3rd touch. Silence is the default, not a verdict. Three touches max, all short:

- **Touch 1** — the first message. Record it in the tracker.
- **Touch 2 — day 7–9, if no reply.** Two lines, re-link the artifact, no guilt. "Resending the <artifact> in case it got buried. Still very interested."
- **Touch 3 — 3–4 weeks later, only if the thread went alive-then-dead** (they replied once, then went silent). One line of real news. Never send a touch 3 to a thread that never replied.

**Dead-thread revival:** stalled processes, months-silent contacts → one re-ping with one line of real news
("since we spoke I built/wrote X"). The news must be true and in `profile.md`.

## "Check my outreach" (on demand)

Run when the user asks:
1. **Find replies.** Gmail MCP available → search threads by recipient or subject, check who sent the latest message. Otherwise → list the open tracker rows and ask the user which ones got replies.
2. **Classify each thread:** replied (handle the reply) · no reply past day 7–9 (draft touch 2) · alive-then-dead past 3–4 weeks (draft touch 3) · still in window (wait) · 3 touches done (close).
3. **Draft due follow-ups** through the same gates, save them as above, update the tracker.
4. **Report** in a few lines: who replied, which follow-ups were drafted, who is still in window.
