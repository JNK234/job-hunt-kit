#!/usr/bin/env python3
# ABOUTME: Live ATS interrogation over public APIs (Ashby, Greenhouse, Lever): parse an apply URL,
# ABOUTME: list a board, dump a posting's exact form schema, and check liveness by board presence.
"""
Usage:
  ats.py parse <url>                       -> ats<TAB>slug<TAB>jobId
  ats.py board ashby|greenhouse|lever <slug>   -> id<TAB>title<TAB>location<TAB>type<TAB>url
  ats.py form  ashby|greenhouse|lever <slug> <jobId>
                                           -> REQUIRED|optional<TAB>type<TAB>title<TAB>options<TAB>flags
  ats.py alive <url>                       -> LIVE | DEAD | UNKNOWN

Exit codes: 0 ok, 2 bad args / unrecognized URL, 3 unreachable or dead, 4 posting not found,
5 recognized ATS without a public form schema (read the form in a browser instead).

Why: job forms are client-side rendered, so scraping the page yields only a title. HTTP 200 is not
liveness either (Ashby serves a 200 shell for any path). Board presence is the authoritative check.
"""
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"
TIMEOUT = 25

ASHBY_QUERY = (
    "query ApiJobPosting($organizationHostedJobsPageName: String!, $jobPostingId: String!) "
    "{ jobPosting(organizationHostedJobsPageName: $organizationHostedJobsPageName, "
    "jobPostingId: $jobPostingId) { title applicationForm { sections { fieldEntries "
    "{ field isRequired } } } } }"
)

# Field titles worth a human look before answering. Sponsorship questions are sometimes
# inverted ("authorized ... WITHOUT sponsorship?", "UNRESTRICTED work authorization?"), and
# some forms plant a decoy question addressed to an LLM that must be left blank.
FLAGS = [
    (re.compile(r"\bwithout\b|\bunrestricted\b|\brestrictions\b", re.I), "INVERTED-AUTH?"),
    (re.compile(r"if you are an? (llm|ai)|ai tool|language model", re.I), "AI-TRAP-LEAVE-BLANK"),
    (re.compile(r"u\.?s\.? person|export control|itar|security clearance|citizenship", re.I), "US-PERSON/EXPORT"),
    (re.compile(r"do not use (llms?|ai|chatgpt)", re.I), "NO-AI-DRAFTING"),
]


class AtsError(Exception):
    def __init__(self, msg, code=2):
        super().__init__(msg)
        self.code = code


def fetch(url, data=None):
    headers = {"User-Agent": UA}
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise AtsError(f"HTTP {e.code} from {url}", 3)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        raise AtsError(f"unreachable: {url} ({e})", 3)


def q(slug):
    return urllib.parse.quote(slug, safe="")


def parse(url):
    """Resolve an apply URL to (ats, slug, jobId).

    Strips the query string and a trailing /apply, /application or /apply-form first. Leaving
    those on yields a jobId that never matches the board, which silently marks live roles dead.
    """
    query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
    clean = url.split("?", 1)[0].split("#", 1)[0].rstrip("/")
    for suffix in ("/apply", "/application", "/apply-form"):
        if clean.endswith(suffix):
            clean = clean[: -len(suffix)]
    if "jobs.ashbyhq.com/" in clean:
        parts = clean.split("jobs.ashbyhq.com/", 1)[1].split("/")
        if len(parts) >= 2:
            return "ashby", urllib.parse.unquote(parts[0]), parts[1]
    if "greenhouse.io/" in clean:
        rest = clean.split("greenhouse.io/", 1)[1]
        m = re.search(r"/jobs/(\d+)", clean)
        if m:
            return "greenhouse", rest.split("/")[0], m.group(1)
        if "for" in query and ("token" in query or "gh_jid" in query):
            return "greenhouse", query["for"][0], (query.get("token") or query["gh_jid"])[0]
    if "lever.co/" in clean:
        parts = clean.split("lever.co/", 1)[1].split("/")
        if len(parts) >= 2:
            return "lever", parts[0], parts[1]
    if "myworkdayjobs.com" in clean or "workday" in clean:
        raise AtsError("WORKDAY: form is behind a candidate login. Handle manually; do not queue as drafted.", 5)
    for host, name in (("smartrecruiters.com", "SMARTRECRUITERS"), ("workable.com", "WORKABLE"), ("icims.com", "ICIMS")):
        if host in clean:
            raise AtsError(f"{name}: no public form schema. Read the live form with chrome-devtools take_snapshot.", 5)
    raise AtsError(f"unrecognized ATS url: {url} (read the live form in a browser)", 2)


def board(ats, slug):
    """Return [(id, title, location, type, url)] for every open posting on the board."""
    if ats == "ashby":
        data = fetch(f"https://api.ashbyhq.com/posting-api/job-board/{q(slug)}") or {}
        return [(j.get("id", ""), j.get("title", ""), j.get("location") or "", j.get("employmentType") or "",
                 j.get("jobUrl", "")) for j in data.get("jobs") or []]
    if ats == "greenhouse":
        data = fetch(f"https://boards-api.greenhouse.io/v1/boards/{q(slug)}/jobs") or {}
        return [(str(j.get("id", "")), j.get("title", ""), (j.get("location") or {}).get("name", ""), "",
                 j.get("absolute_url", "")) for j in data.get("jobs") or []]
    if ats == "lever":
        data = fetch(f"https://api.lever.co/v0/postings/{q(slug)}?mode=json") or []
        return [(j.get("id", ""), j.get("text", ""), (j.get("categories") or {}).get("location") or "",
                 (j.get("categories") or {}).get("commitment") or "", j.get("hostedUrl", "")) for j in data]
    raise AtsError(f"unknown ats: {ats}")


def flags_for(title):
    return ",".join(tag for rx, tag in FLAGS if rx.search(title or ""))


def form(ats, slug, job_id):
    """Return [(required, type, title, options, flags)] for the posting's application form."""
    rows = []
    if ats == "ashby":
        payload = {"operationName": "ApiJobPosting",
                   "variables": {"organizationHostedJobsPageName": slug, "jobPostingId": job_id},
                   "query": ASHBY_QUERY}
        data = fetch("https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobPosting", payload)
        posting = ((data or {}).get("data") or {}).get("jobPosting")
        if not posting:
            raise AtsError(f"ashby: posting {job_id} not found on board '{slug}' (closed or wrong id)", 4)
        for sec in (posting.get("applicationForm") or {}).get("sections") or []:
            for fe in sec.get("fieldEntries") or []:
                f = fe.get("field") or {}  # `field` is a JSON scalar, not a selection set
                opts = "|".join(str(v.get("label") or v.get("value")) for v in f.get("selectableValues") or [])
                rows.append(("REQUIRED" if fe.get("isRequired") else "optional", f.get("type", "?"),
                             f.get("title", "?"), opts))
    elif ats == "greenhouse":
        data = fetch(f"https://boards-api.greenhouse.io/v1/boards/{q(slug)}/jobs/{job_id}?questions=true")
        if not data:
            raise AtsError(f"greenhouse: job {job_id} not found on board '{slug}'", 4)
        for qn in data.get("questions") or []:
            f0 = (qn.get("fields") or [{}])[0]
            opts = "|".join(str(v.get("label")) for v in f0.get("values") or [])
            rows.append(("REQUIRED" if qn.get("required") else "optional", f0.get("type", "?"),
                         qn.get("label", "?"), opts))
    elif ats == "lever":
        data = fetch(f"https://api.lever.co/v0/postings/{q(slug)}?mode=json") or []
        if not any(j.get("id") == job_id for j in data):
            raise AtsError(f"lever: posting {job_id} absent from board '{slug}' (likely closed)", 4)
        rows = [("REQUIRED", "input_text", "Full name", ""), ("REQUIRED", "input_text", "Email", ""),
                ("optional", "input_text", "Phone", ""), ("REQUIRED", "input_file", "Resume", "")]
        print("WARNING: Lever hides custom questions from its public API. Read this form live "
              "(chrome-devtools take_snapshot) before drafting.", file=sys.stderr)
    else:
        raise AtsError(f"unknown ats: {ats}")
    return [r + (flags_for(r[2]),) for r in rows]


def alive(url):
    """Return 'LIVE', 'DEAD' or 'UNKNOWN' by checking the jobId against the live board."""
    ats, slug, job_id = parse(url)
    try:
        ids = {row[0] for row in board(ats, slug)}
    except AtsError:
        return "UNKNOWN"
    if not ids:
        # Empty can mean a client-rendered board (some Lever boards return [] while the page is
        # live) or a typo'd slug. Never kill a role on this alone.
        return "UNKNOWN"
    return "LIVE" if job_id in ids else "DEAD"


def main(argv):
    cmd, args = (argv[0], argv[1:]) if argv else ("", [])
    try:
        if cmd == "parse" and len(args) == 1:
            print("\t".join(parse(args[0])))
        elif cmd == "board" and len(args) == 2:
            for row in board(*args):
                print("\t".join(row))
        elif cmd == "form" and len(args) == 3:
            for row in form(*args):
                print("\t".join(row))
        elif cmd == "alive" and len(args) == 1:
            state = alive(args[0])
            print(state)
            return 0 if state == "LIVE" else 3
        else:
            print(__doc__, file=sys.stderr)
            return 2
    except AtsError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return e.code
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
