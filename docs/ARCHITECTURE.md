# Architecture

## Request flow

```
Browser ─► Databricks Apps proxy ─► gunicorn ─► Flask
              │ authenticates the user (workspace SSO)
              │ strips client-sent X-Forwarded-* headers, sets its own
              │ forwards the user's token (X-Forwarded-Access-Token) when user authorization is enabled
```

In production, one Flask process serves both:

- `/api/*`: JSON endpoints (blueprints in `backend/app/api/`)
- everything else: the built React app from `frontend/dist`, with `index.html` as the fallback for client-side routes

Frontend and API share an origin, so there is **no CORS**. Locally, Vite serves the frontend on `:5173` and proxies `/api` to Flask on `:8000` (the same port Databricks Apps uses). The browser still only ever talks to one origin.

## Backend layers

| Layer | Folder | Responsibility | Must not |
|---|---|---|---|
| HTTP | `app/api/` | Parse and validate input (`parse_body`), call a service, shape the response | Query the database directly or contain business rules |
| Service | `app/services/` | Business rules, **authorization checks**, transactions | Touch `request` (take `CurrentUser` and validated data as arguments) |
| Model | `app/models/` | SQLAlchemy tables (Lakebase) | Contain request logic |
| Data access | `app/db/` | Engines, sessions, the Lakehouse connection helpers | Be bypassed: don't create engines elsewhere |
| Auth | `app/auth/` | Identity, `@public`, `@require_group`, OBO/SP clients | Be reimplemented per app |

Each request gets one Lakebase `Session` (`db_session()`), which is closed at teardown. Commit explicitly in the service.

`create_app()` in `app/__init__.py` wires the app in this order: settings → logging → security → error handlers → DB session → API blueprints → SPA serving.

## Frontend structure

- `router.tsx`: every route, all rendered inside `AppShell` (sidebar, header, user menu).
- `config/nav.ts`: sidebar entries. One line per page.
- `lib/api.ts`: the **only** place that calls `fetch`. It throws `ApiError` with the backend's error code and request ID.
- `hooks/`: one TanStack Query hook file per backend resource. Components never call `api` directly.
- `components/ui/`: shadcn components, owned by the repo. Regenerate or add them with the shadcn CLI and don't hand-edit them.
- `components/states.tsx`: the standard loading, empty and error states.

## Data stores

| Store | Use it for | Access |
|---|---|---|
| **Lakebase** (Postgres) | Transactional app state: forms, workflow, user settings | `db_session()` / ORM, as the app's service principal |
| **Lakehouse** (SQL warehouse) | Reading governed analytical data from Unity Catalog | `obo_connection()` (as the user) or `sp_engine()` (as the app) |

Lakebase credentials are short-lived OAuth tokens. `app/db/lakebase.py` fetches a fresh token for every new connection and recycles pooled connections after 45 minutes, so nothing expires mid-request.

## Errors and logging

- Every API error is JSON: `{"error": {"code", "message", "request_id"}}`. Unexpected exceptions return a generic 500. The details are only logged.
- Log lines carry the request ID (`X-Request-Id` from the proxy). Users can quote the ID shown in the UI's error state.
- A logging filter redacts anything that looks like a Databricks token, and gunicorn's access log never includes headers.

## Deployment artifact

`npm run build` creates `.build/`:

```
.build/
├── app.yaml
├── requirements.txt
├── backend/            (without tests)
└── frontend/dist/
```

`.build/` has no `package.json`, so Databricks only runs `pip install -r requirements.txt`. No npm runs on the platform. CI builds the frontend once and promotes the same artifact through every environment.
