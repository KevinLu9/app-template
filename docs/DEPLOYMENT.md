# Deployment (Azure DevOps → Databricks)

## Overview

```
PR ─────► ci.yml:  python + frontend checks │ Windows + macOS dev workflow (incl. DB tests) │ build artifact │ bundle validate (dev)
main ───► cd.yml:  build artifact ─► dev ─► staging (approval) ─► prod (approval)
laptop ─► npm run deploy:sandbox (your own prefixed copy in the dev workspace)
```

Deploys use **Databricks Asset Bundles** (`databricks.yml` + `resources/app.yml`) and the **Databricks CLI** (pinned in `azure-pipelines/templates/bundle-steps.yml`). Each environment authenticates through an Azure Resource Manager service connection that uses **workload identity federation (WIF)**. No client secrets exist anywhere.

Every deploy does three things:

1. `databricks bundle validate -t <env>`
2. `databricks bundle deploy -t <env>` uploads `.build/` and creates or updates the app and its resources and permissions.
3. `databricks bundle run app -t <env>` deploys the uploaded code to the app and (re)starts it. Migrations run on start.

## One-time setup per environment

Repeat for `dev`, `staging` and `prod`. The examples use `dev`.

### 1. Deployment identity (Entra ID + Databricks) (admin)

1. In Azure DevOps → Project settings → Service connections, create an **Azure Resource Manager** connection using **Workload identity federation**, named `databricks-dev-wif`. Let ADO create the app registration, or use an existing one with a federated credential for this service connection.
2. Add that Entra application to the Databricks workspace as a **service principal** (Workspace settings → Identity and access → Service principals → Add → Microsoft Entra ID managed). Use the application (client) ID.
3. Grant the deployment SP:
   - permission to create apps (workspace entitlement), or `CAN_MANAGE` on the existing app
   - `CAN_MANAGE` on the SQL warehouse, so it can grant the app `CAN_USE`
   - `CAN_MANAGE` on the Lakebase instance or database, so it can attach it to the app
   - write access to `/Workspace/Shared/.bundle/` (where bundle files and state live)

This deployment SP is **not** the app's runtime identity. Databricks creates a separate service principal for each app automatically.

### 2. Variable group

Create a library variable group named **`app-template-dev`** (rename it per app). All of these values are required:

| Variable | Example |
|---|---|
| `WAREHOUSE_ID` | `1234567890abcdef` |
| `LAKEBASE_INSTANCE` | `shared-lakebase-dev` |
| `LAKEBASE_DATABASE` | `databricks_postgres` |
| `APP_USERS_GROUP` | `app-template-users` |

The pipeline passes these to the bundle as `BUNDLE_VAR_*`. They are identifiers, not secrets.

### 3. Environment and approvals

Create Pipelines → Environments: `app-template-dev`, `app-template-staging` and `app-template-prod`. Add **Approvals and checks** to staging and prod, such as required approvers or a business-hours window. Optionally restrict prod to the `main` branch with a branch control check.

### 4. Workspace host

Set `workspace.host` for each target in `databricks.yml`.

## Pipelines

1. Pipelines → New pipeline → Azure Repos Git → *Existing YAML*:
   - `azure-pipelines/ci.yml`: name it `<app>-ci`
   - `azure-pipelines/cd.yml`: name it `<app>-cd`
2. Repos → Branches → `main` → Branch policies → **Build validation**: add `<app>-ci`, required.
3. On the first run, authorize the pipeline to use the service connections, variable groups and environments.

## Personal sandbox deploys

The `sandbox` target uses `mode: development`. Resources get a per-user prefix, and the deploy uses your own CLI login.

```bash
# macOS (zsh/bash)
databricks auth login --host https://<dev-workspace>.azuredatabricks.net
export BUNDLE_VAR_warehouse_id=... BUNDLE_VAR_lakebase_instance=... BUNDLE_VAR_lakebase_database=...
npm run deploy:sandbox
```

```powershell
# Windows (PowerShell)
databricks auth login --host https://<dev-workspace>.azuredatabricks.net
$env:BUNDLE_VAR_warehouse_id="..."; $env:BUNDLE_VAR_lakebase_instance="..."; $env:BUNDLE_VAR_lakebase_database="..."
npm run deploy:sandbox
```

Use this to try OBO behaviour, which can't be reproduced locally. Clean up with `databricks bundle destroy -t sandbox`.

## Rollback

Each `cd.yml` run deploys one immutable artifact. To roll back, re-run the stage from a previous successful run. Write database migrations so the previous version still works against the new schema: add columns first, remove them in a later release.

## Troubleshooting

| Problem | Check |
|---|---|
| `bundle validate` fails with an auth error | The service connection's SP has been added to the workspace, and `DATABRICKS_AUTH_TYPE=azure-cli` is set (it is in `bundle-steps.yml`) |
| `Permission denied` attaching the warehouse or Lakebase | The deployment SP needs `CAN_MANAGE` on those resources |
| App deploys but crashes on start | App → Logs in the workspace. Usually a migration error or a missing `DATABRICKS_WAREHOUSE_ID` |
| `$(WAREHOUSE_ID)` appears literally in errors | The variable is missing from the variable group |
| App name rejected | Use lowercase letters, digits and hyphens, at most 30 characters |
