// Run a Python module from the project virtualenv, cross-platform.
//   node scripts/py.mjs <module> [args...]   e.g. node scripts/py.mjs pytest -k items
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const venvPython =
  process.platform === "win32"
    ? path.join(root, ".venv", "Scripts", "python.exe")
    : path.join(root, ".venv", "bin", "python");

if (!existsSync(venvPython)) {
  console.error("No virtualenv found at .venv. Run `npm run setup` first.");
  process.exit(1);
}

const [module, ...args] = process.argv.slice(2);
if (!module) {
  console.error("Usage: node scripts/py.mjs <module> [args...]");
  process.exit(1);
}

const result = spawnSync(venvPython, ["-m", module, ...args], { cwd: root, stdio: "inherit" });
process.exit(result.status ?? 1);
