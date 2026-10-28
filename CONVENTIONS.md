# job-hunt-kit — authoring conventions

Every skill in this plugin follows these rules so the kit works for anyone.

## No personal dependencies
- No names, emails, phone numbers, schools, employers, file paths, or API keys of any specific person.
- No Obsidian, no vault, no `obsidian-cli`. All state is plain text in the user's workspace folder.
- No hard-coded model names for second-opinion reviews; say "a different model if one is available (e.g. via an MCP), otherwise a fresh subagent".
- Optional integrations are optional: each skill must still work, with a manual fallback, when Gmail MCP, chrome-devtools MCP, Hunter/Apollo keys, TypeSafe key, or tectonic are missing.

## The workspace (single source of truth)
Location: `$JOB_HUNT_HOME` if set, otherwise `./job-hunt/` in the current directory. Created by the `setup` skill.

```
job-hunt/
  profile.md            # who the user is: contact, work authorization, location prefs, every role/project with
                        # verified facts and numbers, links, writing/voice preferences (sign-off, banned phrases)
  answer-bank.md        # reusable written answers (why-us, proudest, hardest problem...), each with source + best-for
  applications/         # one file per application: NNN-company-role.md (JD snapshot, fit, form fields, answers, status)
  roles/                # saved JDs / sourced roles (job-pipeline)
  outreach/tracker.csv  # person, company, channel, email, artifact, touch_count, last_touch, next_touch_due, status
  resume/               # preamble.tex + masters (<name>_<TRACK>.tex/.pdf) + tailored/<company-role>/
```

## Skill references
- Skills are invoked as `/job-hunt-kit:<skill>`; refer to sibling skills by that name.
- Files in the skill's own folder: `${CLAUDE_SKILL_DIR}/...`. Files elsewhere in the plugin (e.g. `templates/`):
  `${CLAUDE_PLUGIN_ROOT}/...`. Claude Code substitutes both in SKILL.md text; they are NOT shell env vars, so write
  them inline in the commands shown in SKILL.md (e.g. `uv run ${CLAUDE_SKILL_DIR}/judge.py draft.json`).
- Never write user state inside the plugin folder (it is replaced on update). State lives in the workspace.
- Every SKILL.md starts with YAML frontmatter: `name`, `description` (with trigger phrases).

## Behaviour rules (learned the hard way; keep them)
- Never send email or submit an application. Draft and fill; the user sends/submits.
- When filling a web form, fill only the free-text answer fields; the user does uploads, yes/no, location, consent. File uploads on some ATSs (Ashby) wipe already-filled text.
- Every claim about the user must trace to `profile.md`. Never invent metrics, employers, deployments, or "production" usage. Interview/take-home work may be described by what was built, without claiming employment or production use.
- Never claim compliance work (HIPAA, SOC2, etc.) unless profile.md says it was done.
- Run `/job-hunt-kit:judge` on every outreach email and every written application answer before showing it as final.
- Keep chat output short; long artifacts go in workspace files.
