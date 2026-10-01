#!/usr/bin/env node
import path from "node:path";
import fs from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { info, error as logError } from "./lib/logger.mjs";
import { copyDirRecursive, dirIsEmpty, ensureDir, readJson, writeJsonPretty } from "./lib/fs-safe.mjs";

function parseArgs(argv) {
  const args = { dest: null, name: null, force: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--dest") args.dest = argv[++i];
    else if (a === "--name") args.name = argv[++i];
    else if (a === "--force") args.force = true;
    else if (a === "--help" || a === "-h") args.help = true;
  }
  return args;
}

function printHelp() {
  console.log(`
Usage:
  node scripts/scaffold-reactflow-app.mjs --dest <path> [--name <pkg-name>] [--force]

Copies the bundled template app from assets/reactflow-starter into <path>.

Options:
  --dest   Destination directory (required)
  --name   Updates package.json name (optional)
  --force  Allow copying into a non-empty directory (overwrites files)
`);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || !args.dest) {
    printHelp();
    process.exit(args.dest ? 0 : 2);
  }

  const __filename = fileURLToPath(import.meta.url);
  const __dirname = path.dirname(__filename);

  const templateDir = path.resolve(__dirname, "..", "assets", "reactflow-starter");
  const destDir = path.resolve(process.cwd(), args.dest);

  await ensureDir(destDir);

  const empty = await dirIsEmpty(destDir);
  if (!empty && !args.force) {
    throw new Error(`Destination is not empty: ${destDir}. Use --force to overwrite.`);
  }

  info("scaffold:start", { templateDir, destDir });

  await copyDirRecursive(templateDir, destDir);

  // Update package.json name if requested
  if (args.name) {
    const pkgPath = path.join(destDir, "package.json");
    const pkg = await readJson(pkgPath);
    pkg.name = args.name;
    await writeJsonPretty(pkgPath, pkg);
    info("scaffold:package-name-updated", { name: args.name });
  }

  // Best-effort: remove node_modules if template was copied from a dirty folder
  const nm = path.join(destDir, "node_modules");
  try {
    await fs.rm(nm, { recursive: true, force: true });
  } catch {
    // ignore
  }

  info("scaffold:done", { status: "OK", appPath: destDir });
}

main().catch((e) => {
  logError("scaffold:failed", { error: String(e?.message || e) });
  process.exit(1);
});
