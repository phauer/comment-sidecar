# R1 compatibility test matrix

This harness is for development/CI only. It does not change the production
runtime requirement: production remains Apache + PHP + MariaDB/MySQL, with no
Docker, Node.js server, Python server, Redis, worker, or cron requirement.

Run the fast DB-free PHP runtime checks first:

```bash
./test/r1_php_smoke.sh
```

Run the existing upstream pytest integration suite across the R1 target matrix:

```bash
./test/run_r1_matrix.sh
```

The matrix runner creates a test-only `.venv-r1-tests` environment and installs
`test/requirements-r1.txt`. This deliberately avoids the historical
`poetry.lock`, whose legacy format is not readable by current Poetry 2.x. The
upstream `pyproject.toml` and `poetry.lock` are left unchanged.

To avoid colliding with local web/database services, the harness uses
non-privileged host ports by default:

- HTTP: `18080`
- MariaDB/MySQL: `13306`
- MailHog SMTP: `11025`
- MailHog HTTP: `18025`

They can be overridden with `R1_HTTP_PORT`, `R1_MYSQL_PORT`,
`R1_MAILHOG_SMTP_PORT`, and `R1_MAILHOG_HTTP_PORT`.

The matrix is:

- PHP 8.2 + MariaDB 11.4
- PHP 8.4 + MariaDB 11.4
- PHP 8.2 + MySQL 8.4

`Dockerfile.r1` and `docker-compose.r1.yml` are test-only assets. The production
deployment remains upload-only PHP/JS/CSS/SQL.
