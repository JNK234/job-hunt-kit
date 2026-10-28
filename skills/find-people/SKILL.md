---
name: find-people
description: Find the real people on a hiring team (hiring manager, peer engineers, warm connections) and get emails you can trust before any outreach is drafted. Use when the user says "find the hiring manager", "who should I email at X", "reach out to the team", "warm outreach for [role/company]", "find people at X", or after applying to a job and wanting to contact the team. Targets hiring managers / peer ICs / warm connections, never recruiters by default. Hands drafting to /job-hunt-kit:write-outreach.
---

# Find People

Find the people behind a job posting, confirm how to reach them, and hand each one to `/job-hunt-kit:write-outreach` for drafting. This skill never sends anything.

**Workspace:** `$JOB_HUNT_HOME` if set, otherwise `./job-hunt/`. Read `profile.md` (for warm-connection angles) and log to `outreach/tracker.csv`. Never write state inside the plugin folder.

**Integrations (all optional):**

| Integration | Used for | Without it |
|---|---|---|
| chrome-devtools MCP | Reading search-engine results for `site:linkedin.com/in` queries | Run a web search tool, or give the user the search URLs; the user confirms names |
| `HUNTER_API_KEY` | Domain-search (candidates) + email-verifier (SMTP gate) | Find public emails / contact pages yourself, or suggest a LinkedIn message |
| `APOLLO_API_KEY` | Resolving a named IC that Hunter misses | Manual confirmation, or LinkedIn message |
| `jq`, `curl` | Required by the shell scripts | Skip the scripts; use the manual fallbacks |

Keys come from environment variables first, then `$JOB_HUNT_HOME/.env` or `./job-hunt/.env`. Template: `${CLAUDE_SKILL_DIR}/scripts/.env.example`. Never put a key in the plugin folder.

---

## Reality check first: who to target and what to ask

The biggest failure is the wrong person with the wrong ask. Execs are easy to find (public emails) and are the wrong recipients for "please consider my application."

**Target priority (best to worst):**
1. **A warm / shared connection**: someone the user knows or shares ground with (school, ex-employer, mutual contact, research area, per `profile.md`). Ask: a forwardable intro.
2. **The hiring manager of that specific team / req.** Ask: a tight why-me + "who owns this?" or a short chat.
3. **A peer IC on the team** (same or near-same role). Ask: a low-stakes curiosity ask, e.g. 15 minutes on what the team is building. ICs reply more and can flag the user internally.

**Do not target by default:** recruiters / talent acquisition, or VPs / C-suite just because their email is confirmable. Only target a recruiter if the user explicitly asks.

**If only an exec is confirmable and there is no warm connection:** say so plainly. Recommend finding the actual hiring manager or a peer IC (even via manual LinkedIn lookup), or a value-first note on their work, not a "consider me" note.

---

## The pipeline

```
[0]  Pre-flight: check the user's own history       (tracker.csv + applications/)
[1]  Infer team + pick target tier                  (JD + company research)
[2]  Find real people on that team                  (search engine -> site:linkedin.com/in)
[3a] Candidate emails                               (Hunter domain-search, sources > 0 only)
[3b] SMTP verify gate                               (verify_email.sh must say SAFE)
[3c] IC fallback                                    (Apollo people/match, then 3b again)
[4]  Hand off to /job-hunt-kit:write-outreach       (drafting, judge, saving)
[5]  Log each person to outreach/tracker.csv
```

**The rule that prevents every email mistake:** never guess an email. An address is send-eligible only when `verify_email.sh` returns **SAFE**, or the user confirms it from a source they trust (see manual fallback). Hunter `sources > 0` is a candidate, not a confirmation.

### Step 0: Pre-flight

Before finding anyone, check `outreach/tracker.csv` and `applications/` in the workspace:
- **Recently rejected by this team** (under about a month): do not cold-outreach that team. Pick a different team or wait.
- **Live pending application:** outreach can help; keep it soft and value-first, never "reconsider me."
- **Existing warm thread** (someone already in touch, a prior interviewer): revive that thread instead of starting cold.
- **Person already in tracker.csv:** do not add a duplicate; follow the existing row's `next_touch_due`.

### Step 1: Infer the team and target tier

From the JD (and a company-research subagent if needed), decide:
- The specific **team / org** the role sits in.
- The **title keywords** for people on it.
- The **target tier** (warm first, else hiring manager, else peer IC).

Cross-reference `profile.md` (schools, past employers, research areas, communities) for a warm-connection angle. That beats everything.

### Step 2: Find real people

Generate the searches:
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/build_searches.py "<Company>" "<Team>"
```
It prints, per tier (hiring_manager / senior_ic / director), a `search_query`, Google and DuckDuckGo URLs, and LinkedIn search URLs. Use the `site:linkedin.com/in` search-engine query: no LinkedIn login, no scraping.

**With chrome-devtools MCP:**
1. `new_page` with the search URL (open a fresh page; don't reuse a stale tab).
2. `take_snapshot` to read names, titles, locations, and LinkedIn URLs from the results.
3. Parse `{name, title, location, linkedin_url, tier}`.

**Without chrome-devtools MCP:** run the `search_query` through any available web search tool, or give the user the URLs to open. List the candidates you found and have the user confirm each one (current company, current team) before continuing. Never present a name you did not see in a result.

**Filter out:** wrong-company namesakes (a similarly named company is not the target), former employees (title says "ex-" or past tense), recruiters, and anyone off-team.

**Never scrape LinkedIn directly** (ToS / account bans). If search results are thin, ask the user to run the LinkedIn search URL themselves and paste names back.

### Step 3a: Candidate emails (Hunter domain-search, not finder)

Hunter's email-finder guesses addresses from the company pattern. Guesses come back with `sources: 0`. On catch-all domains (servers that accept every address) a guess can even look "deliverable." **Never trust a `sources: 0` address.**

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/domain_search.sh <domain>
```
Prints only addresses found in real public sources (`sources > 0`), with confidence, name, and position. Guesses are dropped and counted on stderr. Free plan: `limit` max 10, about 50 searches and 100 verifications per month, so spend them on the right team.

Exit code 3 means no Hunter key: go to the manual fallback below.

### Step 3b: SMTP verify gate (every address, before drafting)

`sources >= 1` does not prove the mailbox is live; one stale source can list an address for someone who has left. Run the gate on every candidate:

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/verify_email.sh <email> [email2 ...]
```
One verdict per address; exit 0 only if all are SAFE:
- **SAFE**: `smtp_check=true`, `status=valid`, `score >= 80`, `accept_all=false`. OK to hand off.
- **RISKY**: deliverable but catch-all (`accept_all=true`) or low score. This is the guess zone. Do not use unless a second independent source confirms it (Apollo verified, the person's own site, a public commit author email).
- **BLOCKED**: the server refuses verification probes. Unknowable, not dead. Use only if the address came from an independent trusted source and matches the org's known pattern, and the user agrees.
- **REJECT**: undeliverable / invalid. Drop it.

Raise or lower the score floor with `VERIFY_SCORE_THRESHOLD` (default 80).

### Step 3c: IC fallback (Apollo)

Hunter skews toward execs and public addresses and often misses the peer ICs who are the best targets. When the right person has no SAFE Hunter email:

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/apollo_lookup.sh "First Last" "Company"
bash ${CLAUDE_SKILL_DIR}/scripts/apollo_lookup.sh --linkedin "<linkedin_url>"
```
- Trust only `email_status == "verified"`, then still run it through `verify_email.sh` (3b).
- `guessed` / `unavailable`: treat like `sources: 0`. Do not use.

**Never substitute** "an exec I can confirm" for "the right person I can't." Reconsider the target, try manual confirmation, or skip.

### Manual fallback (no Hunter / Apollo key, or no SAFE address)

Do these in order and stop at the first that works:
1. **Public email the person published themselves**: personal site, GitHub profile, paper author block, conference page, a public commit author email. Record where you found it. The user confirms before it is used.
2. **Public team / contact page or form** on the company site, if it routes to the right team.
3. **LinkedIn message or connection note**: suggest this as the channel. It needs no email at all.
4. **Skip** the person and say why.

Never build an address from the company pattern (first@, first.last@) and present it as found.

### Step 4: Hand off to `/job-hunt-kit:write-outreach`

For each confirmed target, pass to `/job-hunt-kit:write-outreach`:
- name, title, team, company, tier, channel (`email` or `linkedin`), the confirmed email (if any) and how it was confirmed,
- the specific ask for that tier,
- any real, verifiable hook on the person (a post, talk, paper, repo you actually saw, with its URL), and any warm-connection angle from `profile.md`.

Do not draft here. `write-outreach` owns voice, the `/job-hunt-kit:judge` check, and saving drafts. Do not invent a hook to make the email look researched; if there is no real hook, say so in the handoff.

### Step 5: Log to `outreach/tracker.csv`

Create the file with this header if it does not exist:
```
person,company,channel,email,artifact,touch_count,last_touch,next_touch_due,status
```
One row per person (no duplicates):
- `person`: full name (put title/team in `artifact` notes only if useful; keep the column a name)
- `channel`: `email` or `linkedin`
- `email`: confirmed address, or empty for LinkedIn
- `artifact`: the hook or user artifact the message leans on (URL or short label)
- `touch_count`: `0` until the user sends
- `last_touch`, `next_touch_due`: empty until sent (dates as YYYY-MM-DD)
- `status`: `found` after this skill; `write-outreach` moves it to `drafted`; the user moves it to `sent` / `replied`

Quote any field that contains a comma.

Finish by telling the user, in a few lines: who was found, which addresses are SAFE vs. not, which people need a LinkedIn message instead, and that drafting is next via `/job-hunt-kit:write-outreach`.

---

## Do not

1. Target recruiters or random execs with "please consider my application" (unless the user explicitly asks for a recruiter).
2. Use any address that is not SAFE from `verify_email.sh` or confirmed by the user from a source they trust.
3. Trust Hunter email-finder guesses or any `sources: 0` address, especially on catch-all domains.
4. Guess an email from the company pattern.
5. Substitute a confirmable exec for the right IC.
6. Scrape LinkedIn directly.
7. Present a person you did not see in a search result, or a hook you did not actually read.
8. Send anything. Drafting goes to `/job-hunt-kit:write-outreach`; the user sends.
9. Store API keys or outreach data in the plugin folder.

## Quick reference

| Step | Action | Tool |
|---|---|---|
| 0 | Check history | `outreach/tracker.csv`, `applications/` |
| 1 | Team + tier | JD + company research |
| 2 | Find people | `build_searches.py` -> chrome-devtools MCP or web search -> user confirms |
| 3a | Candidates | `domain_search.sh <domain>` (sources > 0 only) |
| 3b | Verify gate | `verify_email.sh <email>` -> must be SAFE |
| 3c | IC fallback | `apollo_lookup.sh` (verified only) -> 3b again |
| fallback | No key / no SAFE | self-published email, contact page, LinkedIn message, or skip |
| 4 | Draft | `/job-hunt-kit:write-outreach` |
| 5 | Log | `outreach/tracker.csv` |
