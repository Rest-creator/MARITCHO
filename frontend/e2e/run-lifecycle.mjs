#!/usr/bin/env node
/*
 * Runs the lifecycle suite against its own throwaway backend: a separate
 * docker-compose project (`maricho-e2e`) on its own ports, with a fresh
 * database that is deleted afterwards. Your dev stack (`maricho`) and its
 * data are never touched, and earlier runs can't leave workers behind that
 * change who gets matched.
 *
 * Extra arguments go to Playwright, e.g. `npm run test:e2e -- --headed`.
 * KEEP_E2E_STACK=1 leaves the stack running afterwards for debugging.
 */
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontend = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const composeFile = resolve(frontend, "..", "backend", "docker-compose.yml");
const project = "maricho-e2e";
const ports = { api: "18000", db: "15434", redis: "16381" };

const composeEnv = {
  ...process.env,
  MARICHO_API_PORT: ports.api,
  MARICHO_DB_PORT: ports.db,
  MARICHO_REDIS_PORT: ports.redis,
};

function compose(...args) {
  return spawnSync("docker", ["compose", "-p", project, "-f", composeFile, ...args], {
    env: composeEnv,
    stdio: "inherit",
  });
}

function stopStack() {
  if (process.env.KEEP_E2E_STACK === "1") {
    console.warn(`Leaving ${project} running on port ${ports.api}.`);
    return;
  }
  compose("down", "--volumes", "--remove-orphans");
}

// Only the backend: the suite builds and serves the web app itself, against this stack.
const up = compose("up", "--detach", "--build", "--wait", "db", "redis", "api");
if (up.status !== 0) {
  compose("logs", "api");
  stopStack();
  process.exit(up.status ?? 1);
}

const playwright = spawnSync(
  process.execPath,
  [
    resolve(frontend, "node_modules", "@playwright", "test", "cli.js"),
    "test",
    "--project=lifecycle",
    ...process.argv.slice(2),
  ],
  {
    cwd: frontend,
    stdio: "inherit",
    env: {
      ...process.env,
      // Read at build time too, so the app is built against this stack.
      BACKEND_URL: `http://127.0.0.1:${ports.api}`,
      NEXT_PUBLIC_WS_URL: `ws://127.0.0.1:${ports.api}`,
    },
  },
);

if (playwright.status !== 0) compose("logs", "--tail", "100", "api");
stopStack();
process.exit(playwright.status ?? 1);
