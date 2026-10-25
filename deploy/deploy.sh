#!/usr/bin/env bash
# Deploys comment-sidecar to the web space. Your real config.php and deploy.env are gitignored, see the *.example.* files.
# usage: deploy/deploy.sh [--dry-run] [--skip-tests]
# Needs deploy/config.php (production config) and deploy/deploy.env (SSH_TARGET, REMOTE_DIR, BASE_URL, SMOKE_TEST_SITES).
# Create them from deploy/config.example.php and deploy/deploy.example.env.
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${DEPLOY_DIR}/.." && pwd)"
DRY_RUN=false
SKIP_TESTS=false
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --skip-tests) SKIP_TESTS=true ;;
        *) echo "unknown argument: $arg"; exit 1 ;;
    esac
done

for f in config.php deploy.env; do
    [[ -f "${DEPLOY_DIR}/${f}" ]] || { echo "missing ${DEPLOY_DIR}/${f}. Copy the matching .example file in that folder to ${f} and fill it in."; exit 1; }
done
# shellcheck disable=SC1091
source "${DEPLOY_DIR}/deploy.env"
: "${SSH_TARGET:?}" "${REMOTE_DIR:?}" "${BASE_URL:?}" "${SMOKE_TEST_SITES:?}"

if grep -q "TODO" "${DEPLOY_DIR}/deploy.env" && [[ "$DRY_RUN" == false ]]; then
    echo "deploy.env still contains a TODO. Please verify it first (REMOTE_DIR)."; exit 1
fi

echo "== target: ${SSH_TARGET}:${REMOTE_DIR} (${BASE_URL}), dry run: ${DRY_RUN}"

if [[ "$SKIP_TESTS" == false ]]; then
    echo "== running tests (needs 'docker compose up')"
    # PYTEST can override the command. otherwise use uv (see README) or a pytest on the PATH
    if [[ -n "${PYTEST:-}" ]]; then PYTEST_CMD=("${PYTEST}")
    elif command -v uv >/dev/null; then PYTEST_CMD=(uv run pytest)
    elif command -v pytest >/dev/null; then PYTEST_CMD=(pytest)
    else echo "neither uv nor pytest found. Install the test dependencies (README) or use --skip-tests."; exit 1
    fi
    (cd "${ROOT_DIR}" && "${PYTEST_CMD[@]}" -q test)
fi

RSYNC_FLAGS=(-avz)
[[ "$DRY_RUN" == true ]] && RSYNC_FLAGS+=(--dry-run)

echo "== uploading code"
# whitelist. never uploads src/config.php, phpinfo.php or the playgrounds. no --delete.
rsync "${RSYNC_FLAGS[@]}" \
    --include='comment-sidecar.php' --include='comment-sidecar-js-delivery.php' \
    --include='unsubscribe.php' --include='common.php' --include='comment-sidecar.js' \
    --include='translations/' --include='translations/*.php' \
    --include='form-templates/' --include='form-templates/*.html' \
    --exclude='*' \
    "${ROOT_DIR}/src/" "${SSH_TARGET}:${REMOTE_DIR}/"

echo "== uploading production config"
rsync "${RSYNC_FLAGS[@]}" "${DEPLOY_DIR}/config.php" "${SSH_TARGET}:${REMOTE_DIR}/config.php"

if [[ "$DRY_RUN" == true ]]; then
    echo "== dry run finished. nothing was changed."
    exit 0
fi

echo "== restricting config permissions"
# macOS' rsync doesn't support --chmod, so do it over ssh
ssh "${SSH_TARGET}" chmod 600 "${REMOTE_DIR}/config.php"

echo "== smoke tests"
fail() { echo "SMOKE TEST FAILED: $1"; exit 1; }
check_body() { # $1 label, $2 body
    if grep -qE 'Warning:|Deprecated:|Fatal error|Notice:' <<<"$2"; then fail "$1 contains PHP errors"; fi
}
status() { curl -s -o /dev/null -w '%{http_code}' "$1"; }

for site in ${SMOKE_TEST_SITES}; do
    url="${BASE_URL}comment-sidecar-js-delivery.php?site=${site}"
    body="$(curl -s -w '\n%{http_code}' "$url")"
    code="${body##*$'\n'}"; body="${body%$'\n'*}"
    [[ "$code" == "200" ]] || fail "js delivery for ${site} returned ${code}"
    grep -q "const SITE = \"${site}\"" <<<"$body" || fail "js delivery for ${site} doesn't contain the site key"
    check_body "js delivery for ${site}" "$body"

    url="${BASE_URL}comment-sidecar.php?site=${site}&path=/smoke-test/"
    body="$(curl -s -w '\n%{http_code}' "$url")"
    code="${body##*$'\n'}"; body="${body%$'\n'*}"
    [[ "$code" == "200" ]] || fail "comments for ${site} returned ${code}"
    python3 -c 'import json,sys; json.loads(sys.argv[1])' "$body" || fail "comments for ${site} are no valid json"
    echo "ok: ${site}"
done
[[ "$(status "${BASE_URL}comment-sidecar-js-delivery.php?site=does-not-exist.invalid")" == "400" ]] || fail "unknown site is not rejected (old code still deployed?)"
echo "ok: unknown site is rejected"

if [[ -n "${CSS_COPY_TO:-}" ]]; then
    echo "== copying css to ${CSS_COPY_TO}"
    cp -f "${ROOT_DIR}/src/comment-sidecar-basic.css" "${CSS_COPY_TO}"
fi
echo "== done"
