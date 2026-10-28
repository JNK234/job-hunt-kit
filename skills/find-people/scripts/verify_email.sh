#!/usr/bin/env bash
# ABOUTME: SMTP-level email verification gate for find-people outreach (Hunter email-verifier).
# ABOUTME: An email is SAFE-TO-SEND only if smtp_check=true AND status=valid AND score>=THRESHOLD AND not catch-all.
#
# Why this exists: Hunter domain-search `sources>=1` is NOT proof a mailbox is live
# (a single stale source can list a since-deleted address that fails SMTP). And
# email-verifier "deliverable" on a catch-all domain still returns sources=0 for
# pattern GUESSES. The only honest gate is a live SMTP check. This script enforces it.
#
# Usage:
#   ./verify_email.sh <email> [email2 email3 ...]
# Output (one line per email, tab-separated):
#   <email>  VERDICT  status=<>  score=<>  smtp=<>  accept_all=<>  sources=<>
# VERDICT is one of:
#   SAFE        -> smtp_check=true, status=valid, score>=THRESHOLD, accept_all=false  (draft OK)
#   RISKY       -> deliverable but accept_all=true OR score below THRESHOLD           (do NOT trust; confirm via 2nd source)
#   BLOCKED     -> server refuses verification probes; unknowable                     (human decides; only with an independent source)
#   REJECT      -> undeliverable / invalid / smtp_check=false                          (never draft to this)
#
# Exit code: 0 if ALL inputs are SAFE, 1 otherwise, 3 if no Hunter key is configured.

set -euo pipefail
THRESHOLD="${VERIFY_SCORE_THRESHOLD:-80}"   # min Hunter confidence to call SAFE
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "${DIR}/_env.sh"
load_key HUNTER_API_KEY || { echo "NO_KEY: HUNTER_API_KEY not set (env var, \$JOB_HUNT_HOME/.env, or ./job-hunt/.env). Use the manual fallback." >&2; exit 3; }

[ "$#" -ge 1 ] || { echo "usage: $0 <email> [email2 ...]"; exit 2; }

all_safe=0
for e in "$@"; do
  r=$(curl -s --get "https://api.hunter.io/v2/email-verifier" \
    --data-urlencode "email=${e}" --data-urlencode "api_key=${HUNTER_API_KEY}")
  # Extract each field explicitly (null-safe — positional @tsv read breaks when fields are null).
  status=$(echo "$r"     | jq -r '.data.status // "null"')
  score=$(echo "$r"      | jq -r '.data.score // 0')
  smtp=$(echo "$r"       | jq -r '.data.smtp_check // false')
  accept_all=$(echo "$r" | jq -r '.data.accept_all // false')
  sources=$(echo "$r"    | jq -r '.data.sources // [] | length')
  raw_smtp=$(echo "$r"   | jq -r 'if .data.smtp_check == null then "null" else "set" end')
  raw_result=$(echo "$r" | jq -r 'if .data.result == null then "null" else "set" end')
  verdict="REJECT"
  if [ "$smtp" = "true" ] && [ "$status" = "valid" ]; then
    if [ "$accept_all" = "true" ] || [ "$score" -lt "$THRESHOLD" ]; then
      verdict="RISKY"
    else
      verdict="SAFE"
    fi
  elif [ "$raw_smtp" = "null" ] && [ "$raw_result" = "null" ] && echo "$r" | jq -e '.data' >/dev/null 2>&1; then
    # Hunter returned all-null: the mail server blocks verification probes (anti-harvesting).
    # This is UNKNOWABLE, not undeliverable. Usable ONLY if the address came from an
    # independent trusted source AND matches the org's known pattern. Human-gated.
    verdict="BLOCKED"
  fi
  [ "$verdict" = "SAFE" ] || all_safe=1
  printf '%s\t%s\tstatus=%s\tscore=%s\tsmtp=%s\taccept_all=%s\tsources=%s\n' \
    "$e" "$verdict" "$status" "$score" "$smtp" "$accept_all" "$sources"
done
exit $all_safe
