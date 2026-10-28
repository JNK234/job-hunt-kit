#!/usr/bin/env python3
# ABOUTME: Persistent job-pipeline state in <workspace>/roles/PIPELINE.json so each run resumes
# ABOUTME: where the last stopped: add/dedup roles, update fields, rank the queue, re-verify liveness.
"""
Usage:
  pipeline.py init
  pipeline.py add <ats> <slug> <jobId> <company> <title> <url> [fit 0-10] [sponsor yes|no|unknown]
  pipeline.py set <id> <key> <value>
  pipeline.py status [status]
  pipeline.py next [n]            # top sourced/verified roles, sponsorship-in-writing first, then fit
  pipeline.py has <id>            # exit 0 if tracked
  pipeline.py stats
  pipeline.py verify              # re-check every non-dead role against its ATS board

Workspace: $JOB_HUNT_HOME if set, else ./job-hunt. Writes only <workspace>/roles/PIPELINE.json.
Role id: <ats>:<slug>:<jobId>. Status: sourced -> verified -> drafted -> submitted (user only) | dead.
"""
import json
import os
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ats  # noqa: E402

STATUSES = {"sourced", "verified", "drafted", "submitted", "dead"}
SPONSOR_RANK = {"yes": 0, "unknown": 1, "no": 2}


def workspace():
    return Path(os.environ.get("JOB_HUNT_HOME") or Path.cwd() / "job-hunt")


def db_path():
    return workspace() / "roles" / "PIPELINE.json"


def load():
    p = db_path()
    if not p.exists():
        return {"version": 1, "roles": []}
    return json.loads(p.read_text())


def save(db):
    """Atomic write: a failed dump must never truncate the only persistent state."""
    p = db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".PIPELINE.", suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(db, f, indent=2)
        f.write("\n")
    os.replace(tmp, p)


def find(db, rid):
    return next((r for r in db["roles"] if r["id"] == rid), None)


def row(r):
    return "\t".join([r["status"], str(r["fit"]), r["sponsor"], r["company"], r["title"], r["id"]])


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def cmd_add(args):
    if len(args) < 6:
        die("add <ats> <slug> <jobId> <company> <title> <url> [fit] [sponsor]")
    a, slug, jid, company, title, url = args[:6]
    fit = args[6] if len(args) > 6 else "0"
    sponsor = args[7] if len(args) > 7 else "unknown"
    try:
        fit = float(fit)
    except ValueError:
        die(f"fit must be numeric, got '{fit}'")
    if sponsor not in SPONSOR_RANK:
        die("sponsor must be yes|no|unknown")
    db = load()
    rid = f"{a}:{slug}:{jid}"
    if find(db, rid):
        print(f"dup: {rid}")
        return 0
    db["roles"].append({"id": rid, "ats": a, "slug": slug, "jobId": jid, "company": company,
                        "title": title, "url": url, "fit": fit, "sponsor": sponsor,
                        "status": "sourced", "note": "", "file": None,
                        "added": date.today().isoformat()})
    save(db)
    print(f"added: {rid}")
    return 0


def cmd_set(args):
    if len(args) != 3:
        die("set <id> <key> <value>")
    rid, key, val = args
    db = load()
    r = find(db, rid)
    if not r:
        die(f"no such role: {rid}")
    if key == "fit":
        try:
            val = float(val)
        except ValueError:
            die(f"fit must be numeric, got '{val}'")
    if key == "status" and val not in STATUSES:
        die(f"status must be one of {sorted(STATUSES)}")
    if key == "sponsor" and val not in SPONSOR_RANK:
        die("sponsor must be yes|no|unknown")
    r[key] = val
    save(db)
    print(f"set {rid}.{key}={val}")
    return 0


def cmd_verify():
    db = load()
    counts = {"LIVE": 0, "DEAD": 0, "UNKNOWN": 0}
    for r in db["roles"]:
        if r["status"] in ("dead", "submitted"):
            continue
        if r["ats"] not in ("ashby", "greenhouse", "lever"):
            state = "UNKNOWN"
        else:
            try:
                ids = {b[0] for b in ats.board(r["ats"], r["slug"])}
                state = "UNKNOWN" if not ids else ("LIVE" if r["jobId"] in ids else "DEAD")
            except ats.AtsError:
                state = "UNKNOWN"
        counts[state] += 1
        print(f"  {state:8} {r['id']}")
        if state == "DEAD":
            r["status"] = "dead"
            r["note"] = f"absent from {r['ats']} board on {date.today().isoformat()}"
        if state == "LIVE":
            r["checked"] = date.today().isoformat()
    save(db)
    print(f"\nlive={counts['LIVE']} dead={counts['DEAD']} unknown={counts['UNKNOWN']} (unknown roles left as-is)")
    return 0


def main(argv):
    cmd, args = (argv[0], argv[1:]) if argv else ("", [])
    if cmd == "init":
        if db_path().exists():
            print(f"exists: {db_path()}")
        else:
            save(load())
            print(f"created: {db_path()}")
        return 0
    if cmd == "add":
        return cmd_add(args)
    if cmd == "set":
        return cmd_set(args)
    if cmd == "verify":
        return cmd_verify()
    db = load()
    if cmd == "status":
        roles = [r for r in db["roles"] if not args or r["status"] == args[0]]
        for r in sorted(roles, key=lambda r: -r["fit"]):
            print(row(r))
        return 0
    if cmd == "next":
        n = int(args[0]) if args else 5
        queue = [r for r in db["roles"] if r["status"] in ("sourced", "verified")]
        queue.sort(key=lambda r: (SPONSOR_RANK.get(r["sponsor"], 1), -r["fit"]))
        for r in queue[:n]:
            print(row(r))
        return 0
    if cmd == "has" and len(args) == 1:
        return 0 if find(db, args[0]) else 1
    if cmd == "stats":
        counts = {}
        for r in db["roles"]:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
        print(f"TOTAL\t{len(db['roles'])}")
        for k in sorted(counts):
            print(f"{k}\t{counts[k]}")
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
