import fs from "node:fs/promises";
import path from "node:path";

export function resolveWithinBase(baseDir, userPath) {
  const resolvedBase = path.resolve(baseDir);
  const resolvedTarget = path.resolve(resolvedBase, userPath);

  if (resolvedTarget === resolvedBase) return resolvedTarget;
  if (!resolvedTarget.startsWith(resolvedBase + path.sep)) {
    throw new Error(`Path escapes base directory: ${userPath}`);
  }
  return resolvedTarget;
}

export async function dirIsEmpty(dirPath) {
  try {
    const entries = await fs.readdir(dirPath);
    return entries.length === 0;
  } catch (e) {
    if (e && e.code === "ENOENT") return true;
    throw e;
  }
}

export async function ensureDir(dirPath) {
  await fs.mkdir(dirPath, { recursive: true });
}

export async function copyDirRecursive(srcDir, dstDir) {
  await ensureDir(dstDir);
  const entries = await fs.readdir(srcDir, { withFileTypes: true });

  for (const ent of entries) {
    const src = path.join(srcDir, ent.name);
    const dst = path.join(dstDir, ent.name);

    if (ent.isDirectory()) {
      await copyDirRecursive(src, dst);
    } else if (ent.isFile()) {
      const data = await fs.readFile(src);
      await fs.writeFile(dst, data);
    }
  }
}

export async function readJson(filePath) {
  const raw = await fs.readFile(filePath, "utf8");
  return JSON.parse(raw);
}

export async function writeJsonPretty(filePath, obj) {
  const raw = JSON.stringify(obj, null, 2) + "\n";
  await fs.writeFile(filePath, raw, "utf8");
}
