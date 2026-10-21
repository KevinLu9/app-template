// Local Postgres without Docker or a system install, on macOS, Windows and Linux.
// Binaries come from the @embedded-postgres/<platform> npm package (optionalDependencies;
// npm installs only the one for your OS/CPU). Data lives in .local/postgres (gitignored).
//
//   node scripts/db.mjs up | down | status | reset
//
// pg_ctl runs Postgres in the background, so it keeps running after this script exits,
// like `docker compose up -d` did. It listens on 127.0.0.1 only.
import { spawnSync } from "node:child_process";
import { appendFileSync, existsSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

import pg from "pg";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const localDir = path.join(root, ".local");
const dataDir = path.join(localDir, "postgres");
const logFile = path.join(localDir, "postgres.log");

// Must match DATABASE_URL in .env.example.
const USER = "app";
const PASSWORD = "app";
const DATABASE = "app";
const PORT = Number(process.env.LOCAL_PG_PORT ?? 5432);

const PLATFORM_PACKAGES = {
  "darwin-arm64": "@embedded-postgres/darwin-arm64",
  "darwin-x64": "@embedded-postgres/darwin-x64",
  "win32-x64": "@embedded-postgres/windows-x64",
  "linux-x64": "@embedded-postgres/linux-x64",
  "linux-arm64": "@embedded-postgres/linux-arm64",
};

async function binaries() {
  const key = `${os.platform()}-${os.arch()}`;
  const pkg = PLATFORM_PACKAGES[key];
  if (!pkg) fail(`No embedded Postgres build for ${key}. Point DATABASE_URL at any Postgres 16.`);
  try {
    return await import(pkg);
  } catch {
    fail(`${pkg} is not installed. Run \`npm install\` (or \`npm run setup\`).`);
  }
}

function fail(message) {
  console.error(message);
  process.exit(1);
}

function run(bin, args, { quiet = false } = {}) {
  // stdin/stdout are not piped, so pg_ctl can return while the server keeps running.
  return spawnSync(bin, args, { stdio: quiet ? "ignore" : ["ignore", "inherit", "inherit"] });
}

function isRunning(bin) {
  return run(bin.pg_ctl, ["status", "-D", dataDir], { quiet: true }).status === 0;
}

function init(bin) {
  mkdirSync(localDir, { recursive: true });
  const pwFile = path.join(localDir, "pwfile");
  writeFileSync(pwFile, PASSWORD);
  try {
    const result = run(bin.initdb, [
      "-D", dataDir,
      "-U", USER,
      `--pwfile=${pwFile}`,
      "--auth=scram-sha-256",
      "--encoding=UTF8",
      "--no-locale", // avoids OS-specific locale names (e.g. on Windows)
    ]);
    if (result.status !== 0) fail("initdb failed.");
  } finally {
    rmSync(pwFile, { force: true });
  }
  appendFileSync(
    path.join(dataDir, "postgresql.conf"),
    "\n# Added by scripts/db.mjs\nlisten_addresses = '127.0.0.1'\n",
  );
}

async function ensureDatabase() {
  const client = new pg.Client({
    host: "127.0.0.1", port: PORT, user: USER, password: PASSWORD, database: "postgres",
  });
  await client.connect();
  try {
    const { rowCount } = await client.query("SELECT 1 FROM pg_database WHERE datname = $1", [DATABASE]);
    if (!rowCount) await client.query(`CREATE DATABASE "${DATABASE}"`);
  } finally {
    await client.end();
  }
}

async function up() {
  const bin = await binaries();
  if (!existsSync(path.join(dataDir, "PG_VERSION"))) {
    console.log(`Initialising Postgres in ${path.relative(root, dataDir)}`);
    init(bin);
  }
  if (isRunning(bin)) {
    console.log("Postgres is already running.");
  } else {
    const result = run(bin.pg_ctl, ["start", "-D", dataDir, "-l", logFile, "-w", "-o", `-p ${PORT}`]);
    if (result.status !== 0) fail(`Postgres failed to start. See ${path.relative(root, logFile)}`);
  }
  await ensureDatabase();
  console.log(`Postgres ready: postgresql://${USER}:***@127.0.0.1:${PORT}/${DATABASE}`);
}

async function down() {
  const bin = await binaries();
  if (!existsSync(dataDir) || !isRunning(bin)) {
    console.log("Postgres is not running.");
    return;
  }
  if (run(bin.pg_ctl, ["stop", "-D", dataDir, "-m", "fast", "-w"]).status !== 0) {
    fail("Failed to stop Postgres.");
  }
}

async function status() {
  const bin = await binaries();
  const running = existsSync(dataDir) && isRunning(bin);
  console.log(running ? `Postgres is running on 127.0.0.1:${PORT}.` : "Postgres is not running.");
  process.exitCode = running ? 0 : 1;
}

async function reset() {
  await down();
  rmSync(dataDir, { recursive: true, force: true });
  rmSync(logFile, { force: true });
  await up();
}

const commands = { up, down, status, reset };
const command = commands[process.argv[2]];
if (!command) fail("Usage: node scripts/db.mjs up | down | status | reset");
await command();
