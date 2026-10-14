#!/usr/bin/env node
/*
 * Runs the visual suite inside the same Linux image CI uses, so screenshots
 * match pixel for pixel whatever OS you are on. Extra arguments go to
 * Playwright, e.g. `npm run test:visual -- --update-snapshots`.
 *
 * node_modules and .next live in Docker volumes: the container needs Linux
 * builds of Next.js, and must not overwrite the ones on your machine.
 */
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontend = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const version = JSON.parse(readFileSync(resolve(frontend, "package.json"), "utf8")).devDependencies[
  "@playwright/test"
];
const image = `mcr.microsoft.com/playwright:v${version}-noble`;
const args = process.argv
  .slice(2)
  .map((arg) => `'${arg.replaceAll("'", "'\\''")}'`)
  .join(" ");

const script = [
  "set -e",
  // Reinstall only when the lockfile changed since the last run.
  "if ! cmp -s package-lock.json node_modules/.lock-copy; then",
  "  npm ci --no-audit --no-fund && cp package-lock.json node_modules/.lock-copy",
  "fi",
  `npx playwright test --project=visual ${args}`,
].join("\n");

const result = spawnSync(
  "docker",
  [
    "run",
    "--rm",
    "--ipc=host",
    "-e",
    "CI=1",
    "-v",
    `${frontend}:/work`,
    "-v",
    "maricho-e2e-node-modules:/work/node_modules",
    "-v",
    "maricho-e2e-next:/work/.next",
    "-w",
    "/work",
    image,
    "bash",
    "-c",
    script,
  ],
  { stdio: "inherit" },
);
process.exit(result.status ?? 1);
