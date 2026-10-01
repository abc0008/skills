#!/usr/bin/env node
import path from "node:path";
import { info, error as logError } from "./lib/logger.mjs";
import { readJson } from "./lib/fs-safe.mjs";

function parseArgs(argv) {
  const args = { file: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--file") args.file = argv[++i];
    else if (a === "--help" || a === "-h") args.help = true;
  }
  return args;
}

function printHelp() {
  console.log(`
Usage:
  node scripts/validate-flow-json.mjs --file <path>

Validates a FlowDocument JSON file (export/import format).
`);
}

function isNumber(x) {
  return typeof x === "number" && Number.isFinite(x);
}

function validateFlowDocument(doc) {
  const errors = [];

  if (!doc || typeof doc !== "object") {
    return ["Document is not an object."];
  }
  if (!Number.isInteger(doc.version) || doc.version < 1) {
    errors.push("version must be an integer >= 1");
  }
  if (typeof doc.createdAt !== "string") {
    errors.push("createdAt must be a string");
  }
  if (!doc.flow || typeof doc.flow !== "object") {
    errors.push("flow must be an object");
    return errors;
  }

  if (!Array.isArray(doc.flow.nodes)) errors.push("flow.nodes must be an array");
  if (!Array.isArray(doc.flow.edges)) errors.push("flow.edges must be an array");

  const vp = doc.flow.viewport;
  if (!vp || typeof vp !== "object") {
    errors.push("flow.viewport must be an object");
  } else {
    if (!isNumber(vp.x)) errors.push("flow.viewport.x must be a number");
    if (!isNumber(vp.y)) errors.push("flow.viewport.y must be a number");
    if (!isNumber(vp.zoom)) errors.push("flow.viewport.zoom must be a number");
  }

  return errors;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || !args.file) {
    printHelp();
    process.exit(args.file ? 0 : 2);
  }

  const filePath = path.resolve(process.cwd(), args.file);
  const doc = await readJson(filePath);

  const errors = validateFlowDocument(doc);
  if (errors.length > 0) {
    logError("validate:failed", { filePath, errors });
    process.exit(1);
  }

  info("validate:ok", {
    filePath,
    version: doc.version,
    nodes: doc.flow.nodes.length,
    edges: doc.flow.edges.length
  });
}

main().catch((e) => {
  logError("validate:error", { error: String(e?.message || e) });
  process.exit(1);
});
