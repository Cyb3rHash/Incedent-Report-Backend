#!/usr/bin/env node
"use strict";

/**
 * Simple backend runner.
 *
 * Usage:
 *   node scripts/run-backend.js           # starts in "dev" if NODE_ENV!=production, else "prod"
 *   node scripts/run-backend.js dev       # starts with `npm run dev`
 *   node scripts/run-backend.js prod      # starts with `npm start`
 *
 * Notes:
 * - This script intentionally uses `npm` so it respects the existing package.json scripts.
 * - It does a small preflight check to help diagnose missing configuration early.
 */

const { spawn } = require("node:child_process");

function usageAndExit(code) {
  // eslint-disable-next-line no-console
  console.error(
    [
      "Usage: node scripts/run-backend.js [dev|prod]",
      "",
      "Examples:",
      "  node scripts/run-backend.js dev",
      "  node scripts/run-backend.js prod",
      "",
      "Environment:",
      "  DATABASE_URL is required (see README.md).",
    ].join("\n")
  );
  process.exit(code);
}

function getModeFromArgs(argv) {
  const arg = (argv[2] || "").trim().toLowerCase();
  if (!arg) {
    // Default mode: dev unless explicitly in production.
    return process.env.NODE_ENV === "production" ? "prod" : "dev";
  }
  if (arg === "dev" || arg === "prod") return arg;
  usageAndExit(2);
}

function preflightEnv() {
  // dotenv is loaded in src/index.js; this just helps catch obvious misconfig.
  if (!process.env.DATABASE_URL) {
    // eslint-disable-next-line no-console
    console.error(
      [
        "Missing required env var: DATABASE_URL",
        "",
        "Create/populate your .env (one already exists in this environment) or export DATABASE_URL before running.",
      ].join("\n")
    );
    process.exit(1);
  }
}

function run() {
  const mode = getModeFromArgs(process.argv);
  preflightEnv();

  const npmCmd = process.platform === "win32" ? "npm.cmd" : "npm";
  const npmArgs = mode === "prod" ? ["start"] : ["run", "dev"];

  // eslint-disable-next-line no-console
  console.log(`[run-backend] starting backend in ${mode.toUpperCase()} mode...`);

  const child = spawn(npmCmd, npmArgs, {
    stdio: "inherit",
    env: process.env,
  });

  child.on("exit", (code, signal) => {
    if (signal) process.exit(1);
    process.exit(code ?? 1);
  });
}

run();
