# Starting a new app from the template

Work through this list once per new app. Steps marked **(admin)** need a workspace or Azure DevOps admin.

## 1. Repository

- [ ] Create the repo from this template in Azure DevOps, then clone it.
- [ ] Run `npm run setup && npm run dev` and check http://localhost:5173.

## 2. Name the app

- [ ] `databricks.yml`: set `bundle.name` and the `app_name` defaults/target values. App names allow lowercase letters, digits and hyphens, with **a maximum of 30 characters**. The `sandbox` target adds a per-user prefix, so keep the base name short.
- [ ] `frontend/src/config/app.ts` (`APP_NAME`) and `frontend/index.html` (`<title>`).
- [ ] `package.json` `name` and `pyproject.toml` `project.name`.
- [ ] Pick a **unique Postgres schema** for the app and set it as `DB_SCHEMA` in `app.yaml` and `.env.example`. Apps can share a Lakebase database, but never a schema.

## 3. Databricks resources (admin)

For each environment (dev, staging, prod):

- [ ] Create or choose a **SQL warehouse**. Note its ID.
- [ ] Create or choose a **Lakebase database instance** and database. Note the instance and database names.
- [ ] Create a workspace group for the app's users. It gets `CAN_USE` on the app.
- [ ] Make sure **user authorization** is allowed for apps in the workspace (Settings → Development → OAuth scopes for apps). It is needed for OBO.

## 4. Scopes and resources

- [ ] In `resources/app.yml`, trim `user_api_scopes` to what the app actually uses. If the app never calls Databricks as the user, remove the block entirely and delete the OBO examples.
- [ ] Add or remove app resources (warehouse, Lakebase, secrets, serving endpoints...). Expose each one to the code through `app.yaml` `valueFrom`.
- [ ] If the Lakehouse queries should default to a catalog/schema, set `LAKEHOUSE_CATALOG` / `LAKEHOUSE_SCHEMA` in `app.yaml`.

## 5. CI/CD (admin)

Follow [DEPLOYMENT.md](DEPLOYMENT.md):

- [ ] Service connections `databricks-{dev,staging,prod}-wif`
- [ ] Variable groups `app-template-{dev,staging,prod}` (rename to match your app)
- [ ] Environments `app-template-{dev,staging,prod}` with approvals on staging and prod
- [ ] Pipelines from `azure-pipelines/ci.yml` and `azure-pipelines/cd.yml`, plus a branch policy that requires CI on `main`
- [ ] Set the workspace hosts in `databricks.yml`

## 6. Make it yours

- [ ] Replace the `Item` model, its service, routes, hook and page with your own. Delete migration `0001` *before the first prod deploy*. After that, write a new migration instead.
- [ ] Delete `api/examples.py` and the Examples page when you no longer need them.
- [ ] Keep the Ventia theme as is (see [BRANDING.md](BRANDING.md)). Only replace the placeholder logo/favicon with official assets.
- [ ] Add shadcn components as needed: `cd frontend && npx shadcn@latest add <component>`.
