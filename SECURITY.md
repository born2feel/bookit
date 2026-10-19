# Security Policy

## Reporting a vulnerability

Please **do not** open a public issue for security problems.
Use GitHub's [private vulnerability reporting](https://github.com/born2feel/bookit/security/advisories/new)
instead. I will get back to you as soon as possible.

## Handling secrets

- The bot token is read **only** from the `BOT_TOKEN` environment variable (or a local `.env` file).
- `.env` is listed in `.gitignore` and `.dockerignore` — never commit it.
- If a token has leaked, revoke it immediately via [@BotFather](https://t.me/BotFather) (`/revoke`)
  and put the new one into `.env`.
- `docker-compose.yml` refuses to start without an explicit `POSTGRES_PASSWORD`.

## Hardening already in place

- Admin handlers are guarded by the `IsAdmin` filter on both messages and callback queries.
- Clients can only cancel their own bookings (ownership is checked in the services layer).
- All user-provided text is HTML-escaped before it is sent with `parse_mode=HTML`.
- The Docker image runs as a non-root user; PostgreSQL is not exposed outside the compose network.
- CI runs with a read-only `GITHUB_TOKEN`; Dependabot keeps dependencies up to date.
