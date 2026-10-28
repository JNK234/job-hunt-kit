#!/usr/bin/env python3
# ABOUTME: Mechanical honesty gate for drafted application packages: AI-slop phrasing, uncredited
# ABOUTME: compliance claims, numbers that do not appear in profile.md, and unresolved placeholders.
"""
Usage: gate.py <package.md> [more.md ...]
Exit:  0 clean, 1 violations found, 2 bad args / no profile.md

Reads <workspace>/profile.md ($JOB_HUNT_HOME, else ./job-hunt). This is the cheap, deterministic
half of review. It cannot judge whether an argument is good; run /job-hunt-kit:judge on top.

Checks:
  AI-SLOP              stock phrases ("excited to", "passionate about", "leverage my skills"...)
  BANNED-BY-PROFILE    phrases listed under a "banned" heading in profile.md
  COMPLIANCE-CLAIM     HIPAA/SOC 2/FDA/PCI/GDPR claims when profile.md never mentions that term
  UNSOURCED-NUMBER     a metric inside an answer block (```...```) that profile.md does not contain
  PLACEHOLDER          TODO/TBD/[NEEDS INPUT]/[... TO FILL]/{{...}} left in a "submit-ready" file

Exemptions (each from a real false positive): guardrail notes ("do not claim X", checklist marks),
a negation word just before the match ("never use 'excited to'"), and lines that quote the
EMPLOYER's own field title (table rows, headings, bold field labels, inline quotes) when they trip
only one check. A structural line that trips several checks is prose in disguise and is flagged.
"""
import os
import re
import sys
from pathlib import Path

SLOP = (r"(so |really |very |i.m |am |incredibly )?excited (to|about)|passionate about|thrilled to|"
        r"aligns perfectly|perfect fit for|deeply resonates|i am confident that i|"
        r"leverage my (skills|expertise|background)|proven track record|uniquely positioned to|"
        r"fast-paced environment|i would be honored|cutting-edge")
COMPLIANCE_TERMS = ["HIPAA", "SOC 2", "SOC2", "FDA", "PCI-DSS", "PCI DSS", "GDPR", "FedRAMP", "ISO 27001"]
COMPLIANCE = (r"(experience|built|implemented|ensured|delivered|worked on|shipped|designed)[^.]{0,40}"
              r"\b(HIPAA|SOC ?2|FDA|PCI[- ]DSS|GDPR|FedRAMP|ISO 27001)\b|"
              r"\b(HIPAA|SOC ?2|FDA[- ]cleared|PCI[- ]DSS|GDPR[- ]compliant|FedRAMP)\b[^.]{0,40}"
              r"(experience|built|implemented|ensured|delivered|compliant|compliance)")
PLACEHOLDER = r"\bTODO\b|\bTBD\b|\bXXX\b|\[NEEDS INPUT\]|\[INSERT|\[[^\]]{0,20}TO FILL|\{\{.*?\}\}|lorem ipsum|<placeholder>"

MARKERS = re.compile(r"✅|✔|❌|~~|banned|guardrail|forbidden|do not (use|claim|say|mention|add|include|write)|"
                     r"don.t (claim|add|mention|include)|must not|left out|deliberately (omitted|avoided|left)|"
                     r"off-limits|appears nowhere", re.I)
NEG_NEAR = re.compile(r"(^|[\s\"(*_-])(no|not|never|avoid(ed|s|ing)?|without|omit(ted|s)?|exclude[ds]?|zero)\s[^.]{0,40}$", re.I)
FAKE_NEG = re.compile(r"never been more|no exceptions|not just|not only|nothing short|no doubt|without (a )?(doubt|question)|not merely", re.I)
STRUCTURAL = re.compile(r"^\s*(\||#{1,6}\s|\*\*(field\s+)?\d+[.\s])", re.I)
INLINE_QUOTED = re.compile(r"[\"“][^\"”]{0,200}(excited|passionate|thrilled)[^\"”]{0,200}[\"”]", re.I)
NUMBER = re.compile(r"(?<![\w.])(\$?\d[\d,]*(?:\.\d+)?\s?(?:%|x\b|k\b|m\b|b\b|\+)?)", re.I)


def workspace():
    return Path(os.environ.get("JOB_HUNT_HOME") or Path.cwd() / "job-hunt")


def banned_from_profile(text):
    """Bullets under any heading whose title contains 'banned' (e.g. '## Banned phrases')."""
    out, active = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            active = "banned" in line.lower()
            continue
        if active and re.match(r"\s*[-*]\s+", line):
            phrase = re.sub(r"^\s*[-*]\s+", "", line).strip().strip("\"'`")
            if phrase:
                out.append(re.escape(phrase))
    return "|".join(out)


def classes_on(line, checks):
    return sum(1 for _, rx in checks if rx and re.search(rx, line, re.I))


def exempt(line, rx, checks):
    if MARKERS.search(line):
        return True
    m = re.search(rx, line, re.I)
    if m and NEG_NEAR.search(line[: m.start()]) and not FAKE_NEG.search(line):
        return True
    if (STRUCTURAL.search(line) or INLINE_QUOTED.search(line)) and classes_on(line, checks) <= 1:
        return True
    return False


def norm_num(s):
    return re.sub(r"[\s,$+]", "", s.lower())


def gate(path, profile):
    text = path.read_text()
    profile_l = profile.lower()
    compliance_ok = [t for t in COMPLIANCE_TERMS if t.lower() in profile_l]
    checks = [("AI-SLOP", SLOP), ("BANNED-BY-PROFILE", banned_from_profile(profile)),
              ("COMPLIANCE-CLAIM", COMPLIANCE), ("PLACEHOLDER", PLACEHOLDER)]
    hits = []
    for n, line in enumerate(text.splitlines(), 1):
        for label, rx in checks:
            if not rx or not re.search(rx, line, re.I) or exempt(line, rx, checks):
                continue
            if label == "COMPLIANCE-CLAIM" and any(t.lower() in line.lower() for t in compliance_ok):
                continue
            hits.append((label, n, line.strip()))
    # Metrics inside answer blocks must exist in profile.md (word counts and years excepted).
    profile_nums = {norm_num(m) for m in NUMBER.findall(profile)}
    profile_digits = re.sub(r"[\s,]", "", profile_l)
    for block in re.finditer(r"```[^\n]*\n(.*?)```", text, re.S):
        start = text[: block.start()].count("\n") + 2
        for i, line in enumerate(block.group(1).splitlines()):
            for raw in NUMBER.findall(line):
                v = norm_num(raw)
                bare = re.sub(r"[^\d.]", "", v)
                has_unit = bare != v or raw.strip().startswith("$")
                if not bare or (len(bare.replace(".", "")) < 2 and not has_unit) or re.fullmatch(r"(19|20)\d\d", bare):
                    continue
                if v in profile_nums or bare in profile_digits:
                    continue
                hits.append(("UNSOURCED-NUMBER", start + i, f"{raw.strip()} :: {line.strip()[:100]}"))
    return hits


def main(argv):
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    prof = workspace() / "profile.md"
    if not prof.exists():
        print(f"ERROR: {prof} not found. Run /job-hunt-kit:setup first.", file=sys.stderr)
        return 2
    profile = prof.read_text()
    failed = False
    for arg in argv:
        p = Path(arg)
        if not p.exists():
            print(f"MISSING: {p}")
            failed = True
            continue
        hits = gate(p, profile)
        print(f"-- {p.name}: {'clean' if not hits else f'{len(hits)} flag(s)'}")
        for label, n, line in hits[:30]:
            print(f"   [{label}] line {n}: {line[:140]}")
        failed = failed or bool(hits)
    print("\nGATE: FAIL. Fix each flag or confirm it is a false positive." if failed
          else "\nGATE: PASS (mechanical). Still run /job-hunt-kit:judge on every written answer.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
