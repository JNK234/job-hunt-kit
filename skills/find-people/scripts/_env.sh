#!/usr/bin/env bash
# ABOUTME: Shared key loader for find-people scripts; sourced, never run directly.
# ABOUTME: Uses env vars first, then the workspace .env ($JOB_HUNT_HOME/.env or ./job-hunt/.env).

# load_key VAR_NAME : sets VAR_NAME from the environment or the workspace .env file.
load_key() {
  local name="$1" file line val
  [ -n "${!name:-}" ] && return 0
  if [ -n "${JOB_HUNT_HOME:-}" ]; then file="${JOB_HUNT_HOME}/.env"; else file="./job-hunt/.env"; fi
  [ -f "$file" ] || return 1
  line=$(grep -E "^[[:space:]]*(export[[:space:]]+)?${name}=" "$file" | tail -n 1 || true)
  [ -n "$line" ] || return 1
  val="${line#*=}"
  val="${val%\"}"; val="${val#\"}"; val="${val%\'}"; val="${val#\'}"
  [ -n "$val" ] || return 1
  printf -v "$name" '%s' "$val"
  export "$name"
}
