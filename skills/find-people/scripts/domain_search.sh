#!/usr/bin/env bash
# ABOUTME: Hunter domain-search wrapper that lists only emails found in real public sources (sources > 0).
# ABOUTME: Pattern guesses (sources 0, common on catch-all domains) are dropped and counted, never shown as candidates.
#
# Usage:
#   ./domain_search.sh <domain> [limit]      # limit defaults to 10 (free-plan max)
# Output: one candidate per line: confidence  email  First Last - Position  (sources=N)
# Exit 3 if no Hunter key is configured (use the manual fallback in SKILL.md).

set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "${DIR}/_env.sh"
load_key HUNTER_API_KEY || { echo "NO_KEY: HUNTER_API_KEY not set (env var, \$JOB_HUNT_HOME/.env, or ./job-hunt/.env). Use the manual fallback." >&2; exit 3; }

[ -n "${1:-}" ] || { echo "usage: $0 <domain> [limit]"; exit 2; }
domain="$1"; limit="${2:-10}"

r=$(curl -s --get "https://api.hunter.io/v2/domain-search" \
  --data-urlencode "domain=${domain}" --data-urlencode "limit=${limit}" \
  --data-urlencode "api_key=${HUNTER_API_KEY}")

if echo "$r" | jq -e '.errors' >/dev/null 2>&1; then
  echo "$r" | jq -r '.errors[] | "HUNTER_ERROR: \(.id // "") \(.details // "")"' >&2
  exit 1
fi

pattern=$(echo "$r" | jq -r '.data.pattern // "unknown"')
accept_all=$(echo "$r" | jq -r '.data.accept_all // false')
dropped=$(echo "$r" | jq '[.data.emails[]? | select((.sources | length) == 0)] | length')
echo "# domain=${domain} pattern=${pattern} accept_all=${accept_all} dropped_guesses=${dropped}" >&2
echo "$r" | jq -r '.data.emails[]? | select((.sources | length) > 0)
  | "\(.confidence)\t\(.value)\t\(.first_name // "") \(.last_name // "") - \(.position // "")\t(sources=\(.sources | length))"'
