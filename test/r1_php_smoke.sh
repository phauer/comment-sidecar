#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-18080}"
BASE_URL="http://127.0.0.1:${PORT}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$(mktemp)"
BODY_FILE="$(mktemp)"
HEADERS_FILE="$(mktemp)"

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]]; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
    wait "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
  rm -f "${LOG_FILE}" "${BODY_FILE}" "${HEADERS_FILE}"
}
trap cleanup EXIT

php -S "127.0.0.1:${PORT}" -t "${ROOT_DIR}/src" >"${LOG_FILE}" 2>&1 &
SERVER_PID=$!

for _ in $(seq 1 50); do
  if curl -fsS "${BASE_URL}/comment-sidecar-js-delivery.php" >/dev/null 2>&1; then
    break
  fi
  sleep 0.1
done

fail() {
  echo "FAIL: $*" >&2
  echo "--- PHP server log ---" >&2
  cat "${LOG_FILE}" >&2 || true
  exit 1
}

request() {
  local method="$1"
  local url="$2"
  shift 2
  curl -sS -X "${method}" -D "${HEADERS_FILE}" -o "${BODY_FILE}" "$@" "${url}"
}

status_code() {
  awk 'NR==1 {print $2}' "${HEADERS_FILE}"
}

header_value() {
  local name="$1"
  awk -v target="${name}" 'BEGIN{IGNORECASE=1} $0 ~ "^" target ":" {sub(/\r$/,""); sub(/^[^:]+:[[:space:]]*/,""); print; exit}' "${HEADERS_FILE}"
}

# Widget delivery must be served as JavaScript.
request GET "${BASE_URL}/comment-sidecar-js-delivery.php"
[[ "$(status_code)" == "200" ]] || fail "widget delivery did not return 200"
[[ "$(header_value Content-Type)" == "application/javascript; charset=UTF-8" ]] \
  || fail "unexpected widget MIME type: $(header_value Content-Type)"

# Malformed JSON must not turn into a PHP TypeError/fatal.
request POST "${BASE_URL}/comment-sidecar.php" \
  -H 'Content-Type: application/json' --data-binary '{bad json'
[[ "$(status_code)" == "400" ]] || fail "malformed JSON did not return 400"
jq -e '.message == "Request body must contain a valid JSON object."' "${BODY_FILE}" >/dev/null \
  || fail "malformed JSON response is not valid/expected JSON"

# Wrong JSON types must be rejected before DB access.
request POST "${BASE_URL}/comment-sidecar.php" \
  -H 'Content-Type: application/json' \
  --data-binary '{"author":[],"content":"x","site":"s","path":"/"}'
[[ "$(status_code)" == "400" ]] || fail "array author did not return 400"

# Missing Origin must not emit warnings; OPTIONS remains valid.
request OPTIONS "${BASE_URL}/comment-sidecar.php"
[[ "$(status_code)" == "200" ]] || fail "OPTIONS without Origin did not return 200"
[[ -z "$(header_value Access-Control-Allow-Origin)" ]] \
  || fail "OPTIONS without Origin unexpectedly returned ACAO"

# Allowed origin receives CORS headers.
request OPTIONS "${BASE_URL}/comment-sidecar.php" \
  -H 'Origin: http://testdomain.com' \
  -H 'Access-Control-Request-Method: POST'
[[ "$(header_value Access-Control-Allow-Origin)" == "http://testdomain.com" ]] \
  || fail "allowed Origin did not receive matching ACAO"
[[ "$(header_value Access-Control-Allow-Methods)" == "GET, POST" ]] \
  || fail "unexpected Access-Control-Allow-Methods"

# Disallowed origin receives no ACAO.
request OPTIONS "${BASE_URL}/comment-sidecar.php" \
  -H 'Origin: https://evil.example'
[[ -z "$(header_value Access-Control-Allow-Origin)" ]] \
  || fail "disallowed Origin received ACAO"

# Unsupported methods are explicit.
request PUT "${BASE_URL}/comment-sidecar.php"
[[ "$(status_code)" == "405" ]] || fail "PUT did not return 405"
[[ "$(header_value Allow)" == "GET, POST, OPTIONS" ]] || fail "unexpected Allow header"

# UTF-8 length is counted as characters, not bytes.
python3 - <<'PY' >"${BODY_FILE}.json"
import json
print(json.dumps({
    "author": "가" * 41,
    "content": "댓글",
    "site": "s",
    "path": "/"
}, ensure_ascii=False))
PY
request POST "${BASE_URL}/comment-sidecar.php" \
  -H 'Content-Type: application/json' --data-binary "@${BODY_FILE}.json"
rm -f "${BODY_FILE}.json"
[[ "$(status_code)" == "400" ]] || fail "41-character Korean author did not return 400"
jq -e '.message == "author value exceeds maximal length of 40"' "${BODY_FILE}" >/dev/null \
  || fail "unexpected Korean length validation response"

if grep -Eqi 'warning|fatal error|uncaught|deprecated' "${LOG_FILE}"; then
  fail "PHP runtime emitted warning/fatal/deprecation"
fi

echo "PASS: PHP runtime smoke tests"
