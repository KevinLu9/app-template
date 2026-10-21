# Authentication, authorization and security

Databricks handles **authentication**: nobody reaches the app without signing in to the workspace and having `CAN_USE` on it. The app handles **authorization**, meaning what each signed-in user may see and do. This document covers how to do that safely.

## How identity reaches the app

The Databricks Apps proxy sets these headers on every request. It removes any client-sent versions first.

| Header | Meaning |
|---|---|
| `X-Forwarded-Email` | User's email |
| `X-Forwarded-User` | User's ID from the identity provider |
| `X-Forwarded-Preferred-Username` | Display name |
| `X-Forwarded-Access-Token` | User's OAuth token (only with user authorization enabled) |
| `X-Request-Id` | Unique request ID |

Read identity only through `app.auth.identity`:

```python
from app.auth import current_user

user = current_user()  # CurrentUser(user_id, email, display_name), or a 401 if missing
user.email  # safe to store, e.g. as created_by
user.access_token  # OBO only. Never log, return, store or cache it.
```

**Never** take identity from a request body, query string or cookie. In `services/items.py`, `created_by` comes from `current_user()`. A body containing `created_by` is rejected, because the pydantic models use `extra="forbid"`.

### Local development

There is no proxy locally. When `APP_ENV=local`, `identity.py` returns a stub user built from `LOCAL_DEV_USER_*` in `.env`. Three guards keep that stub out of production:

- `APP_ENV` defaults to `production`.
- `Settings` refuses to load if `APP_ENV` isn't `production` and `DATABRICKS_APP_NAME` is set (it is always set in Databricks Apps).
- `app.yaml` sets `APP_ENV=production` explicitly.

## Access control

- **Authentication is on by default.** `api/__init__.py` returns 401 for any `/api` route without an identity, unless the view is decorated with `@public`.
- **Groups:** `@require_group("app-admins")` checks the user's workspace groups, looked up as the user, once per request. The lookup needs the `iam.current-user:read` scope.
- **Ownership and row-level rules** belong in services. See `_owned_item()` in `services/items.py`.

## OBO vs service principal

Two identities can call Databricks. Choose deliberately, per call.

### Service principal (app authorization)

The app's own identity. Databricks injects `DATABRICKS_CLIENT_ID`/`DATABRICKS_CLIENT_SECRET`, and `Config()` picks them up.

```python
from app.auth.clients import sp_workspace_client
from app.db.lakehouse import sp_engine
from app.db.session import db_session  # Lakebase: always as the SP
```

- Grant the app's service principal only what it needs, through app resources or Unity Catalog grants.
- **Every user sees what the SP can see.** If the data isn't meant for everyone, filter it in the service, or use OBO instead.
- Good for: Lakebase app data, reference data everyone may read, writes the app controls.

### On behalf of the user (user authorization)

The signed-in user's identity, via `X-Forwarded-Access-Token`. It requires `user_api_scopes` in `resources/app.yml`, and users consent on first use.

```python
from app.auth.clients import obo_workspace_client
from app.db.lakehouse import obo_connection

with obo_connection() as conn:
    rows = conn.execute(text("SELECT * FROM main.finance.costs WHERE year = :y"), {"y": 2026})
```

- Unity Catalog applies the user's own grants, row filters and column masks. Databricks enforces the permissions for you.
- Ask only for the scopes you need. Common ones are `sql` (warehouse queries), `iam.current-user:read` (who am I, groups), `files` and `serving.serving-endpoints`.
- The token lives only for the request. A new engine is created per request and disposed afterwards (`NullPool`), so one user's connection is never reused for another.
- **Locally**, both OBO and SP run as your CLI profile, so OBO-vs-SP differences show up only once deployed. Use the Examples page in the sandbox target to check.

| Question | Choose |
|---|---|
| Should each user see only what UC lets *them* see? | OBO |
| Is the data owned by the app (Lakebase)? | SP |
| Does it run without a user (startup, background)? | SP |
| Must the audit log show the real user? | OBO |

## Hardening already in place

| Control | Where |
|---|---|
| Strict CSP (`self` only), `nosniff`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` | `security.py` |
| `Cache-Control: no-store` on API responses | `security.py` |
| Cross-origin `Origin` rejected on writes; non-JSON writes rejected (415) | `security.py` |
| 1 MB request body limit | `config.py` (`max_request_bytes`) |
| Generic error messages; details only in logs, with request ID | `errors.py` |
| Token redaction in logs; no headers in access logs | `log.py`, `gunicorn.conf.py` |
| Input validation with `extra="forbid"` | `services/*`, `validation.py` |
| Bound SQL parameters; table names from constants | `api/examples.py` |
| No `dangerouslySetInnerHTML` | `frontend/eslint.config.js` |
| Dependency audits and secret scanning | CI (`pip-audit`, `npm audit`), pre-commit (`gitleaks`) |

## Secrets

- Use app **secret resources** (a secret scope with key `READ`) and reference them from `app.yaml` with `valueFrom`. The value arrives as an env var. Read it in `config.py`.
- Never commit secrets or put them in `app.yaml` `value:` fields or ADO pipeline variables. Deploys use workload identity federation and need no secrets.
- `.env` is gitignored and only for local development.

## Review checklist for new endpoints

- [ ] It does not use `@public`, unless it really is public (and then returns nothing sensitive).
- [ ] The input is validated with a pydantic model that sets `extra="forbid"`.
- [ ] User-specific fields (owner, author) come from `current_user()`, never the body.
- [ ] Data read as the SP is filtered for the user, or the call uses OBO.
- [ ] SQL uses bound parameters. Identifiers come from an allow-list.
- [ ] No tokens or personal data are logged.
- [ ] There are tests for the 401/403 paths.
