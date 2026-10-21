// Assemble .build/: exactly what gets deployed to Databricks Apps, and nothing else.
// The frontend is prebuilt here (in CI), so the deployed folder has no package.json and
// Databricks does not run npm on deploy. Run via `npm run build`.
import { cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const out = path.join(root, ".build");
const dist = path.join(root, "frontend", "dist");

if (!existsSync(path.join(dist, "index.html"))) {
  console.error("frontend/dist is missing. Run `npm run build -w frontend` first.");
  process.exit(1);
}

const skip = new Set(["__pycache__", "tests", ".pytest_cache", ".ruff_cache"]);
const filter = (src) => !skip.has(path.basename(src)) && !src.endsWith(".pyc");

rmSync(out, { recursive: true, force: true });
mkdirSync(out, { recursive: true });
cpSync(path.join(root, "backend"), path.join(out, "backend"), { recursive: true, filter });
cpSync(dist, path.join(out, "frontend", "dist"), { recursive: true });
cpSync(path.join(root, "app.yaml"), path.join(out, "app.yaml"));
cpSync(path.join(root, "requirements.txt"), path.join(out, "requirements.txt"));

console.log(`Bundle assembled in ${path.relative(root, out)}/`);
