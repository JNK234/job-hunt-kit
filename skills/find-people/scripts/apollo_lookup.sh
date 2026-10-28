#!/usr/bin/env bash
# ABOUTME: Apollo.io people/match lookup that resolves a named IC to an email with a verification status.
# ABOUTME: Use when Hunter has no SAFE email for the right target (peer engineers, ICs).
#
# Usage:
#   ./apollo_lookup.sh "First Last" "Company"        # match by name + org
#   ./apollo_lookup.sh --linkedin "<linkedin_url>"   # match by LinkedIn URL
#
# Trust: only act on email_status == "verified". "guessed"/"unavailable" -> do NOT draft;
# fall back to manual confirmation. ALWAYS re-run a verified hit through verify_email.sh
# (the SMTP gate) before drafting — two independent confirmations beat one.
# Exit 3 if no Apollo key is configured.

set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "${DIR}/_env.sh"
load_key APOLLO_API_KEY || { echo "NO_KEY: APOLLO_API_KEY not set (env var, \$JOB_HUNT_HOME/.env, or ./job-hunt/.env). apollo.io -> Settings -> API." >&2; exit 3; }

if [ "${1:-}" = "--linkedin" ]; then
  [ -n "${2:-}" ] || { echo "usage: $0 --linkedin <url>"; exit 2; }
  body=$(jq -n --arg u "$2" '{linkedin_url:$u, reveal_personal_emails:false}')
else
  { [ -n "${1:-}" ] && [ -n "${2:-}" ]; } || { echo "usage: $0 \"First Last\" \"Company\"  |  $0 --linkedin <url>"; exit 2; }
  first="${1%% *}"; last="${1#* }"
  body=$(jq -n --arg f "$first" --arg l "$last" --arg o "$2" \
    '{first_name:$f, last_name:$l, organization_name:$o, reveal_personal_emails:false}')
fi

curl -s -X POST "https://api.apollo.io/api/v1/people/match" \
  -H "Content-Type: application/json" -H "X-Api-Key: ${APOLLO_API_KEY}" \
  -d "$body" \
| jq '{name:.person.name, title:.person.title, email:.person.email, email_status:.person.email_status, org:.person.organization.name, linkedin:.person.linkedin_url}'

echo "" >&2
echo ">> If email_status=verified, run verify_email.sh <that-email> (final SMTP gate)" >&2
