# App Template

The company standard for building **Databricks Apps**: a Vite + React frontend and a Flask backend, deployed to Databricks from Azure DevOps. Every new app starts from this repository.

```
Browser ──► Databricks Apps proxy ──► Flask (gunicorn) ──┬──► Lakebase (Postgres)      SQLAlchemy + psycopg
            (signs the user in,        │  /api/*          ├──► SQL warehouse / UC        SQLAlchemy + databricks-sqlalchemy
             adds X-Forwarded-*)       └  /* → React SPA  └──► Databricks REST APIs      databricks-sdk
```

| Layer | Stack |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS v4, shadcn/ui (Ventia theme), lucide-react, React Router, TanStack Query |
| Backend | Python 3.11, Flask, gunicorn, SQLAlchemy 2, Alembic, pydantic, Databricks SDK |
| Data | Lakebase (Postgres) for app data, Lakehouse (SQL warehouse) for analytics |
| Delivery | Databricks Asset Bundles, Azure DevOps Pipelines (workload identity federation) |

**Read next:** [docs/NEW_APP.md](docs/NEW_APP.md) to start an app, [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for where code goes, [docs/AUTH_AND_SECURITY.md](docs/AUTH_AND_SECURITY.md) **before you write any endpoint**, [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for CI/CD, and [docs/BRANDING.md](docs/BRANDING.md) for colours, type and charts.

## Prerequisites

Development is supported on **macOS and Windows**. CI checks the local workflow on both (`azure-pipelines/templates/dev-env-check.yml`).

| Tool | macOS | Windows |
|---|---|---|
| **Python 3.11** (matches the Databricks Apps runtime) | `brew install python@3.11` or python.org | python.org installer (includes the `py` launcher), or `winget install Python.Python.3.11` |
| **Node.js 22** | `nvm install` (reads `.nvmrc`) or `brew install node@22` | `winget install OpenJS.NodeJS.LTS`, or nvm-windows: `nvm install 22 && nvm use 22` |
| **Databricks CLI ≥ 1.21** | `brew tap databricks/tap && brew install databricks` | `winget install Databricks.DatabricksCLI` |
| **Git** | Xcode CLT or `brew install git` | Git for Windows |

Then sign in once: `databricks auth login --host https://<workspace>.azuredatabricks.net`.

Every project command is an npm script backed by Node helpers in `scripts/`, so the same commands work in Terminal, PowerShell, cmd and Git Bash. There is no Makefile and nothing needs bash.

`npm run setup` looks for `python3.11` on macOS and `py -3.11` on Windows. To use a specific interpreter, set `PYTHON`:

```bash
PYTHON=/opt/homebrew/bin/python3.11 npm run setup                      # macOS
$env:PYTHON="C:\Program Files\Python311\python.exe"; npm run setup  # Windows PowerShell
```

## Quick start

```bash
npm run setup      # creates .venv, installs Python + Node deps, pre-commit hooks, copies .env.example → .env
npm run dev        # starts local Postgres, applies migrations, then runs Flask on :8000 + Vite on :5173
```

Open **http://localhost:5173**. You're signed in as the stub user from `.env` (`LOCAL_DEV_USER_*`). The **Examples** page needs `DATABRICKS_CONFIG_PROFILE` and `DATABRICKS_WAREHOUSE_ID` set in `.env`.

## Creating a new app from this template

1. Create the repo from this template in Azure DevOps.
2. Rename the app in `databricks.yml` (`bundle.name`, `app_name` variables), `frontend/src/config/app.ts` and `frontend/index.html`.
3. Pick a unique Postgres schema (`DB_SCHEMA` in `app.yaml` and `.env`).
4. Set the workspace hosts in `databricks.yml` and create the ADO variable groups, environments and service connections.
5. Delete the `items` example once you have your own models.

The full checklist is in [docs/NEW_APP.md](docs/NEW_APP.md).

## Project structure

```
├── app.yaml               Databricks Apps runtime: start command + env
├── databricks.yml         Asset bundle: variables + targets (sandbox, dev, staging, prod)
├── resources/app.yml      The app resource: warehouse, Lakebase, scopes, permissions
├── azure-pipelines/       ci.yml (PRs), cd.yml (main → dev → staging → prod), templates/
├── scripts/               Cross-platform Node helpers used by npm scripts
├── backend/
│   ├── app/
│   │   ├── api/           HTTP layer: one blueprint per resource, thin handlers
│   │   ├── services/      Business logic + authorization rules
│   │   ├── models/        SQLAlchemy models (Lakebase)
│   │   ├── auth/          Identity, @public/@require_group, OBO + SP clients
│   │   ├── db/            Lakebase + Lakehouse engines, sessions, migrations runner
│   │   ├── config.py      All settings (env vars)
│   │   └── security.py    Security headers, same-origin checks
│   ├── migrations/        Alembic
│   └── tests/
├── frontend/src/
│   ├── pages/             One file per route
│   ├── components/layout/ App shell: sidebar, header, user menu
│   ├── components/ui/     shadcn/ui (generated: `npx shadcn@latest add <name>`)
│   ├── hooks/             TanStack Query hooks, one per resource
│   ├── lib/api.ts         The only fetch wrapper
│   └── config/nav.ts      Sidebar entries
└── docs/
```

Rules of thumb:
- A new endpoint is a route in `api/`, its logic in `services/`, and a hook in `frontend/src/hooks/`.
- A new page is a file in `pages/`, a route in `router.tsx` and an entry in `config/nav.ts`.

## Commands

| Command | What it does |
|---|---|
| `npm run setup` | One-time setup: venv, dependencies, pre-commit, `.env` |
| `npm run dev` | Start local Postgres (`db:up`), apply migrations (`migrate`), then run Flask (`:8000`) and Vite (`:5173`) together. `npm run dev --ignore-scripts` skips the first two steps |
| `npm run db:up` / `db:down` / `db:status` / `db:reset` | Start, stop, check, or wipe the local Postgres (keeps running in the background until `db:down` or a reboot) |
| `npm run migrate` | Apply migrations (`alembic upgrade head`) |
| `npm run migrate:new -- "add orders"` | Autogenerate a migration from model changes |
| `npm run lint` | Ruff, ESLint, TypeScript, Prettier |
| `npm run format` | Auto-fix formatting (Python + frontend) |
| `npm run test` | Pytest + Vitest |
| `npm run audit` | `pip-audit` + `npm audit` |
| `npm run build` | Build the frontend and assemble `.build/` (what gets deployed) |
| `npm run deploy:sandbox` | Build and deploy to your personal sandbox in the dev workspace |

## Environment variables

Locally these come from `.env`. In Databricks they come from `app.yaml`, app resources and the platform.

| Variable | Local | Databricks |
|---|---|---|
| `APP_ENV` | `local` | `production` (set in `app.yaml`; anything else refuses to start) |
| `DATABASE_URL` | local Postgres from `npm run db:up` | unset: uses injected `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGSSLMODE` |
| `DB_SCHEMA` | `app` | set in `app.yaml`, unique per app |
| `DATABRICKS_CONFIG_PROFILE` | your CLI profile | unset: platform injects `DATABRICKS_HOST/CLIENT_ID/CLIENT_SECRET` |
| `DATABRICKS_WAREHOUSE_ID` | a warehouse you can use | `valueFrom: sql-warehouse` |
| `LOCAL_DEV_USER_EMAIL/NAME/GROUPS` | stub identity | ignored |
| `RUN_MIGRATIONS_ON_START` | `false` | `true` |
| `LOG_LEVEL` | `INFO` | `INFO` |

## OBO vs service principal

| | On behalf of user (OBO) | Service principal (SP) |
|---|---|---|
| Identity | The signed-in user | The app itself |
| Permissions | User's own Unity Catalog grants | Grants given to the app |
| Use for | Reading governed Lakehouse data | App-owned data (Lakebase), shared lookups, background work |
| Authorization | Enforced by Databricks | **You** enforce it in `services/` |

```python
from app.auth.clients import obo_workspace_client, sp_workspace_client
from app.db.lakehouse import obo_connection, sp_engine

obo_workspace_client().current_user.me()  # → the user
sp_workspace_client().current_user.me()  # → the app's service principal

with obo_connection() as conn:  # SQL as the user
    conn.execute(text("SELECT * FROM main.sales.orders WHERE region = :r"), {"r": region})
with sp_engine().connect() as conn:  # SQL as the app
    ...
```

Try both on the **Examples** page. Details are in [docs/AUTH_AND_SECURITY.md](docs/AUTH_AND_SECURITY.md).

## Database and migrations

App data lives in **Lakebase**, in a schema owned by the app (`DB_SCHEMA`). Locally it's an embedded Postgres 16 (the same major version as Lakebase Provisioned). `npm run db:up` starts it from npm-installed binaries in the [`embedded-postgres`](https://github.com/leinelissen/embedded-postgres) packages, and its data lives in `.local/postgres`. It needs no Docker, no admin rights and no system service. To use a Postgres you already have instead, point `DATABASE_URL` at it and start the app with `npm run dev --ignore-scripts` (this skips `db:up` and `migrate`; run `npm run migrate` yourself).

1. Change or add a model in `backend/app/models/` and import it in `models/__init__.py`.
2. Run `npm run migrate:new -- "describe the change"`, then **review the generated file** in `backend/migrations/versions/`.
3. Run `npm run migrate` to apply it locally.

On deploy, migrations run once in the gunicorn master process before workers start (`RUN_MIGRATIONS_ON_START`). Keep migrations backwards compatible: the old version keeps serving while the new one starts.

## Deployment

| Event | Pipeline | Result |
|---|---|---|
| Pull request to `main` | `azure-pipelines/ci.yml` | Lint, tests (with Postgres), audits, build, `bundle validate` |
| Merge to `main` | `azure-pipelines/cd.yml` | Build once, deploy **dev**, then **staging** (approval), then **prod** (approval) |
| Developer laptop | `npm run deploy:sandbox` | Personal, name-prefixed copy in the dev workspace |

Pipelines authenticate with **workload identity federation**, so no secrets are stored in Azure DevOps. One-time setup is in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Security rules (must follow)

1. **Identity comes only from the proxy headers**, via `app.auth.current_user()`. Never trust a user ID or email from the request body, query string or a cookie.
2. **Every `/api` route requires a user** by default. Use `@public` only for things like health checks.
3. **Never log, return or store the user's access token.** It is only for OBO calls inside the request.
4. **SQL uses bound parameters only** (`text("... :param")`). Table and column names come from allow-lists.
5. **SP access means you own authorization.** Check ownership, roles or groups in `services/`.
6. **Secrets come from app resources** (`valueFrom`) or secret scopes. Never put them in code, `app.yaml` or ADO variables.
7. **Ask for the fewest `user_api_scopes`** your app needs.
8. **No `dangerouslySetInnerHTML`.** ESLint blocks it.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `No virtualenv found at .venv` | Run `npm run setup` |
| `connection refused` on port 5432 | Run `npm run db:up`, or restart `npm run dev` (Postgres doesn't restart by itself after a reboot) |
| `db:up` fails: port 5432 in use | Another Postgres is running. Stop it, or set `LOCAL_PG_PORT=5433` and change the port in `DATABASE_URL` in `.env` |
| `db:up` fails for another reason | Check `.local/postgres.log`. `npm run db:reset` re-creates the database and **deletes local data** |
| Port 8000 or 5173 already in use | Stop the other process, or change the port in `package.json` (`dev:api`) and `frontend/vite.config.ts` |
| Windows: `running scripts is disabled` in PowerShell | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once (needed for `npm`/`npx` shims) |
| Windows: Prettier reports every file changed | Your checkout has CRLF line endings. Run `git config core.autocrlf false`, then `git rm --cached -r .` and `git reset --hard` (`.gitattributes` forces LF) |
| Examples return 403/502 locally | Run `databricks auth login` for the profile in `.env` and set `DATABRICKS_WAREHOUSE_ID` |
| `relation "app.items" does not exist` | Run `npm run migrate` (`npm run dev` does this on start) |
| App refuses to start in Databricks with `APP_ENV` error | `app.yaml` must set `APP_ENV=production` |
| API calls fail with "session expired" | The Databricks login expired. Reload the page |
