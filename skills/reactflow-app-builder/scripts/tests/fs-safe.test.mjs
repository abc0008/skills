import test from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import { resolveWithinBase } from "../lib/fs-safe.mjs";

test("resolveWithinBase allows relative paths inside base", () => {
  const base = path.resolve("/tmp/base");
  const result = resolveWithinBase(base, "child/file.txt");
  assert.ok(result.startsWith(base + path.sep));
});

test("resolveWithinBase rejects path traversal outside base", () => {
  const base = path.resolve("/tmp/base");
  assert.throws(() => resolveWithinBase(base, "../escape.txt"));
});
