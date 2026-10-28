#!/bin/sh
set -eu
BASE="${SENTINEL_BASE_URL:-http://localhost:8000}"
TOKEN="${SENTINEL_TOKEN:?Set SENTINEL_TOKEN}"
curl -fsS "$BASE/live"
printf "\n"
curl -fsS "$BASE/ready"
printf "\n"
curl -fsS -H "Authorization: Bearer $TOKEN" "$BASE/api/v1/dashboard/scans"
printf "\n"
