#!/usr/bin/env python3
# ABOUTME: Deterministic generator of LinkedIn + search-engine people-search URLs for outreach targeting.
# ABOUTME: Given company/team, emits ready-to-open searches for hiring-manager / senior-IC / director tiers.
import sys, json, urllib.parse

# Title keyword sets per target tier (NOT recruiters)
TIERS = {
    "hiring_manager": ["Engineering Manager", "Hiring Manager", "Team Lead", "Manager", "Head of"],
    "senior_ic":      ["Senior", "Staff", "Principal", "Member of Technical Staff", "Forward Deployed"],
    "director":       ["Director", "VP", "Vice President", "Head of Engineering"],
}

def li_people_url(company, title_terms, extra=""):
    # LinkedIn people search by keyword (company + title + optional team term)
    kw = f'{company} ' + " OR ".join(f'"{t}"' for t in title_terms)
    if extra:
        kw = f'{company} "{extra}" ' + " OR ".join(f'"{t}"' for t in title_terms)
    q = urllib.parse.quote(kw)
    return f"https://www.linkedin.com/search/results/people/?keywords={q}&origin=GLOBAL_SEARCH_HEADER"

def li_company_filtered_url(title_terms, extra=""):
    # Title-keyword search you then filter by 'Current company' in the LinkedIn UI
    base = " OR ".join(f'"{t}"' for t in title_terms)
    kw = f'{extra} {base}' if extra else base
    return f"https://www.linkedin.com/search/results/people/?keywords={urllib.parse.quote(kw)}"

def search_query(company, title_terms, team=""):
    terms = " OR ".join(f'"{t}"' for t in title_terms[:3])
    team_q = f'"{team}" ' if team else ""
    return f'site:linkedin.com/in "{company}" {team_q}({terms})'

def build(company, team=""):
    out = {"company": company, "team": team, "targets": {}}
    for tier, terms in TIERS.items():
        q = search_query(company, terms, team)
        out["targets"][tier] = {
            "search_query": q,
            "google": f"https://www.google.com/search?q={urllib.parse.quote(q)}",
            "duckduckgo": f"https://duckduckgo.com/?q={urllib.parse.quote(q)}",
            "linkedin": li_people_url(company, terms, team),
            "linkedin_title_filter": li_company_filtered_url(terms, team),
            "title_keywords": terms,
        }
    return out

if __name__ == "__main__":
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        sys.exit('usage: build_searches.py "<Company>" ["<Team>"]')
    company = sys.argv[1]
    team    = sys.argv[2] if len(sys.argv) > 2 else ""
    print(json.dumps(build(company, team), indent=2))
