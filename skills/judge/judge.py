# /// script
# dependencies = ["typesafe-sdk", "pyyaml"]
# ///
# ABOUTME: Content check for outreach emails and application answers: gold-standard yes/no questions answered by Jev.
# ABOUTME: Every NO prints its fix; claims are checked per sentence against the workspace profile.md. Exit 0 = ready.

import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml
from typesafe_sdk import Noul, TypeSafeClient

HERE = Path(__file__).parent


def workspace():
    return Path(os.environ.get("JOB_HUNT_HOME") or Path.cwd() / "job-hunt")


def sender_facts():
    """The user's verified facts: profile.md, plus the text of any master resume PDFs if pdftotext exists."""
    ws = workspace()
    parts = [(ws / "profile.md").read_text()] if (ws / "profile.md").exists() else []
    for pdf in sorted((ws / "resume").glob("*.pdf")) if (ws / "resume").exists() else []:
        out = os.popen(f'pdftotext -layout "{pdf}" - 2>/dev/null').read()
        if out:
            parts.append(f"## Resume {pdf.name}\n{out}")
    if not parts:
        sys.exit(f"No profile found at {ws}/profile.md — run /job-hunt-kit:setup first.")
    return "\n\n".join(parts)
MODEL = "jev-1.14.0"  # pinned so answers stay stable; bump deliberately and re-check a few known texts


SIGNOFF = re.compile(r"\n\s*(thanks and regards|best regards|regards|best|cheers|sincerely|thanks)\s*,?\s*\n", re.I)


def sentences(text):
    """Sentences of the message body, signature excluded."""
    m = SIGNOFF.search(text)
    text = text[:m.start()] if m else text
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip(" -•\t") for p in parts if len(p.strip(" -•\t").split()) >= 4]


def unsupported_claims(text, facts_text, client):
    """Citation-check pattern: one yes/no per sentence against the resume facts."""
    claims = sentences(text)
    if not claims:
        return []
    resp = client.system_one(
        model=MODEL,
        state={"claims": claims, "sender_facts": facts_text},
        questions={f"c{i}": Noul(
            instructions=f"Is every background fact that `claims[{i}]` states about the writer supported by "
                         f"`sender_facts`? A statement of what the writer wants is not a background fact. "
                         f"Answer yes if `claims[{i}]` states no background facts.")
            for i in range(len(claims))},
    )
    # Wording and threshold chosen on planted true/false claims: false claims scored <= 0.21, true >= 0.40.
    return [c for i, c in enumerate(claims) if resp.answers[f"c{i}"].noul < 0.3]


def applies(q, context):
    """applies_when: a list of relationships, or {context_field: [allowed values]}."""
    cond = q.get("applies_when")
    if not cond:
        return True
    if isinstance(cond, list):
        return context.get("relationship") in cond
    return all(context.get(field) in allowed for field, allowed in cond.items())


def check(text, context, kind):
    rubric = yaml.safe_load((HERE / "rubrics" / f"{kind}.yaml").read_text())
    questions = [q for q in rubric["questions"] if applies(q, context)]
    facts = sender_facts()
    whole = [q for q in questions if not q.get("per_sentence")]
    per_sentence = [q for q in questions if q.get("per_sentence")]
    sents = sentences(text)
    with TypeSafeClient() as client:
        resp = client.system_one(
            model=MODEL,
            state={"text": text, "context": context, "sentences": sents},
            questions={**{q["id"]: Noul(instructions=q["question"]) for q in whole},
                       **{f"{q['id']}__{i}": Noul(instructions=q["question"].replace("`sentence`", f"`sentences[{i}]`")
                                                  + " The full message is `text`.")
                          for q in per_sentence for i in range(len(sents))}},
        )
        results = [{"id": q["id"], "question": q["question"], "p": round(resp.answers[q["id"]].noul, 2),
                    "yes": resp.answers[q["id"]].noul >= 0.5, "fix": q["fix"]} for q in whole]
        for q in per_sentence:
            # Flag only clear misses: a single borderline sentence is not worth a rewrite.
            flagged = [s for i, s in enumerate(sents) if resp.answers[f"{q['id']}__{i}"].noul < 0.3]
            results.append({"id": q["id"], "yes": not flagged,
                            "fix": q["fix"] + " " + "; ".join(f'"{s[:110]}"' for s in flagged)})
        bad = unsupported_claims(text, facts, client)
    results.append({"id": "claims_true", "yes": not bad,
                    "fix": "Not on your resume — correct or remove: " + "; ".join(f'"{c[:110]}"' for c in bad)})
    return results


def report(results):
    noes = [r for r in results if not r["yes"]]
    if not noes:
        return f"READY — all {len(results)} questions YES."
    lines = [f"FIX {len(noes)} of {len(results)}, then re-run:"]
    lines += [f"  {i}. NO  {r['id']}\n     fix: {r['fix']}" for i, r in enumerate(noes, 1)]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Gold-standard content check for an email or application answer.")
    ap.add_argument("draft", help="JSON: {text, context}. Email context: {recipient, relationship, referrer, goal}. "
                                  "Answer context: {question, role, requirements}.")
    ap.add_argument("--kind", choices=["email", "answer"], default="email")
    ap.add_argument("--verbose", action="store_true", help="show every question with its P(yes)")
    args = ap.parse_args()
    draft = json.loads(Path(args.draft).read_text())
    text = draft.get("text") or draft["body"]
    if not os.environ.get("TYPESAFE_API_KEY"):
        # No Jev: hand the same questions to the calling agent to answer itself.
        rubric = yaml.safe_load((HERE / "rubrics" / f"{args.kind}.yaml").read_text())
        print("NO_TYPESAFE_KEY — answer each question YES or NO yourself, strictly, then apply the fix for every NO:")
        for q in rubric["questions"]:
            print(f"- [{q['id']}] {q['question']}\n    fix: {q['fix']}")
        print("- [claims_true] Is every background fact about the writer, sentence by sentence, supported by profile.md?")
        sys.exit(3)
    results = check(text, draft.get("context", {}), args.kind)
    if args.verbose:
        for r in results:
            p = f"{r['p']:.2f}" if "p" in r else "  - "
            print(f"  {'YES' if r['yes'] else 'NO '}  {p}  {r['id']}")
    print(report(results))
    sys.exit(0 if all(r["yes"] for r in results) else 1)


if __name__ == "__main__":
    main()
