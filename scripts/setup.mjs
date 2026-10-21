// One-time local setup: virtualenv, Python + Node dependencies, pre-commit hooks, .env.
import { spawnSync } from "node:child_process";
import { copyFileSync, existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const isWindows = process.platform === "win32";
const venvPython = isWindows
  ? path.join(root, ".venv", "Scripts", "python.exe")
  : path.join(root, ".venv", "bin", "python");

// Only npm needs a shell (it is npm.cmd on Windows). Python is spawned directly so that
// interpreter paths containing spaces (C:\Program Files\...) work.
function run(cmd, args, { allowFail = false, shell = false } = {}) {
  console.log(`\n> ${cmd} ${args.join(" ")}`);
  const result = spawnSync(cmd, args, { cwd: root, stdio: "inherit", shell });
  if (result.status !== 0 && !allowFail) {
    console.error(`\nCommand failed: ${cmd} ${args.join(" ")}`);
    process.exit(result.status ?? 1);
  }
  return result.status === 0;
}

function pythonVersion(cmd, args) {
  const r = spawnSync(cmd, [...args, "-c", "import sys; print('%d.%d' % sys.version_info[:2])"], {
    encoding: "utf8",
  });
  return r.status === 0 ? r.stdout.trim() : null;
}

// Databricks Apps runs Python 3.11, so prefer it locally. Set PYTHON to force an interpreter,
// e.g. PYTHON=C:\Python311\python.exe (Windows) or PYTHON=/opt/homebrew/bin/python3.11 (macOS).
function findPython() {
  if (process.env.PYTHON) {
    const version = pythonVersion(process.env.PYTHON, []);
    if (!version) {
      console.error(`PYTHON=${process.env.PYTHON} is not a working Python interpreter.`);
      process.exit(1);
    }
    return { cmd: process.env.PYTHON, args: [], version };
  }
  const candidates = isWindows
    ? [["py", ["-3.11"]], ["py", ["-3"]], ["python", []]]
    : [["python3.11", []], ["python3", []], ["python", []]];
  for (const [cmd, args] of candidates) {
    const version = pythonVersion(cmd, args);
    if (version) {
      const [major, minor] = version.split(".").map(Number);
      if (major === 3 && minor >= 11) return { cmd, args, version };
    }
  }
  console.error("Python 3.11+ is required (3.11 matches the Databricks Apps runtime).");
  process.exit(1);
}

if (!existsSync(venvPython)) {
  const py = findPython();
  if (py.version !== "3.11") {
    console.warn(`\nWarning: using Python ${py.version}; Databricks Apps runs 3.11.`);
  }
  run(py.cmd, [...py.args, "-m", "venv", ".venv"]);
}

run(venvPython, ["-m", "pip", "install", "--upgrade", "pip"]);
run(venvPython, ["-m", "pip", "install", "-r", "requirements-dev.txt"]);
run("npm", ["install"], { shell: isWindows });

if (existsSync(path.join(root, ".git"))) {
  run(venvPython, ["-m", "pre_commit", "install"], { allowFail: true });
}

const envFile = path.join(root, ".env");
if (!existsSync(envFile)) {
  copyFileSync(path.join(root, ".env.example"), envFile);
  console.log("\nCreated .env from .env.example");
}

console.log("\nSetup complete. Next: npm run db:up && npm run migrate && npm run dev");
