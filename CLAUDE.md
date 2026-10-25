# Comment-Sidecar Project Rules

Plain PHP backend (no Composer, no dependencies) plus one JS file, MySQL or MariaDB, pytest integration tests against a docker stack. Code and comments in English.

## Public Repo, Private Deployment

- This repo is public. Never commit domains, mail addresses, hosts, credentials or deploy scripts of a real installation.
- `deploy/deploy.sh`, `deploy/config.example.php` and `deploy/deploy.example.env` are tracked and generic. The real `deploy/config.php`, `deploy/deploy.env` and one-off SQL are gitignored (whitelist in `.gitignore`). Tests, docs and examples use generic names (`localhost`, `example.com`).
- A new option in `src/config.php` must be added to `deploy/config.example.php` too. `test/test_deploy_examples.py` checks it.
- `src/config.php` is the dev config used by docker and the tests. Production gets its own `config.php` from your private `deploy/config.php`.

## Running the Tests

- `docker compose up -d`, then `poetry run pytest test` (Poetry needs Python below 3.15, `mysql-connector-python` still uses `ssl.PROTOCOL_TLSv1`).
- The suite needs port 80, 3306 and 8025. If another container holds port 80, stop it first and restart it afterwards.
- Tests rewrite `RATE_LIMIT_THRESHOLD_SECONDS` in `src/config.php` and `conftest.py` restores it. Keep that constant's format.
- Run with `display_errors=On` (the Dockerfile does). A PHP warning in a response body breaks the JSON and the tests catch it.

## Multi-Site Design

- One installation and one DB serve many sites. `SITES` in `config.php` maps a site key to url, language, notification mail, allowed origins, template and button classes. `DEFAULT_SITE` keeps embeds without `?site=` working.
- Every entry point validates the site (`getSiteConfig()` in `common.php`). Origins are checked per site, same-origin requests and requests without `Origin` stay allowed.
- Per-site data must never come from global constants again. Add new per-site options to the `SITES` entries.
- Not done yet: a reply's parent should belong to the same site and path.

## PHP 8 Lessons

- Keep the JSON API stable across PHP versions: `PDO::ATTR_STRINGIFY_FETCHES` (8.1 returns native ints) and explicit `htmlspecialchars` flags (8.1 changed the default and would escape single quotes).
- Catch `Throwable`, not `Exception`. TypeErrors are `Error`s. Never echo exception messages for unexpected errors (database messages leak users and hosts). `respondWithError()` logs them instead.
- No `${var}` interpolation, guard optional array keys and `$_SERVER` entries, build JSON with `json_encode`.
- Strip CR and LF from anything that ends up in mail headers.

## Docker Environment

- Current `mhsendmail` rejects the `-t -i` flags PHP passes, so `sendmail_path` points to a small wrapper script.
- xdebug 3 uses `xdebug.mode` and `client_*` settings.

## Deployment Notes

- macOS ships openrsync. It has no `--chmod`, set permissions over ssh instead.
- Deploy order for breaking config changes: deploy code and config together, then run the smoke tests (every site, plus an unknown site must return 400).
- Back up the DB and the server files before every deploy. Rolling back means re-uploading the old files.
