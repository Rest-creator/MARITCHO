#!/usr/bin/env node
/*
 * Runs a Flutter command for this app inside Docker, for machines without
 * the Flutter SDK. The official Flutter release (same version as CI,
 * .github/workflows/mobile-ci.yml) is downloaded once into a Docker
 * volume; the public Flutter images lag months behind and can't build an
 * app that needs Dart 3.13.
 *
 *   node tool/flutter_in_docker.mjs analyze
 *   node tool/flutter_in_docker.mjs test
 *   node tool/flutter_in_docker.mjs pub get
 *   node tool/flutter_in_docker.mjs dart format .     (any `dart` command too)
 *
 * The SDK and pub cache live in Docker volumes, so each downloads once.
 */
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const FLUTTER_VERSION = "3.47.5";
// Any image with git, curl, xz and the Linux build tools Flutter expects.
const BASE_IMAGE = "ghcr.io/cirruslabs/flutter:stable";
const SDK_URL = `https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_${FLUTTER_VERSION}-stable.tar.xz`;

const app = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const args = process.argv.slice(2);
if (args.length === 0) {
  console.error("Usage: node tool/flutter_in_docker.mjs <flutter args…> | dart <dart args…>");
  process.exit(2);
}
const [tool, rest] = args[0] === "dart" ? ["dart", args.slice(1)] : ["flutter", args];
const quoted = rest.map((arg) => `'${arg.replaceAll("'", "'\\''")}'`).join(" ");

const script = [
  "set -e",
  "if [ ! -x /opt/flutter/bin/flutter ]; then",
  `  echo "Downloading Flutter ${FLUTTER_VERSION} (once)…"`,
  `  curl -fsSL "${SDK_URL}" | tar -xJ -C /opt`,
  "fi",
  "git config --global --add safe.directory /opt/flutter",
  "export PATH=/opt/flutter/bin:$PATH",
  "flutter config --no-analytics >/dev/null 2>&1 || true",
  `${tool} ${quoted}`,
].join("\n");

const result = spawnSync(
  "docker",
  [
    "run",
    "--rm",
    "-v",
    `${app}:/app`,
    "-v",
    `maricho-flutter-${FLUTTER_VERSION}:/opt`,
    "-v",
    "maricho-pub-cache:/root/.pub-cache",
    // Keep the container's .dart_tool/build out of your checkout's way.
    "-v",
    "maricho-mobile-dart-tool:/app/.dart_tool",
    "-v",
    "maricho-mobile-build:/app/build",
    "-w",
    "/app",
    BASE_IMAGE,
    "bash",
    "-c",
    script,
  ],
  { stdio: "inherit" },
);
process.exit(result.status ?? 1);
