#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

export R1_HTTP_PORT="${R1_HTTP_PORT:-18080}"
export R1_MYSQL_PORT="${R1_MYSQL_PORT:-13306}"
export R1_MAILHOG_SMTP_PORT="${R1_MAILHOG_SMTP_PORT:-11025}"
export R1_MAILHOG_HTTP_PORT="${R1_MAILHOG_HTTP_PORT:-18025}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required to run the DB compatibility matrix." >&2
  exit 2
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose v2 is required." >&2
  exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to run the upstream pytest integration suite." >&2
  exit 2
fi

VENV_DIR="${R1_TEST_VENV:-${ROOT_DIR}/.venv-r1-tests}"
PYTEST_BIN="${VENV_DIR}/bin/pytest"

prepare_test_venv() {
  if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
    python3 -m venv "${VENV_DIR}"
  fi
  "${VENV_DIR}/bin/python" -m pip install --disable-pip-version-check -q --upgrade pip
  "${VENV_DIR}/bin/python" -m pip install --disable-pip-version-check -q -r test/requirements-r1.txt
}

prepare_test_venv

cleanup() {
  docker compose -f docker-compose.r1.yml down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

run_case() {
  local php_version="$1"
  local db_image="$2"
  local label="$3"

  echo
  echo "=== ${label}: PHP ${php_version} + ${db_image} ==="
  cleanup

  PHP_VERSION="${php_version}" DB_IMAGE="${db_image}" \
    docker compose -f docker-compose.r1.yml up -d --build

  # Compose waits for the DB healthcheck before starting Apache, but make the
  # HTTP readiness explicit before invoking the existing pytest suite.
  for _ in $(seq 1 60); do
    if curl -fsS "http://127.0.0.1:${R1_HTTP_PORT}/comment-sidecar-js-delivery.php" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  curl -fsS "http://127.0.0.1:${R1_HTTP_PORT}/comment-sidecar-js-delivery.php" >/dev/null

  COMMENT_SIDECAR_BASE_URL="http://127.0.0.1:${R1_HTTP_PORT}" \
  COMMENT_SIDECAR_PUBLIC_BASE_URL="http://localhost" \
  MAILHOG_BASE_URL="http://127.0.0.1:${R1_MAILHOG_HTTP_PORT}/api/" \
  MYSQL_PORT="${R1_MYSQL_PORT}" \
    "${PYTEST_BIN}" -q
  echo "PASS: ${label}"
}

run_case "8.2" "mariadb:11.4" "php82-mariadb"
run_case "8.4" "mariadb:11.4" "php84-mariadb"
run_case "8.2" "mysql:8.4"   "php82-mysql8"

echo
echo "PASS: complete R1 DB compatibility matrix"
