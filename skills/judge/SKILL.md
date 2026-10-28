---
name: judge
description: Gold-standard yes/no content check for outreach emails and written job-application answers. Use BEFORE saving or sending any outreach email and BEFORE submitting any written application answer; also when the user says "judge this", "check this email", "is this answer good". Every NO comes with a fix; revise until all YES.
---

# Judge

A few evergreen yes/no questions about the **content** — why this person, one specific ask, evidence that fits,
every sentence earns its place, sounds human, true claims. Nothing mechanical (no word counts or phrase lists).
Questions live in `${CLAUDE_SKILL_DIR}/rubrics/email.yaml` and `${CLAUDE_SKILL_DIR}/rubrics/answer.yaml`.
Every background claim is checked sentence by sentence against the user's `profile.md` (and master resume PDFs).

Answers come from **Jev** (TypeSafe System One, fast calibrated yes/no) when `TYPESAFE_API_KEY` is set.
Without a key the script prints the questions and exits 3 — then answer each one yourself, strictly, as YES/NO.

## Run

Write the draft to a JSON file, then:

```bash
uv run --quiet ${CLAUDE_SKILL_DIR}/judge.py draft.json --kind email     # or --kind answer; add --verbose for P(yes)
```
Exit 0 = READY, 1 = fix needed, 3 = no key (answer the printed questions yourself).
Run from the folder that contains `job-hunt/`, or set `JOB_HUNT_HOME`.

- Email: `{"text": "...", "context": {"recipient": {"name", "role", "company"}, "relationship": "cold|referral|warm|follow-up", "referrer": "...", "goal": "..."}}`
- Answer: `{"text": "...", "context": {"question": "the exact form question", "role": "...", "requirements": ["..."]}}`

Give honest context about what the recipient or role needs; without it, "evidence fits" cannot pass.

## Loop

1. Run. Apply the fix for every NO (per-sentence checks name the exact sentence).
2. Re-run. Stop at READY or after 3 rounds, then show the user what is left.
3. If a NO is a judge miss (the claim is in profile.md, or the user explicitly asked for that line), keep the
   user's intent — merge or reword rather than delete — and say so.
4. If a true fact is flagged only because profile.md lacks it, add it to profile.md with its source — never to
   make an untrue claim pass.

## Editing questions

One condition per question, YES = good, no "if… answer yes if…" compounds (Jev answers those badly).
After editing, re-run a known-good text 3 times to confirm it still passes.
